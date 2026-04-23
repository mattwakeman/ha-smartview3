"""Tests for Smartview decoder helpers."""

from custom_components.smartview3.decoder import decode_data_block, value_decoder

from .fixtures import build_metering_frame


def test_decode_data_block_removes_markers() -> None:
    framed = b"\xF1\x00\x99\x57\x00\x02\x07\x00\x04\x00\x22\x2C\x01\x00\xF2"
    decoded = decode_data_block(framed)
    assert decoded[0] == 0x00
    assert decoded[-1] == 0x00
    assert 0xF1 not in decoded
    assert 0xF2 not in decoded


def test_value_decoder_decodes_uint24_attribute() -> None:
    frame = build_metering_frame(meter_id=b"\x99\x57", attribute=0x0400, value=300)
    decoded = value_decoder(decode_data_block(frame))
    assert decoded["meter"] == b"\x99\x57"
    assert decoded["cluster"] == 0x0702
    assert decoded["parameters"][0x0400]["value"] == 300
