import unittest
from unittest.mock import patch

from src.core.audio_devices import list_microphone_devices


class _FakeDevice:
    def __init__(self, identifier: bytes, name: str):
        self._identifier = identifier
        self._name = name

    def id(self):
        return self._identifier

    def description(self):
        return self._name


class _FakeMediaDevices:
    @staticmethod
    def defaultAudioInput():
        return _FakeDevice(b"default", "USB 麦克风")

    @staticmethod
    def audioInputs():
        return [
            _FakeDevice(b"other", "立体声混音"),
            _FakeDevice(b"default", "USB 麦克风"),
            _FakeDevice(b"default", "重复设备"),
        ]


class AudioDeviceTests(unittest.TestCase):
    def test_default_microphone_is_first_and_duplicate_ids_are_removed(self):
        with patch("PySide6.QtMultimedia.QMediaDevices", _FakeMediaDevices):
            devices = list_microphone_devices()
        self.assertEqual([device.name for device in devices], ["USB 麦克风", "立体声混音"])
        self.assertTrue(devices[0].is_default)
        self.assertEqual(devices[0].identifier, b"default".hex())


if __name__ == "__main__":
    unittest.main()
