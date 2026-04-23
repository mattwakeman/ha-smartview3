"""Shared test fixtures and packet builders for Smartview 3."""

from __future__ import annotations

from dataclasses import dataclass


def _encode_uint24(value: int) -> bytes:
    return value.to_bytes(3, "little", signed=False)


def build_metering_frame(
    meter_id: bytes,
    attribute: int,
    value: int,
    encoding: int = 0x22,
    cluster: int = 0x0702,
) -> bytes:
    """Build a minimal framed Smartview packet with one attribute."""
    payload = bytearray()
    payload.extend(b"\x00")
    payload.extend(meter_id)
    payload.extend(b"\x00")
    payload.extend(cluster.to_bytes(2, "little"))
    payload.extend(attribute.to_bytes(2, "little"))
    payload.extend(b"\x00")
    payload.extend(bytes([encoding]))
    if encoding == 0x22:
        payload.extend(_encode_uint24(value))
    elif encoding == 0x2A:
        payload.extend(value.to_bytes(3, "little", signed=True))
    else:
        raise ValueError("Unsupported test encoding")
    return b"\xF1" + bytes(payload) + b"\xF2"


@dataclass
class MockSerialDevice:
    """Mock serial device supporting read() and close()."""

    chunks: list[bytes]
    is_open: bool = True

    def read(self, _: int) -> bytes:
        if not self.chunks:
            return b""
        return self.chunks.pop(0)

    def close(self) -> None:
        self.is_open = False
