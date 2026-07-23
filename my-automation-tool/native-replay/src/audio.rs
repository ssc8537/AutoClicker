use std::collections::VecDeque;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, AtomicI64, AtomicU32, AtomicU64, Ordering};
use std::sync::mpsc::{self, Receiver, SyncSender};
use std::sync::Arc;
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};

use wasapi::{
    deinitialize, initialize_mta, DeviceEnumerator, Direction, SampleType, StreamMode,
    WasapiError, WaveFormat,
};
use windows_capture::encoder::{
    AudioSettingsBuilder, ContainerSettingsBuilder, VideoEncoder, VideoSettingsBuilder,
};

const SAMPLE_RATE: u32 = 48_000;
const CHANNELS: u32 = 2;
const BITS_PER_SAMPLE: u32 = 16;
const FRAME_BYTES: usize = (CHANNELS as usize) * (BITS_PER_SAMPLE as usize / 8);
const QPC_TICKS_PER_SECOND: i64 = 10_000_000;
const MAX_RECOVERABLE_GAP_FRAMES: usize = (SAMPLE_RATE as usize) * 2;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum AudioSource {
    Desktop,
    Microphone,
}

impl AudioSource {
    fn name(self) -> &'static str {
        match self {
            Self::Desktop => "desktop",
            Self::Microphone => "microphone",
        }
    }
}

pub struct AudioConfig {
    pub segment_directory: PathBuf,
    pub manifest: PathBuf,
    pub levels_file: PathBuf,
    pub max_segments: usize,
    pub microphone_enabled: bool,
    pub microphone_device_id: Option<String>,
    pub microphone_gain_percent: u32,
    pub desktop_gain_percent: u32,
}

struct SharedState {
    segment_index: AtomicU64,
    segment_start_qpc: AtomicI64,
    stop_qpc: AtomicI64,
    stop: AtomicBool,
    desktop_peak: AtomicU32,
    microphone_peak: AtomicU32,
    desktop_discontinuities: AtomicU32,
    microphone_discontinuities: AtomicU32,
}

struct PcmSegment {
    source: AudioSource,
    index: u64,
    start_qpc: i64,
    end_qpc: i64,
    bytes: Vec<u8>,
    peak_percent: u32,
}

struct ReadyInfo {
    source: AudioSource,
    device_id: String,
    device_name: String,
}

pub struct AudioRuntime {
    shared: Arc<SharedState>,
    capture_threads: Vec<JoinHandle<()>>,
    encoder_thread: Option<JoinHandle<()>>,
    level_thread: Option<JoinHandle<()>>,
    error_rx: Receiver<String>,
    pub desktop_device_id: String,
    pub desktop_device_name: String,
    pub microphone_device_id: Option<String>,
    pub microphone_device_name: Option<String>,
    pub microphone_enabled: bool,
}

impl AudioRuntime {
    pub fn start(config: AudioConfig) -> Result<Self, String> {
        fs::create_dir_all(&config.segment_directory).map_err(|error| error.to_string())?;
        let shared = Arc::new(SharedState {
            segment_index: AtomicU64::new(0),
            segment_start_qpc: AtomicI64::new(0),
            stop_qpc: AtomicI64::new(0),
            stop: AtomicBool::new(false),
            desktop_peak: AtomicU32::new(0),
            microphone_peak: AtomicU32::new(0),
            desktop_discontinuities: AtomicU32::new(0),
            microphone_discontinuities: AtomicU32::new(0),
        });
        let (segment_tx, segment_rx) = mpsc::sync_channel::<PcmSegment>(8);
        let (ready_tx, ready_rx) = mpsc::channel::<Result<ReadyInfo, String>>();
        let (error_tx, error_rx) = mpsc::channel::<String>();

        let encoder_thread = spawn_audio_encoder(
            segment_rx,
            error_tx.clone(),
            config.segment_directory.clone(),
            config.manifest.clone(),
            config.max_segments,
        );
        let level_thread = spawn_level_writer(
            shared.clone(),
            config.levels_file.clone(),
            config.microphone_enabled,
        );

        let mut capture_threads = Vec::new();
        capture_threads.push(spawn_capture_thread(
            AudioSource::Desktop,
            None,
            config.desktop_gain_percent.min(300),
            shared.clone(),
            segment_tx.clone(),
            ready_tx.clone(),
            error_tx.clone(),
        ));
        if config.microphone_enabled {
            capture_threads.push(spawn_capture_thread(
                AudioSource::Microphone,
                config.microphone_device_id.clone(),
                config.microphone_gain_percent.min(200),
                shared.clone(),
                segment_tx.clone(),
                ready_tx.clone(),
                error_tx.clone(),
            ));
        }
        drop(segment_tx);
        drop(ready_tx);
        drop(error_tx);

        let expected = if config.microphone_enabled { 2 } else { 1 };
        let mut desktop = None;
        let mut microphone = None;
        for _ in 0..expected {
            match ready_rx.recv_timeout(Duration::from_secs(5)) {
                Ok(Ok(info)) => match info.source {
                    AudioSource::Desktop => desktop = Some(info),
                    AudioSource::Microphone => microphone = Some(info),
                },
                Ok(Err(error)) => {
                    shared.stop.store(true, Ordering::Release);
                    for handle in capture_threads {
                        let _ = handle.join();
                    }
                    let _ = encoder_thread.join();
                    let _ = level_thread.join();
                    return Err(error);
                }
                Err(_) => {
                    shared.stop.store(true, Ordering::Release);
                    for handle in capture_threads {
                        let _ = handle.join();
                    }
                    let _ = encoder_thread.join();
                    let _ = level_thread.join();
                    return Err("等待WASAPI音频设备启动超时".to_owned());
                }
            }
        }
        let desktop = desktop.ok_or("桌面声音设备没有完成初始化")?;
        Ok(Self {
            shared,
            capture_threads,
            encoder_thread: Some(encoder_thread),
            level_thread: Some(level_thread),
            error_rx,
            desktop_device_id: desktop.device_id,
            desktop_device_name: desktop.device_name,
            microphone_device_id: microphone.as_ref().map(|info| info.device_id.clone()),
            microphone_device_name: microphone.map(|info| info.device_name),
            microphone_enabled: config.microphone_enabled,
        })
    }

    pub fn begin_segment(&self, index: u64, start_qpc: i64) {
        self.shared.segment_start_qpc.store(start_qpc, Ordering::Release);
        self.shared.segment_index.store(index, Ordering::Release);
    }

    pub fn poll_error(&self) -> Option<String> {
        self.error_rx.try_recv().ok()
    }

    pub fn discontinuities(&self) -> (u32, u32) {
        (
            self.shared.desktop_discontinuities.load(Ordering::Relaxed),
            self.shared.microphone_discontinuities.load(Ordering::Relaxed),
        )
    }

    pub fn stop(&mut self, end_qpc: i64) -> Result<(), String> {
        self.shared.stop_qpc.store(end_qpc, Ordering::Release);
        self.shared.stop.store(true, Ordering::Release);
        for handle in self.capture_threads.drain(..) {
            handle.join().map_err(|_| "WASAPI采集线程异常退出".to_owned())?;
        }
        if let Some(handle) = self.encoder_thread.take() {
            handle.join().map_err(|_| "AAC编码线程异常退出".to_owned())?;
        }
        if let Some(handle) = self.level_thread.take() {
            handle.join().map_err(|_| "声音电平线程异常退出".to_owned())?;
        }
        if let Some(error) = self.poll_error() {
            return Err(error);
        }
        Ok(())
    }
}

impl Drop for AudioRuntime {
    fn drop(&mut self) {
        self.shared.stop.store(true, Ordering::Release);
        for handle in self.capture_threads.drain(..) {
            let _ = handle.join();
        }
        if let Some(handle) = self.encoder_thread.take() {
            let _ = handle.join();
        }
        if let Some(handle) = self.level_thread.take() {
            let _ = handle.join();
        }
    }
}

fn spawn_capture_thread(
    source: AudioSource,
    device_id: Option<String>,
    gain_percent: u32,
    shared: Arc<SharedState>,
    segment_tx: SyncSender<PcmSegment>,
    ready_tx: mpsc::Sender<Result<ReadyInfo, String>>,
    error_tx: mpsc::Sender<String>,
) -> JoinHandle<()> {
    thread::Builder::new()
        .name(format!("wasapi-{}", source.name()))
        .spawn(move || {
            let result = capture_loop(
                source,
                device_id,
                gain_percent,
                shared,
                segment_tx,
                ready_tx.clone(),
            );
            if let Err(error) = result {
                let _ = ready_tx.send(Err(error.clone()));
                let _ = error_tx.send(error);
            }
        })
        .expect("failed to create WASAPI capture thread")
}

fn capture_loop(
    source: AudioSource,
    device_id: Option<String>,
    gain_percent: u32,
    shared: Arc<SharedState>,
    segment_tx: SyncSender<PcmSegment>,
    ready_tx: mpsc::Sender<Result<ReadyInfo, String>>,
) -> Result<(), String> {
    initialize_mta().ok().map_err(|error| error.to_string())?;
    let result = (|| -> Result<(), String> {
        let enumerator = DeviceEnumerator::new().map_err(|error| error.to_string())?;
        let endpoint_direction = match source {
            AudioSource::Desktop => Direction::Render,
            AudioSource::Microphone => Direction::Capture,
        };
        let device_deadline = Instant::now() + Duration::from_secs(2);
        let device = loop {
            let result = match device_id.as_deref() {
                Some(identifier) => enumerator.get_device(identifier),
                None => enumerator.get_default_device(&endpoint_direction),
            };
            match result {
                Ok(device) => break device,
                Err(_) if Instant::now() < device_deadline => {
                    thread::sleep(Duration::from_millis(100));
                }
                Err(error) => {
                    return Err(format!(
                        "无法打开{}设备（已重试2秒）：{error}",
                        source_label(source)
                    ));
                }
            }
        };
        let actual_id = device.get_id().map_err(|error| error.to_string())?;
        let actual_name = device.get_friendlyname().map_err(|error| error.to_string())?;
        let mut client = device.get_iaudioclient().map_err(|error| error.to_string())?;
        let format = WaveFormat::new(
            BITS_PER_SAMPLE as usize,
            BITS_PER_SAMPLE as usize,
            &SampleType::Int,
            SAMPLE_RATE as usize,
            CHANNELS as usize,
            None,
        );
        let (_default_period, minimum_period) = client.get_device_period().map_err(|error| error.to_string())?;
        let mode = StreamMode::EventsShared {
            autoconvert: true,
            buffer_duration_hns: minimum_period,
        };
        client
            .initialize_client(&format, &Direction::Capture, &mode)
            .map_err(|error| format!("{}设备不支持48kHz立体声采集：{error}", source_label(source)))?;
        let event = client.set_get_eventhandle().map_err(|error| error.to_string())?;
        let capture = client.get_audiocaptureclient().map_err(|error| error.to_string())?;
        client.start_stream().map_err(|error| error.to_string())?;
        ready_tx
            .send(Ok(ReadyInfo {
                source,
                device_id: actual_id,
                device_name: actual_name,
            }))
            .map_err(|_| "主录像线程已关闭".to_owned())?;

        let mut collector = PcmCollector::new(source, gain_percent, segment_tx, shared.clone());
        let mut seen_packet = false;
        while !shared.stop.load(Ordering::Acquire) {
            collector.sync_segment()?;
            match event.wait_for_event(100) {
                Ok(()) => loop {
                    let frames = capture
                        .get_next_packet_size()
                        .map_err(|error| error.to_string())?
                        .unwrap_or(0);
                    if frames == 0 {
                        break;
                    }
                    let mut bytes = vec![0_u8; frames as usize * FRAME_BYTES];
                    let (read_frames, info) = capture
                        .read_from_device(&mut bytes)
                        .map_err(|error| error.to_string())?;
                    bytes.truncate(read_frames as usize * FRAME_BYTES);
                    if info.flags.timestamp_error {
                        return Err(format!("{}时间戳无效，已停止以避免音画错位", source_label(source)));
                    }
                    if seen_packet && info.flags.data_discontinuity {
                        let counter = match source {
                            AudioSource::Desktop => &shared.desktop_discontinuities,
                            AudioSource::Microphone => &shared.microphone_discontinuities,
                        };
                        let count = counter.fetch_add(1, Ordering::Relaxed) + 1;
                        if count <= 3 || count % 10 == 0 {
                            crate::emit_status(
                                "audio_discontinuity_recovered",
                                &format!("source={};count={count}", source.name()),
                            );
                        }
                    }
                    seen_packet = true;
                    if info.flags.silent {
                        bytes.fill(0);
                    }
                    collector.push_packet(info.timestamp as i64, bytes)?;
                },
                Err(WasapiError::EventTimeout) => {}
                Err(error) => return Err(format!("{}事件等待失败：{error}", source_label(source))),
            }
        }
        collector.finish(shared.stop_qpc.load(Ordering::Acquire))?;
        client.stop_stream().map_err(|error| error.to_string())?;
        Ok(())
    })();
    deinitialize();
    result
}

struct PcmCollector {
    source: AudioSource,
    gain_percent: u32,
    sender: SyncSender<PcmSegment>,
    shared: Arc<SharedState>,
    index: u64,
    start_qpc: i64,
    bytes: Vec<u8>,
    peak_percent: u32,
}

impl PcmCollector {
    fn new(
        source: AudioSource,
        gain_percent: u32,
        sender: SyncSender<PcmSegment>,
        shared: Arc<SharedState>,
    ) -> Self {
        Self {
            source,
            gain_percent,
            sender,
            shared,
            index: 0,
            start_qpc: 0,
            bytes: Vec::new(),
            peak_percent: 0,
        }
    }

    fn sync_segment(&mut self) -> Result<(), String> {
        let target = self.shared.segment_index.load(Ordering::Acquire);
        if target == 0 || target == self.index {
            return Ok(());
        }
        let target_start = self.shared.segment_start_qpc.load(Ordering::Acquire);
        if self.index == 0 {
            self.index = target;
            self.start_qpc = target_start;
            return Ok(());
        }
        if target != self.index + 1 {
            return Err(format!("{}错过录像分段边界", source_label(self.source)));
        }
        self.finalize_at(target_start)?;
        self.index = target;
        self.start_qpc = target_start;
        Ok(())
    }

    fn push_packet(&mut self, packet_start_qpc: i64, mut bytes: Vec<u8>) -> Result<(), String> {
        self.sync_segment()?;
        if bytes.is_empty() {
            return Ok(());
        }
        apply_gain(&mut bytes, self.gain_percent);
        let peak = peak_percent(&bytes);
        self.peak_percent = self.peak_percent.max(peak);
        match self.source {
            AudioSource::Desktop => self.shared.desktop_peak.fetch_max(peak, Ordering::Relaxed),
            AudioSource::Microphone => self.shared.microphone_peak.fetch_max(peak, Ordering::Relaxed),
        };
        // Audio-only device preview has no active recording segment. It reports
        // the real PCM peak without retaining or encoding any audio samples.
        if self.index == 0 {
            return Ok(());
        }
        self.append_at(packet_start_qpc, &bytes)
    }

    fn append_at(&mut self, packet_start_qpc: i64, bytes: &[u8]) -> Result<(), String> {
        let packet_frames = bytes.len() / FRAME_BYTES;
        let expected_frame = qpc_to_frames(packet_start_qpc.saturating_sub(self.start_qpc));
        let current_frames = self.bytes.len() / FRAME_BYTES;
        let mut source_frame = 0_usize;
        if expected_frame > current_frames {
            if expected_frame - current_frames > MAX_RECOVERABLE_GAP_FRAMES {
                return Err(format!(
                    "{}连续缺音超过2秒，已停止以避免严重音画错位",
                    source_label(self.source)
                ));
            }
            self.bytes.resize(expected_frame * FRAME_BYTES, 0);
        } else if current_frames > expected_frame {
            if current_frames - expected_frame > MAX_RECOVERABLE_GAP_FRAMES {
                return Err(format!(
                    "{}时间戳倒退超过2秒，已停止以避免严重音画错位",
                    source_label(self.source)
                ));
            }
            source_frame = (current_frames - expected_frame).min(packet_frames);
        }
        self.bytes.extend_from_slice(&bytes[source_frame * FRAME_BYTES..]);
        Ok(())
    }

    fn finalize_at(&mut self, end_qpc: i64) -> Result<(), String> {
        if self.index == 0 || end_qpc <= self.start_qpc {
            return Ok(());
        }
        let expected_frames = qpc_to_frames(end_qpc - self.start_qpc);
        self.bytes.resize(expected_frames * FRAME_BYTES, 0);
        self.bytes.truncate(expected_frames * FRAME_BYTES);
        let segment = PcmSegment {
            source: self.source,
            index: self.index,
            start_qpc: self.start_qpc,
            end_qpc,
            bytes: std::mem::take(&mut self.bytes),
            peak_percent: self.peak_percent,
        };
        self.peak_percent = 0;
        self.sender
            .try_send(segment)
            .map_err(|_| format!("{}AAC编码队列已满", source_label(self.source)))
    }

    fn finish(&mut self, end_qpc: i64) -> Result<(), String> {
        self.sync_segment()?;
        self.finalize_at(end_qpc)
    }
}

fn spawn_audio_encoder(
    receiver: Receiver<PcmSegment>,
    error_tx: mpsc::Sender<String>,
    directory: PathBuf,
    manifest: PathBuf,
    max_segments: usize,
) -> JoinHandle<()> {
    thread::Builder::new()
        .name("aac-segment-encoder".to_owned())
        .spawn(move || {
            let mut desktop = VecDeque::<PathBuf>::new();
            let mut microphone = VecDeque::<PathBuf>::new();
            while let Ok(segment) = receiver.recv() {
                let path = directory.join(format!(
                    "{}-{:06}.mp4",
                    segment.source.name(),
                    segment.index
                ));
                let result = encode_pcm_segment(&path, &segment)
                    .and_then(|_| append_audio_manifest(&manifest, &path, &segment));
                if let Err(error) = result {
                    let _ = error_tx.send(format!(
                        "{}第{}段AAC编码失败：{}",
                        source_label(segment.source),
                        segment.index,
                        error
                    ));
                    break;
                }
                let retained = match segment.source {
                    AudioSource::Desktop => &mut desktop,
                    AudioSource::Microphone => &mut microphone,
                };
                retained.push_back(path);
                while retained.len() > max_segments {
                    if let Some(expired) = retained.pop_front() {
                        let _ = fs::remove_file(expired);
                    }
                }
            }
        })
        .expect("failed to create AAC encoder thread")
}

fn encode_pcm_segment(path: &Path, segment: &PcmSegment) -> Result<(), String> {
    let video = VideoSettingsBuilder::new(1, 1).disabled(true);
    let audio = AudioSettingsBuilder::new()
        .sample_rate(SAMPLE_RATE)
        .channel_count(CHANNELS)
        .bit_per_sample(BITS_PER_SAMPLE)
        .bitrate(192_000);
    let mut encoder = VideoEncoder::new(
        video,
        audio,
        ContainerSettingsBuilder::new().hardware_acceleration(false),
        path,
    )
    .map_err(|error| error.to_string())?;
    for chunk in segment.bytes.chunks(48_000 * FRAME_BYTES) {
        encoder
            .send_audio_buffer(chunk, 0)
            .map_err(|error| error.to_string())?;
    }
    encoder.finish().map_err(|error| error.to_string())
}

fn append_audio_manifest(manifest: &Path, path: &Path, segment: &PcmSegment) -> Result<(), String> {
    let size = fs::metadata(path).map_err(|error| error.to_string())?.len();
    let mut output = OpenOptions::new()
        .create(true)
        .append(true)
        .open(manifest)
        .map_err(|error| error.to_string())?;
    writeln!(
        output,
        "{{\"schema\":1,\"source\":\"{}\",\"index\":{},\"file\":\"{}\",\"start_qpc\":{},\"end_qpc\":{},\"frames\":{},\"bytes\":{},\"peak_percent\":{}}}",
        segment.source.name(),
        segment.index,
        path.file_name().and_then(|name| name.to_str()).unwrap_or_default(),
        segment.start_qpc,
        segment.end_qpc,
        segment.bytes.len() / FRAME_BYTES,
        size,
        segment.peak_percent,
    )
    .map_err(|error| error.to_string())?;
    output.flush().map_err(|error| error.to_string())
}

fn spawn_level_writer(
    shared: Arc<SharedState>,
    path: PathBuf,
    microphone_enabled: bool,
) -> JoinHandle<()> {
    thread::Builder::new()
        .name("audio-level-writer".to_owned())
        .spawn(move || {
            while !shared.stop.load(Ordering::Acquire) {
                let desktop = shared.desktop_peak.swap(0, Ordering::Relaxed).min(100);
                let microphone = shared.microphone_peak.swap(0, Ordering::Relaxed).min(100);
                let desktop_discontinuities =
                    shared.desktop_discontinuities.load(Ordering::Relaxed);
                let microphone_discontinuities =
                    shared.microphone_discontinuities.load(Ordering::Relaxed);
                let body = format!(
                    concat!(
                        "{{\"desktop\":{},\"microphone\":{},\"microphone_enabled\":{},",
                        "\"desktop_discontinuities\":{},\"microphone_discontinuities\":{}}}\n"
                    ),
                    desktop,
                    microphone,
                    microphone_enabled,
                    desktop_discontinuities,
                    microphone_discontinuities,
                );
                let _ = fs::write(&path, body);
                thread::sleep(Duration::from_millis(100));
            }
            let _ = fs::write(
                &path,
                format!(concat!(
                    "{{\"desktop\":0,\"microphone\":0,\"microphone_enabled\":{},",
                    "\"desktop_discontinuities\":{},\"microphone_discontinuities\":{}}}\n"
                ), microphone_enabled,
                    shared.desktop_discontinuities.load(Ordering::Relaxed),
                    shared.microphone_discontinuities.load(Ordering::Relaxed)),
            );
        })
        .expect("failed to create audio level thread")
}

fn apply_gain(bytes: &mut [u8], gain_percent: u32) {
    if gain_percent == 100 {
        return;
    }
    for sample in bytes.chunks_exact_mut(2) {
        let value = i16::from_le_bytes([sample[0], sample[1]]) as i32;
        let adjusted = (value * gain_percent as i32 / 100).clamp(i16::MIN as i32, i16::MAX as i32);
        sample.copy_from_slice(&(adjusted as i16).to_le_bytes());
    }
}

fn peak_percent(bytes: &[u8]) -> u32 {
    let peak = bytes
        .chunks_exact(2)
        .map(|sample| i16::from_le_bytes([sample[0], sample[1]]).unsigned_abs() as u32)
        .max()
        .unwrap_or(0);
    (peak.saturating_mul(100) / 32_768).min(100)
}

fn qpc_to_frames(ticks: i64) -> usize {
    if ticks <= 0 {
        return 0;
    }
    ((ticks as i128 * SAMPLE_RATE as i128 + QPC_TICKS_PER_SECOND as i128 / 2)
        / QPC_TICKS_PER_SECOND as i128) as usize
}

fn source_label(source: AudioSource) -> &'static str {
    match source {
        AudioSource::Desktop => "桌面声音",
        AudioSource::Microphone => "麦克风",
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn gain_and_peak_are_bounded() {
        let mut bytes = Vec::new();
        bytes.extend_from_slice(&10_000_i16.to_le_bytes());
        bytes.extend_from_slice(&(-20_000_i16).to_le_bytes());
        apply_gain(&mut bytes, 200);
        assert_eq!(i16::from_le_bytes([bytes[0], bytes[1]]), 20_000);
        assert_eq!(i16::from_le_bytes([bytes[2], bytes[3]]), i16::MIN);
        assert_eq!(peak_percent(&bytes), 100);
    }

    #[test]
    fn qpc_to_frames_uses_48khz_clock() {
        assert_eq!(qpc_to_frames(QPC_TICKS_PER_SECOND), 48_000);
        assert_eq!(qpc_to_frames(QPC_TICKS_PER_SECOND / 100), 480);
    }

    #[test]
    fn pcm_collector_recovers_short_gaps_and_rejects_large_timestamp_errors() {
        let shared = Arc::new(SharedState {
            segment_index: AtomicU64::new(0),
            segment_start_qpc: AtomicI64::new(0),
            stop_qpc: AtomicI64::new(0),
            stop: AtomicBool::new(false),
            desktop_peak: AtomicU32::new(0),
            microphone_peak: AtomicU32::new(0),
            desktop_discontinuities: AtomicU32::new(0),
            microphone_discontinuities: AtomicU32::new(0),
        });
        let (sender, _receiver) = mpsc::sync_channel(1);
        let mut collector = PcmCollector::new(AudioSource::Desktop, 100, sender, shared);
        collector.start_qpc = 1_000_000;
        let frame = [1_u8; FRAME_BYTES];

        collector.append_at(collector.start_qpc, &frame).unwrap();
        collector
            .append_at(collector.start_qpc + QPC_TICKS_PER_SECOND, &frame)
            .unwrap();
        assert_eq!(collector.bytes.len() / FRAME_BYTES, SAMPLE_RATE as usize + 1);
        collector
            .append_at(collector.start_qpc + 2 * QPC_TICKS_PER_SECOND, &frame)
            .unwrap();
        collector
            .append_at(collector.start_qpc + 3 * QPC_TICKS_PER_SECOND, &frame)
            .unwrap();

        let too_far_forward = collector.start_qpc + 6 * QPC_TICKS_PER_SECOND;
        assert!(collector.append_at(too_far_forward, &frame).is_err());
        let too_far_back = collector.start_qpc;
        assert!(collector.append_at(too_far_back, &frame).is_err());
    }

    #[test]
    fn level_only_collector_reports_peak_without_retaining_pcm() {
        let shared = Arc::new(SharedState {
            segment_index: AtomicU64::new(0),
            segment_start_qpc: AtomicI64::new(0),
            stop_qpc: AtomicI64::new(0),
            stop: AtomicBool::new(false),
            desktop_peak: AtomicU32::new(0),
            microphone_peak: AtomicU32::new(0),
            desktop_discontinuities: AtomicU32::new(0),
            microphone_discontinuities: AtomicU32::new(0),
        });
        let (sender, _receiver) = mpsc::sync_channel(1);
        let mut collector = PcmCollector::new(AudioSource::Desktop, 100, sender, shared.clone());
        let mut bytes = Vec::new();
        bytes.extend_from_slice(&20_000_i16.to_le_bytes());
        bytes.extend_from_slice(&(-20_000_i16).to_le_bytes());

        collector.push_packet(123, bytes).unwrap();

        assert!(shared.desktop_peak.load(Ordering::Relaxed) > 0);
        assert!(collector.bytes.is_empty());
    }
}
