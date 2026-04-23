"""Serial client for Smartview 3."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from glob import glob
import logging
import time
from typing import Any

import serial
from serial import SerialException

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_DEVICE,
    DEFAULT_BAUDRATE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
)
from .decoder import decode_data_block, value_decoder

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SmartviewSample:
    """One decoded sample from the serial stream."""

    meter: bytes
    cluster: int
    parameters: dict[int, dict[str, Any]]
    received_ts: float


class Smartview3SerialClient:
    """Reads Smartview packets from a USB serial device."""

    def __init__(self, data: dict[str, Any], options: dict[str, Any]) -> None:
        self._device = options.get(CONF_SERIAL_DEVICE, data.get(CONF_SERIAL_DEVICE))
        self._scan_interval = options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self._serial: serial.Serial | None = None
        self._read_buf = bytearray()

    @property
    def device(self) -> str:
        """Return configured serial device path."""
        return self._device

    @property
    def scan_interval(self) -> int:
        """Return polling interval in seconds."""
        return int(self._scan_interval)

    def open(self) -> None:
        """Open serial port in executor-friendly way."""
        self.close()
        self._serial = serial.Serial(
            self._device,
            baudrate=DEFAULT_BAUDRATE,
            timeout=DEFAULT_TIMEOUT,
        )
        _LOGGER.debug("Opened Smartview serial device %s", self._device)

    def close(self) -> None:
        """Close serial connection."""
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None
        self._read_buf.clear()

    def read_samples(self, max_packets: int = 8) -> list[SmartviewSample]:
        """Read and decode up to max_packets."""
        if not self._serial or not self._serial.is_open:
            raise SerialException("Serial device is not open")

        raw = self._serial.read(4096)
        if raw:
            self._read_buf.extend(raw)

        packets = self._extract_packets(max_packets)
        samples: list[SmartviewSample] = []
        for packet in packets:
            decoded = value_decoder(decode_data_block(packet))
            samples.append(
                SmartviewSample(
                    meter=decoded["meter"],
                    cluster=decoded["cluster"],
                    parameters=decoded["parameters"],
                    received_ts=time.time(),
                )
            )
        return samples

    def _extract_packets(self, max_packets: int) -> list[bytes]:
        packets: list[bytes] = []
        while len(packets) < max_packets:
            try:
                start = self._read_buf.index(0xF1)
            except ValueError:
                self._read_buf.clear()
                break

            try:
                end = self._read_buf.index(0xF2, start + 1)
            except ValueError:
                if start > 0:
                    del self._read_buf[:start]
                break

            packet = bytes(self._read_buf[start : end + 1])
            del self._read_buf[: end + 1]
            packets.append(packet)
        return packets


def list_serial_devices() -> list[str]:
    """List preferred serial devices for config flow selection."""
    candidates: list[str] = []
    candidates.extend(sorted(glob("/dev/serial/by-id/*")))
    candidates.extend(sorted(glob("/dev/ttyUSB*")))
    return candidates
