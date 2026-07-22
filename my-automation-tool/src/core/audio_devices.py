"""只读枚举 Windows 可用麦克风；QtMultimedia 延迟导入以免拖慢主模块导入。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MicrophoneDevice:
    identifier: str
    name: str
    is_default: bool = False


def list_microphone_devices() -> tuple[MicrophoneDevice, ...]:
    """返回系统当前可用输入设备，默认设备排在最前。"""
    from PySide6.QtMultimedia import QMediaDevices

    default_identifier = bytes(QMediaDevices.defaultAudioInput().id()).hex()
    devices: list[MicrophoneDevice] = []
    seen: set[str] = set()
    for device in QMediaDevices.audioInputs():
        identifier = bytes(device.id()).hex()
        if not identifier or identifier in seen:
            continue
        seen.add(identifier)
        name = device.description().strip() or "未命名麦克风"
        devices.append(
            MicrophoneDevice(identifier, name, identifier == default_identifier)
        )
    devices.sort(key=lambda item: (not item.is_default, item.name.casefold()))
    return tuple(devices)
