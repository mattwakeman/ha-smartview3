"""Tests for Smartview serial client."""

from custom_components.smartview3.serial_client import Smartview3SerialClient

from .fixtures import MockSerialDevice, build_metering_frame


def test_serial_client_extracts_fragmented_packets() -> None:
    frame = build_metering_frame(b"\x01\x02", 0x0400, 450)
    chunks = [frame[:5], frame[5:10], frame[10:]]
    client = Smartview3SerialClient({"serial_device": "/dev/ttyUSB0"}, {})
    client._serial = MockSerialDevice(chunks=chunks)  # noqa: SLF001

    samples = client.read_samples(max_packets=2)

    assert len(samples) == 1
    assert samples[0].meter == b"\x01\x02"
    assert samples[0].parameters[0x0400]["value"] == 450


def test_serial_client_skips_noise_before_start() -> None:
    frame = build_metering_frame(b"\x0A\x0B", 0x0000, 1000)
    client = Smartview3SerialClient({"serial_device": "/dev/ttyUSB1"}, {})
    client._serial = MockSerialDevice(chunks=[b"\xAA\xBB" + frame])  # noqa: SLF001

    samples = client.read_samples(max_packets=2)
    assert len(samples) == 1
    assert samples[0].meter == b"\x0A\x0B"
