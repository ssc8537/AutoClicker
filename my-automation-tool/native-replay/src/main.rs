mod audio;

use std::collections::VecDeque;
use std::env;
use std::error::Error;
use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Write};
use std::path::{Path, PathBuf};
use std::sync::mpsc::{self, Receiver, SyncSender, TryRecvError};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use mp4::{AacConfig, AvcConfig, MediaConfig, MediaType, Mp4Config, Mp4Reader, Mp4Writer, TrackConfig};
use windows::Win32::Media::MediaFoundation::{
    MFMediaType_Video, MFVideoFormat_H264, MFT_CATEGORY_VIDEO_ENCODER, MFT_ENUM_FLAG_HARDWARE,
    MFT_FRIENDLY_NAME_Attribute, MFT_REGISTER_TYPE_INFO, MFTEnumEx,
};
use windows::Win32::System::Com::{
    COINIT_MULTITHREADED, CoInitializeEx, CoTaskMemFree, CoUninitialize,
};
use windows::Win32::System::Performance::{QueryPerformanceCounter, QueryPerformanceFrequency};
use windows_capture::capture::{Context, GraphicsCaptureApiHandler};
use windows_capture::encoder::{
    AudioSettingsBuilder, ContainerSettingsBuilder, VideoEncoder, VideoSettingsBuilder,
    VideoSettingsSubType,
};
use windows_capture::frame::Frame;
use windows_capture::graphics_capture_api::InternalCaptureControl;
use windows_capture::monitor::Monitor;
use windows_capture::settings::{
    ColorFormat, CursorCaptureSettings, DirtyRegionSettings, DrawBorderSettings,
    MinimumUpdateIntervalSettings, SecondaryWindowSettings, Settings,
};

use audio::{AudioConfig, AudioRuntime};

type AnyError = Box<dyn Error + Send + Sync>;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum EncoderMode {
    Gpu,
    Cpu,
}

#[derive(Clone)]
struct EncoderFactory {
    width: u32,
    height: u32,
    source_width: u32,
    source_height: u32,
    fps: u32,
    bitrate: u32,
    hardware: bool,
}

impl EncoderFactory {
    fn create(&self, path: &Path) -> Result<VideoEncoder, AnyError> {
        let video = VideoSettingsBuilder::new(self.width, self.height)
            .source_size(self.source_width, self.source_height)
            .sub_type(VideoSettingsSubType::H264)
            .bitrate(self.bitrate)
            .frame_rate(self.fps);
        Ok(VideoEncoder::new(
            video,
            AudioSettingsBuilder::new().disabled(true),
            ContainerSettingsBuilder::new().hardware_acceleration(self.hardware),
            path,
        )?)
    }
}

struct CaptureOptions {
    metadata: PathBuf,
    monitor: usize,
    duration: Duration,
    width: u32,
    height: u32,
    fps: u32,
    bitrate: u32,
    encoder_mode: EncoderMode,
    stop_file: PathBuf,
    segment_directory: PathBuf,
    manifest: PathBuf,
    rotate_file: PathBuf,
    rotate_ack: PathBuf,
    segment_seconds: u64,
    max_segments: usize,
    audio_manifest: PathBuf,
    audio_levels: PathBuf,
    audio_info: PathBuf,
    record_microphone: bool,
    microphone_device_id: Option<String>,
    microphone_gain_percent: u32,
}

struct AudioMonitorOptions {
    stop_file: PathBuf,
    work_directory: PathBuf,
    audio_levels: PathBuf,
    audio_info: PathBuf,
    microphone_device_id: Option<String>,
    microphone_gain_percent: u32,
}

struct MergeOptions {
    output: PathBuf,
    segments: Vec<PathBuf>,
    desktop_segments: Vec<PathBuf>,
    microphone_segments: Vec<PathBuf>,
}

enum Command {
    Capture(CaptureOptions),
    AudioMonitor(AudioMonitorOptions),
    Merge(MergeOptions),
}

struct CaptureFlags {
    metadata: PathBuf,
    duration: Duration,
    fps: u32,
    bitrate: u32,
    encoder_mode: EncoderMode,
    source_name: String,
    stop_file: PathBuf,
    segment_directory: PathBuf,
    manifest: PathBuf,
    rotate_file: PathBuf,
    rotate_ack: PathBuf,
    segment_ticks: i64,
    max_segments: usize,
    encoder_name: String,
    factory: EncoderFactory,
    audio_manifest: PathBuf,
    audio_levels: PathBuf,
    audio_info: PathBuf,
    record_microphone: bool,
    microphone_device_id: Option<String>,
    microphone_gain_percent: u32,
}

struct SegmentState {
    index: u64,
    path: PathBuf,
    encoder: VideoEncoder,
    start_qpc: i64,
    last_qpc: i64,
    frames: u64,
}

struct PreparedEncoder {
    index: u64,
    path: PathBuf,
    result: Result<VideoEncoder, String>,
}

struct FinalizeJob {
    index: u64,
    path: PathBuf,
    encoder: VideoEncoder,
    start_qpc: i64,
    end_qpc: i64,
    frames: u64,
}

struct FinalizeAck {
    index: u64,
    result: Result<(), String>,
}

struct Capture {
    flags: CaptureFlags,
    started: Instant,
    qpc_start: i64,
    qpc_frequency: i64,
    first_frame_qpc: Option<i64>,
    last_frame_qpc: Option<i64>,
    frames: u64,
    current: Option<SegmentState>,
    next_rx: Receiver<PreparedEncoder>,
    next_ready: Option<PreparedEncoder>,
    next_pending: bool,
    next_retry_after: Instant,
    finalize_tx: Option<SyncSender<FinalizeJob>>,
    finalize_ack_rx: Receiver<FinalizeAck>,
    finalizer_thread: Option<JoinHandle<()>>,
    finalizer_busy: bool,
    rollover_delayed: bool,
    audio: AudioRuntime,
}

impl GraphicsCaptureApiHandler for Capture {
    type Flags = CaptureFlags;
    type Error = AnyError;

    fn new(ctx: Context<Self::Flags>) -> Result<Self, Self::Error> {
        fs::create_dir_all(&ctx.flags.segment_directory)?;
        if let Some(parent) = ctx.flags.manifest.parent() {
            fs::create_dir_all(parent)?;
        }
        let first_path = segment_path(&ctx.flags.segment_directory, 1);
        let first_encoder = ctx.flags.factory.create(&first_path)?;
        let (qpc_start, qpc_frequency) = qpc_now()?;
        let audio = AudioRuntime::start(AudioConfig {
            segment_directory: ctx.flags.segment_directory.clone(),
            manifest: ctx.flags.audio_manifest.clone(),
            levels_file: ctx.flags.audio_levels.clone(),
            max_segments: ctx.flags.max_segments,
            microphone_enabled: ctx.flags.record_microphone,
            microphone_device_id: ctx.flags.microphone_device_id.clone(),
            microphone_gain_percent: ctx.flags.microphone_gain_percent,
        })
        .map_err(|error| format!("音频采集初始化失败：{error}"))?;
        fs::write(
            &ctx.flags.audio_info,
            format!(
                concat!(
                    "{{\n  \"schema\": 1,\n  \"desktop_device_id\": \"{}\",\n",
                    "  \"desktop_device_name\": \"{}\",\n  \"microphone_enabled\": {},\n",
                    "  \"microphone_device_id\": {},\n  \"microphone_device_name\": {}\n}}\n"
                ),
                json_escape(&audio.desktop_device_id),
                json_escape(&audio.desktop_device_name),
                audio.microphone_enabled,
                json_optional_string(audio.microphone_device_id.as_deref()),
                json_optional_string(audio.microphone_device_name.as_deref()),
            ),
        )?;
        let (next_tx, next_rx) = mpsc::channel();
        spawn_encoder(
            next_tx,
            ctx.flags.factory.clone(),
            2,
            segment_path(&ctx.flags.segment_directory, 2),
        );
        let (finalize_tx, finalize_rx) = mpsc::sync_channel(1);
        let (finalize_ack_tx, finalize_ack_rx) = mpsc::channel();
        let finalizer_thread = spawn_finalizer(
            finalize_rx,
            finalize_ack_tx,
            ctx.flags.manifest.clone(),
            ctx.flags.max_segments,
        );
        emit_status("buffer_started", &format!("source={}", ctx.flags.source_name));
        Ok(Self {
            flags: ctx.flags,
            started: Instant::now(),
            qpc_start,
            qpc_frequency,
            first_frame_qpc: None,
            last_frame_qpc: None,
            frames: 0,
            current: Some(SegmentState {
                index: 1,
                path: first_path,
                encoder: first_encoder,
                start_qpc: 0,
                last_qpc: 0,
                frames: 0,
            }),
            next_rx,
            next_ready: None,
            next_pending: true,
            next_retry_after: Instant::now(),
            finalize_tx: Some(finalize_tx),
            finalize_ack_rx,
            finalizer_thread: Some(finalizer_thread),
            finalizer_busy: false,
            rollover_delayed: false,
            audio,
        })
    }

    fn on_frame_arrived(
        &mut self,
        frame: &mut Frame,
        capture_control: InternalCaptureControl,
    ) -> Result<(), Self::Error> {
        self.poll_workers()?;
        if let Some(error) = self.audio.poll_error() {
            return Err(format!("音频采集失败：{error}").into());
        }
        let frame_qpc = frame.timestamp()?.Duration;
        if self.first_frame_qpc.is_none() {
            self.audio.begin_segment(1, frame_qpc);
        }
        self.first_frame_qpc.get_or_insert(frame_qpc);
        self.last_frame_qpc = Some(frame_qpc);
        self.frames += 1;

        let stop_requested = self.flags.stop_file.exists() || self.started.elapsed() >= self.flags.duration;
        if !stop_requested {
            self.maybe_rotate(frame_qpc)?;
        }

        let current = self.current.as_mut().ok_or("录像分段状态丢失")?;
        if current.frames == 0 {
            current.start_qpc = frame_qpc;
        }
        current.last_qpc = frame_qpc;
        current.frames += 1;
        current.encoder.send_frame(frame)?;

        if stop_requested {
            self.finish_capture()?;
            self.write_metadata()?;
            capture_control.stop();
            emit_status("buffer_stopped", &format!("frames={}", self.frames));
        }
        Ok(())
    }

    fn on_closed(&mut self) -> Result<(), Self::Error> {
        emit_status("source_closed", "capture item closed");
        Ok(())
    }
}

impl Capture {
    fn poll_workers(&mut self) -> Result<(), AnyError> {
        loop {
            match self.finalize_ack_rx.try_recv() {
                Ok(ack) => {
                    self.finalizer_busy = false;
                    if let Err(error) = ack.result {
                        return Err(format!("分段 {} 封装失败：{}", ack.index, error).into());
                    }
                }
                Err(TryRecvError::Empty) => break,
                Err(TryRecvError::Disconnected) => break,
            }
        }
        if self.next_ready.is_none() {
            match self.next_rx.try_recv() {
                Ok(prepared) => {
                    self.next_pending = false;
                    if prepared.result.is_err() {
                        if let Err(ref error) = prepared.result {
                            emit_status("encoder_prepare_failed", error);
                        }
                        let _ = fs::remove_file(&prepared.path);
                        self.next_retry_after = Instant::now() + Duration::from_secs(1);
                    } else {
                        self.next_ready = Some(prepared);
                    }
                }
                Err(TryRecvError::Empty) => {}
                Err(TryRecvError::Disconnected) => self.next_pending = false,
            }
        }
        if self.next_ready.is_none() && !self.next_pending && Instant::now() >= self.next_retry_after {
            let next_index = self.current.as_ref().map_or(1, |segment| segment.index + 1);
            let (tx, rx) = mpsc::channel();
            self.next_rx = rx;
            spawn_encoder(
                tx,
                self.flags.factory.clone(),
                next_index,
                segment_path(&self.flags.segment_directory, next_index),
            );
            self.next_pending = true;
        }
        Ok(())
    }

    fn maybe_rotate(&mut self, frame_qpc: i64) -> Result<(), AnyError> {
        let current = self.current.as_ref().ok_or("录像分段状态丢失")?;
        let scheduled = current.frames > 0 && frame_qpc - current.start_qpc >= self.flags.segment_ticks;
        let requested = self.flags.rotate_file.exists();
        if !scheduled && !requested {
            self.rollover_delayed = false;
            return Ok(());
        }
        if self.finalizer_busy || self.next_ready.is_none() {
            if !self.rollover_delayed {
                emit_status("rollover_delayed", "下一编码器或封装工作器尚未就绪");
                self.rollover_delayed = true;
            }
            return Ok(());
        }

        let prepared = self.next_ready.take().expect("checked next encoder");
        let encoder = prepared.result.map_err(|error| format!("下一编码器准备失败：{error}"))?;
        let mut old = self.current.replace(SegmentState {
            index: prepared.index,
            path: prepared.path,
            encoder,
            start_qpc: frame_qpc,
            last_qpc: frame_qpc,
            frames: 0,
        }).ok_or("录像分段状态丢失")?;
        self.audio.begin_segment(prepared.index, frame_qpc);
        // The old encoded segment remains visible until this exact new-frame boundary.
        // Use the same QPC edge for video, desktop audio, microphone and input export.
        old.last_qpc = frame_qpc;
        let old_index = old.index;
        self.send_finalize(old)?;

        let next_index = self.current.as_ref().expect("new segment").index + 1;
        let (tx, rx) = mpsc::channel();
        self.next_rx = rx;
        spawn_encoder(
            tx,
            self.flags.factory.clone(),
            next_index,
            segment_path(&self.flags.segment_directory, next_index),
        );
        self.next_pending = true;
        self.rollover_delayed = false;
        if requested {
            let _ = fs::remove_file(&self.flags.rotate_file);
            fs::write(&self.flags.rotate_ack, old_index.to_string())?;
        }
        emit_status("segment_rotated", &format!("closed={old_index};current={}", next_index - 1));
        Ok(())
    }

    fn send_finalize(&mut self, segment: SegmentState) -> Result<(), AnyError> {
        self.finalize_tx
            .as_ref()
            .ok_or("分段封装工作器已关闭")?
            .send(FinalizeJob {
                index: segment.index,
                path: segment.path,
                encoder: segment.encoder,
                start_qpc: segment.start_qpc,
                end_qpc: segment.last_qpc,
                frames: segment.frames,
            })
            .map_err(|_| "分段封装工作器已断开")?;
        self.finalizer_busy = true;
        Ok(())
    }

    fn wait_for_finalizer(&mut self) -> Result<(), AnyError> {
        if !self.finalizer_busy {
            return Ok(());
        }
        let ack = self.finalize_ack_rx.recv()?;
        self.finalizer_busy = false;
        ack.result
            .map_err(|error| format!("分段 {} 封装失败：{}", ack.index, error).into())
    }

    fn finish_capture(&mut self) -> Result<(), AnyError> {
        self.audio
            .stop(self.last_frame_qpc.unwrap_or_default())
            .map_err(|error| format!("停止音频采集失败：{error}"))?;
        self.wait_for_finalizer()?;
        if let Some(current) = self.current.take() {
            self.send_finalize(current)?;
            self.wait_for_finalizer()?;
        }
        self.finish_unused_encoder();
        self.finalize_tx.take();
        if let Some(worker) = self.finalizer_thread.take() {
            worker.join().map_err(|_| "分段封装线程异常退出")?;
        }
        Ok(())
    }

    fn finish_unused_encoder(&mut self) {
        let prepared = if let Some(prepared) = self.next_ready.take() {
            Some(prepared)
        } else if self.next_pending {
            self.next_rx.recv().ok()
        } else {
            None
        };
        if let Some(prepared) = prepared {
            if let Ok(encoder) = prepared.result {
                let _ = encoder.finish();
            }
            let _ = fs::remove_file(prepared.path);
        }
        self.next_pending = false;
    }

    fn write_metadata(&self) -> Result<(), AnyError> {
        let elapsed = self.started.elapsed().as_secs_f64();
        let average_fps = if elapsed > 0.0 { self.frames as f64 / elapsed } else { 0.0 };
        let unix_ms = SystemTime::now().duration_since(UNIX_EPOCH)?.as_millis();
        let mode = match self.flags.encoder_mode {
            EncoderMode::Gpu => "gpu",
            EncoderMode::Cpu => "cpu",
        };
        let (desktop_discontinuities, microphone_discontinuities) =
            self.audio.discontinuities();
        let body = format!(
            concat!(
                "{{\n  \"schema\": 2,\n  \"mode\": \"segmented_replay_buffer\",\n",
                "  \"source\": \"{}\",\n  \"encoder_mode\": \"{}\",\n",
                "  \"encoder_name\": \"{}\",\n  \"codec\": \"H264\",\n",
                "  \"width\": {},\n  \"height\": {},\n  \"source_width\": {},\n",
                "  \"source_height\": {},\n  \"requested_fps\": {},\n  \"average_fps\": {:.3},\n",
                "  \"bitrate\": {},\n  \"frames\": {},\n  \"estimated_dropped_frames\": {},\n",
                "  \"elapsed_ms\": {:.3},\n  \"qpc_start\": {},\n  \"qpc_frequency\": {},\n",
                "  \"first_frame_qpc\": {},\n  \"last_frame_qpc\": {},\n  \"finished_unix_ms\": {},\n",
                "  \"desktop_audio_device_id\": \"{}\",\n  \"desktop_audio_device_name\": \"{}\",\n",
                "  \"microphone_enabled\": {},\n  \"microphone_device_id\": {},\n",
                "  \"microphone_device_name\": {},\n",
                "  \"desktop_audio_discontinuities_recovered\": {},\n",
                "  \"microphone_audio_discontinuities_recovered\": {}\n}}\n"
            ),
            json_escape(&self.flags.source_name),
            mode,
            json_escape(&self.flags.encoder_name),
            self.flags.factory.width,
            self.flags.factory.height,
            self.flags.factory.source_width,
            self.flags.factory.source_height,
            self.flags.fps,
            average_fps,
            self.flags.bitrate,
            self.frames,
            ((elapsed * f64::from(self.flags.fps)).round() as u64).saturating_sub(self.frames),
            elapsed * 1000.0,
            self.qpc_start,
            self.qpc_frequency,
            self.first_frame_qpc.unwrap_or_default(),
            self.last_frame_qpc.unwrap_or_default(),
            unix_ms,
            json_escape(&self.audio.desktop_device_id),
            json_escape(&self.audio.desktop_device_name),
            self.audio.microphone_enabled,
            json_optional_string(self.audio.microphone_device_id.as_deref()),
            json_optional_string(self.audio.microphone_device_name.as_deref()),
            desktop_discontinuities,
            microphone_discontinuities,
        );
        fs::write(&self.flags.metadata, body)?;
        Ok(())
    }
}

fn spawn_encoder(tx: mpsc::Sender<PreparedEncoder>, factory: EncoderFactory, index: u64, path: PathBuf) {
    thread::spawn(move || {
        let result = factory.create(&path).map_err(|error| error.to_string());
        let _ = tx.send(PreparedEncoder { index, path, result });
    });
}

fn spawn_finalizer(
    rx: Receiver<FinalizeJob>,
    ack_tx: mpsc::Sender<FinalizeAck>,
    manifest: PathBuf,
    max_segments: usize,
) -> JoinHandle<()> {
    thread::spawn(move || {
        let mut retained = VecDeque::<PathBuf>::new();
        while let Ok(job) = rx.recv() {
            let index = job.index;
            let path = job.path.clone();
            let result = finalize_segment(&manifest, job).map_err(|error| error.to_string());
            if result.is_ok() {
                retained.push_back(path);
                while retained.len() > max_segments {
                    if let Some(expired) = retained.pop_front() {
                        let _ = fs::remove_file(expired);
                    }
                }
                emit_status("segment_closed", &format!("index={index}"));
            }
            let _ = ack_tx.send(FinalizeAck { index, result });
        }
    })
}

fn finalize_segment(manifest: &Path, job: FinalizeJob) -> Result<(), AnyError> {
    job.encoder.finish()?;
    let size = fs::metadata(&job.path)?.len();
    let mut stream = OpenOptions::new().create(true).append(true).open(manifest)?;
    writeln!(
        stream,
        "{{\"schema\":1,\"index\":{},\"file\":\"{}\",\"start_qpc\":{},\"end_qpc\":{},\"frames\":{},\"bytes\":{}}}",
        job.index,
        json_escape(job.path.file_name().and_then(|name| name.to_str()).unwrap_or_default()),
        job.start_qpc,
        job.end_qpc,
        job.frames,
        size,
    )?;
    stream.flush()?;
    Ok(())
}

fn main() -> Result<(), AnyError> {
    match parse_command()? {
        Command::Merge(options) => merge_segments(options),
        Command::AudioMonitor(options) => run_audio_monitor(options),
        Command::Capture(options) => run_capture(options),
    }
}

fn write_audio_runtime_info(path: &Path, audio: &AudioRuntime) -> Result<(), AnyError> {
    fs::write(
        path,
        format!(
            concat!(
                "{{\n  \"schema\": 1,\n  \"desktop_device_id\": \"{}\",\n",
                "  \"desktop_device_name\": \"{}\",\n  \"microphone_enabled\": {},\n",
                "  \"microphone_device_id\": {},\n  \"microphone_device_name\": {}\n}}\n"
            ),
            json_escape(&audio.desktop_device_id),
            json_escape(&audio.desktop_device_name),
            audio.microphone_enabled,
            json_optional_string(audio.microphone_device_id.as_deref()),
            json_optional_string(audio.microphone_device_name.as_deref()),
        ),
    )?;
    Ok(())
}

fn run_audio_monitor(options: AudioMonitorOptions) -> Result<(), AnyError> {
    fs::create_dir_all(&options.work_directory)?;
    if let Some(parent) = options.audio_levels.parent() {
        fs::create_dir_all(parent)?;
    }
    let mut audio = AudioRuntime::start(AudioConfig {
        segment_directory: options.work_directory.clone(),
        manifest: options.work_directory.join("unused-audio-segments.jsonl"),
        levels_file: options.audio_levels.clone(),
        max_segments: 2,
        microphone_enabled: true,
        microphone_device_id: options.microphone_device_id,
        microphone_gain_percent: options.microphone_gain_percent,
    })
    .map_err(|error| format!("声音设备预检启动失败：{error}"))?;
    write_audio_runtime_info(&options.audio_info, &audio)?;
    emit_status("audio_monitor_started", &audio.desktop_device_name);
    loop {
        if options.stop_file.exists() {
            break;
        }
        if let Some(error) = audio.poll_error() {
            return Err(format!("声音设备预检失败：{error}").into());
        }
        thread::sleep(Duration::from_millis(100));
    }
    let (end_qpc, _) = qpc_now()?;
    audio
        .stop(end_qpc)
        .map_err(|error| format!("声音设备预检停止失败：{error}"))?;
    emit_status("audio_monitor_stopped", "ok");
    Ok(())
}

fn run_capture(options: CaptureOptions) -> Result<(), AnyError> {
    let encoder_name = if options.encoder_mode == EncoderMode::Gpu {
        hardware_h264_encoder_name()?.ok_or(
            "未检测到 Media Foundation 硬件 H.264 编码器；程序不会静默切换 CPU，请手动选择 CPU 模式",
        )?
    } else {
        "Media Foundation software H.264".to_owned()
    };
    fs::create_dir_all(&options.segment_directory)?;
    if let Some(parent) = options.metadata.parent() {
        fs::create_dir_all(parent)?;
    }
    let monitor = Monitor::from_index(options.monitor)?;
    let source_width = monitor.width()?;
    let source_height = monitor.height()?;
    let source_name = format!("monitor:{}:{}x{}", options.monitor, source_width, source_height);
    let mode_name = if options.encoder_mode == EncoderMode::Gpu { "gpu" } else { "cpu" };
    fs::write(
        &options.metadata,
        format!(
            concat!(
                "{{\n  \"schema\": 2,\n  \"mode\": \"segmented_replay_buffer\",\n",
                "  \"source\": \"{}\",\n  \"encoder_mode\": \"{}\",\n",
                "  \"encoder_name\": \"{}\",\n  \"codec\": \"H264\",\n",
                "  \"width\": {},\n  \"height\": {},\n  \"source_width\": {},\n",
                "  \"source_height\": {},\n  \"requested_fps\": {},\n  \"bitrate\": {},\n",
                "  \"status\": \"buffering\"\n}}\n"
            ),
            json_escape(&source_name),
            mode_name,
            json_escape(&encoder_name),
            options.width,
            options.height,
            source_width,
            source_height,
            options.fps,
            options.bitrate,
        ),
    )?;
    emit_status("encoder_selected", &encoder_name);
    let factory = EncoderFactory {
        width: options.width,
        height: options.height,
        source_width,
        source_height,
        fps: options.fps,
        bitrate: options.bitrate,
        hardware: options.encoder_mode == EncoderMode::Gpu,
    };
    let flags = CaptureFlags {
        metadata: options.metadata,
        duration: options.duration,
        fps: options.fps,
        bitrate: options.bitrate,
        encoder_mode: options.encoder_mode,
        source_name,
        stop_file: options.stop_file,
        segment_directory: options.segment_directory,
        manifest: options.manifest,
        rotate_file: options.rotate_file,
        rotate_ack: options.rotate_ack,
        segment_ticks: i64::try_from(options.segment_seconds)? * 10_000_000,
        max_segments: options.max_segments,
        encoder_name,
        factory,
        audio_manifest: options.audio_manifest,
        audio_levels: options.audio_levels,
        audio_info: options.audio_info,
        record_microphone: options.record_microphone,
        microphone_device_id: options.microphone_device_id,
        microphone_gain_percent: options.microphone_gain_percent,
    };
    Capture::start(capture_settings(monitor, flags))?;
    Ok(())
}

fn merge_segments(options: MergeOptions) -> Result<(), AnyError> {
    if options.segments.is_empty() {
        return Err("没有可合并的录像分段".into());
    }
    if options.output.exists() {
        return Err(format!("输出文件已经存在：{}", options.output.display()).into());
    }
    if let Some(parent) = options.output.parent() {
        fs::create_dir_all(parent)?;
    }
    let part = options.output.with_extension("mp4.part");
    let _ = fs::remove_file(&part);
    let result = merge_segments_to_part(
        &options.segments,
        &options.desktop_segments,
        &options.microphone_segments,
        &part,
    );
    if let Err(error) = result {
        let _ = fs::remove_file(&part);
        return Err(error);
    }
    fs::rename(&part, &options.output)?;
    emit_status("merge_finished", &format!("output={}", options.output.display()));
    Ok(())
}

fn merge_segments_to_part(
    segments: &[PathBuf],
    desktop_segments: &[PathBuf],
    microphone_segments: &[PathBuf],
    part: &Path,
) -> Result<(), AnyError> {
    if desktop_segments.len() != segments.len() {
        return Err("桌面声音分段数量与视频分段数量不一致".into());
    }
    if !microphone_segments.is_empty() && microphone_segments.len() != segments.len() {
        return Err("麦克风分段数量与视频分段数量不一致".into());
    }

    let (config, video_track) = media_track_config(&segments[0], MediaType::H264)?;
    let (_, desktop_track) = media_track_config(&desktop_segments[0], MediaType::AAC)?;
    let microphone_track = if microphone_segments.is_empty() {
        None
    } else {
        Some(media_track_config(&microphone_segments[0], MediaType::AAC)?.1)
    };
    let mut writer = Mp4Writer::write_start(BufWriter::new(File::create(part)?), &config)?;
    writer.add_track(&video_track)?;
    writer.add_track(&desktop_track)?;
    if let Some(track) = microphone_track.as_ref() {
        writer.add_track(track)?;
    }

    let video_samples = append_track_segments(&mut writer, 1, segments, MediaType::H264, &video_track)?;
    let desktop_samples =
        append_track_segments(&mut writer, 2, desktop_segments, MediaType::AAC, &desktop_track)?;
    let microphone_samples = if let Some(track) = microphone_track.as_ref() {
        append_track_segments(&mut writer, 3, microphone_segments, MediaType::AAC, track)?
    } else {
        0
    };
    writer.write_end()?;
    let mut output = writer.into_writer();
    output.flush()?;
    drop(output);

    let verify_file = File::open(part)?;
    let verify_size = verify_file.metadata()?.len();
    let verify = Mp4Reader::read_header(BufReader::new(verify_file), verify_size)?;
    let verify_video = verify
        .tracks()
        .values()
        .find(|track| track.media_type().ok() == Some(MediaType::H264))
        .ok_or("合并后的 MP4 没有 H.264 视频轨")?;
    if verify.sample_count(verify_video.track_id())? != video_samples {
        return Err("合并后的 MP4 样本数校验失败".into());
    }
    let audio_tracks: Vec<_> = verify
        .tracks()
        .values()
        .filter(|track| track.media_type().ok() == Some(MediaType::AAC))
        .collect();
    let expected_audio_tracks = if microphone_segments.is_empty() { 1 } else { 2 };
    if audio_tracks.len() != expected_audio_tracks {
        return Err("合并后的 MP4 音轨数量校验失败".into());
    }
    if verify.sample_count(audio_tracks[0].track_id())? != desktop_samples {
        return Err("合并后的桌面声音样本数校验失败".into());
    }
    if expected_audio_tracks == 2
        && verify.sample_count(audio_tracks[1].track_id())? != microphone_samples
    {
        return Err("合并后的麦克风样本数校验失败".into());
    }
    Ok(())
}

fn media_track_config(path: &Path, media_type: MediaType) -> Result<(Mp4Config, TrackConfig), AnyError> {
    let file = File::open(path)?;
    let size = file.metadata()?.len();
    let reader = Mp4Reader::read_header(BufReader::new(file), size)?;
    let track = reader
        .tracks()
        .values()
        .find(|track| track.media_type().ok() == Some(media_type))
        .ok_or_else(|| format!("分段没有所需的 {:?} 轨道：{}", media_type, path.display()))?;
    let media_conf = match media_type {
        MediaType::H264 => MediaConfig::AvcConfig(AvcConfig {
            width: track.width(),
            height: track.height(),
            seq_param_set: track.sequence_parameter_set()?.to_vec(),
            pic_param_set: track.picture_parameter_set()?.to_vec(),
        }),
        MediaType::AAC => MediaConfig::AacConfig(AacConfig {
            bitrate: track.bitrate(),
            profile: track.audio_profile()?,
            freq_index: track.sample_freq_index()?,
            chan_conf: track.channel_config()?,
        }),
        _ => return Err("当前合并器只支持 H.264 与 AAC".into()),
    };
    Ok((
        Mp4Config {
            major_brand: *reader.major_brand(),
            minor_version: reader.minor_version(),
            compatible_brands: reader.compatible_brands().to_vec(),
            timescale: reader.timescale(),
        },
        TrackConfig {
            track_type: track.track_type()?,
            timescale: track.timescale(),
            language: track.language().to_owned(),
            media_conf,
        },
    ))
}

fn append_track_segments(
    writer: &mut Mp4Writer<BufWriter<File>>,
    output_track_id: u32,
    segments: &[PathBuf],
    media_type: MediaType,
    expected: &TrackConfig,
) -> Result<u32, AnyError> {
    let mut total_samples = 0_u32;
    for segment in segments {
        let (_, actual) = media_track_config(segment, media_type)?;
        if &actual != expected {
            return Err(format!("分段编码参数不一致：{}", segment.display()).into());
        }
        let file = File::open(segment)?;
        let size = file.metadata()?.len();
        let mut reader = Mp4Reader::read_header(BufReader::new(file), size)?;
        let track = reader
            .tracks()
            .values()
            .find(|track| track.media_type().ok() == Some(media_type))
            .ok_or_else(|| format!("无法重新读取轨道：{}", segment.display()))?;
        let source_track_id = track.track_id();
        let sample_count = reader.sample_count(source_track_id)?;
        if sample_count == 0 {
            return Err(format!("分段没有媒体样本：{}", segment.display()).into());
        }
        for sample_id in 1..=sample_count {
            let sample = reader
                .read_sample(source_track_id, sample_id)?
                .ok_or_else(|| format!("无法读取样本 {sample_id}：{}", segment.display()))?;
            if media_type == MediaType::H264 && sample_id == 1 && (!sample.is_sync || sample.start_time != 0) {
                return Err(format!("录像分段不是从可解码关键帧开始：{}", segment.display()).into());
            }
            if sample.duration == 0 || sample.rendering_offset < 0 {
                return Err(format!("分段包含不受支持的时间戳：{}", segment.display()).into());
            }
            writer.write_sample(output_track_id, &sample)?;
            total_samples = total_samples.saturating_add(1);
        }
    }
    Ok(total_samples)
}

fn capture_settings<T>(source: T, flags: CaptureFlags) -> Settings<CaptureFlags, T>
where
    T: TryInto<windows_capture::settings::GraphicsCaptureItemType>,
    T::Error: std::fmt::Debug,
{
    let interval = Duration::from_nanos(1_000_000_000_u64 / u64::from(flags.fps.max(1)));
    Settings::new(
        source,
        CursorCaptureSettings::WithoutCursor,
        DrawBorderSettings::WithoutBorder,
        SecondaryWindowSettings::Exclude,
        MinimumUpdateIntervalSettings::Custom(interval),
        DirtyRegionSettings::Default,
        ColorFormat::Bgra8,
        flags,
    )
}

fn parse_command() -> Result<Command, AnyError> {
    let arguments: Vec<String> = env::args().skip(1).collect();
    if arguments.iter().any(|argument| argument == "--merge-output") {
        let mut output = None;
        let mut segments = Vec::new();
        let mut desktop_segments = Vec::new();
        let mut microphone_segments = Vec::new();
        let mut index = 0;
        while index < arguments.len() {
            let argument = &arguments[index];
            index += 1;
            let value = arguments.get(index).ok_or_else(|| format!("参数缺少值：{argument}"))?;
            index += 1;
            match argument.as_str() {
                "--merge-output" => output = Some(PathBuf::from(value)),
                "--segment" => segments.push(PathBuf::from(value)),
                "--desktop-segment" => desktop_segments.push(PathBuf::from(value)),
                "--microphone-segment" => microphone_segments.push(PathBuf::from(value)),
                other => return Err(format!("未知合并参数：{other}").into()),
            }
        }
        return Ok(Command::Merge(MergeOptions {
            output: output.ok_or("必须提供 --merge-output")?,
            segments,
            desktop_segments,
            microphone_segments,
        }));
    }

    if arguments.iter().any(|argument| argument == "--audio-monitor") {
        let mut stop_file = None;
        let mut work_directory = None;
        let mut audio_levels = None;
        let mut audio_info = None;
        let mut microphone_device_id = None;
        let mut microphone_gain_percent = 100_u32;
        let mut index = 0;
        while index < arguments.len() {
            let argument = &arguments[index];
            index += 1;
            let value = arguments.get(index).ok_or_else(|| format!("参数缺少值：{argument}"))?;
            index += 1;
            match argument.as_str() {
                "--audio-monitor" => {
                    let enabled: bool = value.parse()?;
                    if !enabled {
                        return Err("--audio-monitor 必须为 true".into());
                    }
                }
                "--stop-file" => stop_file = Some(PathBuf::from(value)),
                "--work-directory" => work_directory = Some(PathBuf::from(value)),
                "--audio-levels" => audio_levels = Some(PathBuf::from(value)),
                "--audio-info" => audio_info = Some(PathBuf::from(value)),
                "--microphone-device-id" => {
                    if !value.is_empty() {
                        microphone_device_id = Some(value.to_owned());
                    }
                }
                "--microphone-gain-percent" => microphone_gain_percent = value.parse()?,
                other => return Err(format!("未知声音预检参数：{other}").into()),
            }
        }
        let work_directory = work_directory.ok_or("声音预检必须提供 --work-directory")?;
        return Ok(Command::AudioMonitor(AudioMonitorOptions {
            stop_file: stop_file.unwrap_or_else(|| work_directory.join(".stop")),
            audio_levels: audio_levels.unwrap_or_else(|| work_directory.join("audio-levels.json")),
            audio_info: audio_info.unwrap_or_else(|| work_directory.join("audio-info.json")),
            work_directory,
            microphone_device_id,
            microphone_gain_percent: microphone_gain_percent.min(200),
        }));
    }

    let mut metadata = None;
    let mut monitor = 1_usize;
    let mut duration_seconds = 86_400_u64;
    let mut width = 1920_u32;
    let mut height = 1080_u32;
    let mut fps = 30_u32;
    let mut bitrate = 12_000_000_u32;
    let mut encoder_mode = EncoderMode::Gpu;
    let mut stop_file = None;
    let mut segment_directory = None;
    let mut manifest = None;
    let mut rotate_file = None;
    let mut rotate_ack = None;
    let mut segment_seconds = 10_u64;
    let mut max_segments = 183_usize;
    let mut audio_manifest = None;
    let mut audio_levels = None;
    let mut audio_info = None;
    let mut record_microphone = false;
    let mut microphone_device_id = None;
    let mut microphone_gain_percent = 100_u32;
    let mut index = 0;
    while index < arguments.len() {
        let argument = &arguments[index];
        index += 1;
        let value = arguments.get(index).ok_or_else(|| format!("参数缺少值：{argument}"))?;
        index += 1;
        match argument.as_str() {
            "--metadata" => metadata = Some(PathBuf::from(value)),
            "--monitor" => monitor = value.parse()?,
            "--duration" => duration_seconds = value.parse()?,
            "--width" => width = value.parse()?,
            "--height" => height = value.parse()?,
            "--fps" => fps = value.parse()?,
            "--bitrate" => bitrate = value.parse()?,
            "--encoder" => {
                encoder_mode = match value.to_ascii_lowercase().as_str() {
                    "gpu" => EncoderMode::Gpu,
                    "cpu" => EncoderMode::Cpu,
                    other => return Err(format!("未知编码模式：{other}").into()),
                }
            }
            "--stop-file" => stop_file = Some(PathBuf::from(value)),
            "--segment-directory" => segment_directory = Some(PathBuf::from(value)),
            "--manifest" => manifest = Some(PathBuf::from(value)),
            "--rotate-file" => rotate_file = Some(PathBuf::from(value)),
            "--rotate-ack" => rotate_ack = Some(PathBuf::from(value)),
            "--segment-seconds" => segment_seconds = value.parse()?,
            "--max-segments" => max_segments = value.parse()?,
            "--audio-manifest" => audio_manifest = Some(PathBuf::from(value)),
            "--audio-levels" => audio_levels = Some(PathBuf::from(value)),
            "--audio-info" => audio_info = Some(PathBuf::from(value)),
            "--record-microphone" => record_microphone = value.parse()?,
            "--microphone-device-id" => {
                if !value.is_empty() {
                    microphone_device_id = Some(value.to_owned());
                }
            }
            "--microphone-gain-percent" => microphone_gain_percent = value.parse()?,
            other => return Err(format!("未知参数：{other}").into()),
        }
    }
    let directory = segment_directory.ok_or("必须提供 --segment-directory")?;
    Ok(Command::Capture(CaptureOptions {
        metadata: metadata.unwrap_or_else(|| directory.join("buffer-metadata.json")),
        monitor,
        duration: Duration::from_secs(duration_seconds.max(1)),
        width,
        height,
        fps,
        bitrate,
        encoder_mode,
        stop_file: stop_file.unwrap_or_else(|| directory.join(".stop")),
        manifest: manifest.unwrap_or_else(|| directory.join("segments.jsonl")),
        rotate_file: rotate_file.unwrap_or_else(|| directory.join(".rotate")),
        rotate_ack: rotate_ack.unwrap_or_else(|| directory.join(".rotate-ack")),
        segment_directory: directory.clone(),
        segment_seconds: segment_seconds.max(2),
        max_segments: max_segments.max(2),
        audio_manifest: audio_manifest.unwrap_or_else(|| directory.join("audio-segments.jsonl")),
        audio_levels: audio_levels.unwrap_or_else(|| directory.join("audio-levels.json")),
        audio_info: audio_info.unwrap_or_else(|| directory.join("audio-info.json")),
        record_microphone,
        microphone_device_id,
        microphone_gain_percent: microphone_gain_percent.min(200),
    }))
}

fn segment_path(directory: &Path, index: u64) -> PathBuf {
    directory.join(format!("segment-{index:06}.mp4"))
}

fn hardware_h264_encoder_name() -> Result<Option<String>, AnyError> {
    unsafe {
        CoInitializeEx(None, COINIT_MULTITHREADED).ok()?;
        let mut activates = std::ptr::null_mut();
        let mut count = 0_u32;
        let output_type = MFT_REGISTER_TYPE_INFO {
            guidMajorType: MFMediaType_Video,
            guidSubtype: MFVideoFormat_H264,
        };
        let result = MFTEnumEx(
            MFT_CATEGORY_VIDEO_ENCODER,
            MFT_ENUM_FLAG_HARDWARE,
            None,
            Some(&output_type),
            &mut activates,
            &mut count,
        );
        let mut encoder_name = None;
        if !activates.is_null() {
            if let Some(Some(activation)) = std::slice::from_raw_parts(activates, count as usize).first() {
                let length = activation.GetStringLength(&MFT_FRIENDLY_NAME_Attribute)?;
                let mut value = vec![0_u16; length as usize + 1];
                activation.GetString(&MFT_FRIENDLY_NAME_Attribute, &mut value, None)?;
                encoder_name = Some(String::from_utf16_lossy(&value[..length as usize]));
            }
            for activation in std::slice::from_raw_parts_mut(activates, count as usize) {
                drop(activation.take());
            }
            CoTaskMemFree(Some(activates.cast()));
        }
        CoUninitialize();
        result?;
        Ok(encoder_name)
    }
}

fn qpc_now() -> Result<(i64, i64), AnyError> {
    unsafe {
        let mut counter = 0_i64;
        let mut frequency = 0_i64;
        QueryPerformanceCounter(&mut counter)?;
        QueryPerformanceFrequency(&mut frequency)?;
        Ok((counter, frequency))
    }
}

fn emit_status(event: &str, detail: &str) {
    println!("{{\"event\":\"{}\",\"detail\":\"{}\"}}", json_escape(event), json_escape(detail));
}

fn json_escape(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"").replace('\n', "\\n")
}

fn json_optional_string(value: Option<&str>) -> String {
    value
        .map(|text| format!("\"{}\"", json_escape(text)))
        .unwrap_or_else(|| "null".to_owned())
}
