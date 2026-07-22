# Native Replay Third-Party Notices

## windows-capture 2.0.0

- Source: https://github.com/NiiightmareXD/windows-capture
- License: MIT
- Vendored path: `third_party/windows-capture/`
- Local changes: expose the Media Foundation hardware-acceleration switch for explicit GPU/CPU choice; permit audio-only MediaStreamSource profiles so desktop and microphone PCM can be encoded as separate AAC files.

## wasapi 0.23.0

- Source: https://github.com/HEnquist/wasapi-rs
- License: MIT
- Usage: event-driven WASAPI loopback for desktop audio and capture-endpoint recording for the selected microphone.

## mp4 0.14.0

- Source: https://github.com/alfg/mp4-rust
- License: MIT
- Usage: sample-level remux of H.264 video plus one or two independent AAC tracks into the saved `raw.mp4`.

## Architectural references only

- OBS Studio 32.0.2, GNU GPL v2: replay-buffer packet ring, keyframe-aware eviction and asynchronous mux architecture were studied. No OBS source is copied and OBS is not a runtime dependency.
