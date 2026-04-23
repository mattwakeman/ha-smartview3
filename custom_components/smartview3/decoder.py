"""Smartview 3 protocol decoding helpers."""

from __future__ import annotations

from enum import IntEnum
from typing import Any


class Cluster(IntEnum):
    """Cluster IDs in Smartview payloads."""

    TIME = 0x000A
    METERING = 0x0702
    PREPAYMENT = 0x0705


class MeteringParameter(IntEnum):
    """Metering cluster parameters."""

    CURRENT_SUMMATION_DELIVERED = 0x0000
    CURRENT_SUMMATION_RECEIVED = 0x0001
    SUPPLY_STATUS = 0x0014
    STATUS = 0x0200
    AMBIENT_CONSUMPTION_INDICATOR = 0x0207
    SITE_ID = 0x0307
    CUSTOMER_ID_NUMBER = 0x0311
    INSTANTANEOUS_DEMAND = 0x0400
    CURRENT_DAY_CONSUMPTION_DELIVERED = 0x0401
    PREVIOUS_DAY_CONSUMPTION_DELIVERED = 0x0403
    CURRENT_WEEK_CONSUMPTION_DELIVERED = 0x0430
    PREVIOUS_WEEK_CONSUMPTION_DELIVERED = 0x0432
    CURRENT_MONTH_CONSUMPTION_DELIVERED = 0x0440
    PREVIOUS_MONTH_CONSUMPTION_DELIVERED = 0x0442
    BILL_TO_DATE_DELIVERED = 0x0A00
    BILL_DELIVERED_TRAILING_DIGIT = 0x0A04
    CURRENT_DAY_ALTERNATIVE_CONSUMPTION_DELIVERED = 0x0C01
    PREVIOUS_DAY_ALTERNATIVE_CONSUMPTION_DELIVERED = 0x0C03
    CURRENT_WEEK_ALTERNATIVE_CONSUMPTION_DELIVERED = 0x0C30
    PREVIOUS_WEEK_ALTERNATIVE_CONSUMPTION_DELIVERED = 0x0C32
    CURRENT_MONTH_ALTERNATIVE_CONSUMPTION_DELIVERED = 0x0C40
    PREVIOUS_MONTH_ALTERNATIVE_CONSUMPTION_DELIVERED = 0x0C42


class PrepaymentParameter(IntEnum):
    """Prepayment cluster parameters."""

    PAYMENT_CONTROL_CONFIGURATION = 0x0000
    CURRENT_DAY_COST_CONSUMPTION_DELIVERED = 0x051C
    PREVIOUS_DAY_COST_CONSUMPTION_DELIVERED = 0x051E
    CURRENT_WEEK_COST_CONSUMPTION_DELIVERED = 0x0530
    PREVIOUS_WEEK_COST_CONSUMPTION_DELIVERED = 0x0532
    CURRENT_MONTH_COST_CONSUMPTION_DELIVERED = 0x0540
    PREVIOUS_MONTH_COST_CONSUMPTION_DELIVERED = 0x0542


class Encoding(IntEnum):
    """Attribute encoding values."""

    BITMAP_8 = 0x18
    BITMAP_16 = 0x19
    BITMAP_32 = 0x1B
    INT_24 = 0x2A
    UINT_8 = 0x20
    UINT_24 = 0x22
    UINT_32 = 0x23
    UINT_48 = 0x25
    ENUM_8 = 0x30
    STRING = 0x41
    UTC = 0xE2


def decode_data_block(data: bytes) -> bytes:
    """Strip framing and substitution markers from a received packet."""
    output_data = bytearray()
    marker = 0
    while marker < len(data):
        byte = data[marker]
        if byte == 0xF1:
            marker += 1
            continue
        if byte == 0xF2:
            marker += 1
            continue
        if byte == 0xF3:
            if marker + 1 >= len(data):
                raise ValueError("Malformed substitution marker in frame")
            output_data.append(0xF0 + data[marker + 1])
            marker += 2
            continue
        output_data.append(byte)
        marker += 1
    return bytes(output_data)


def value_decoder(data: bytes) -> dict[str, Any]:
    """Decode a Smartview block into meter, cluster, and attributes."""
    if len(data) < 7:
        raise ValueError("Decoded frame too short")

    meter_id = data[1:3]
    cluster = int.from_bytes(data[4:6], "little")
    parameters: dict[int, dict[str, Any]] = {}

    marker = 6
    while marker < len(data):
        if marker + 4 > len(data):
            break
        attribute = int.from_bytes(data[marker : marker + 2], "little")
        status = data[marker + 2]
        if status != 0x00:
            break

        encoding = data[marker + 3]
        marker += 4

        if encoding == Encoding.BITMAP_8:
            value = data[marker]
            marker += 1
        elif encoding == Encoding.BITMAP_16:
            value = int.from_bytes(data[marker : marker + 2], "little")
            marker += 2
        elif encoding == Encoding.BITMAP_32:
            value = int.from_bytes(data[marker : marker + 4], "little")
            marker += 4
        elif encoding == Encoding.INT_24:
            value = int.from_bytes(data[marker : marker + 3], "little", signed=True)
            marker += 3
        elif encoding == Encoding.UINT_8:
            value = int.from_bytes(data[marker : marker + 1], "little", signed=False)
            marker += 1
        elif encoding == Encoding.UINT_24:
            value = int.from_bytes(data[marker : marker + 3], "little", signed=False)
            marker += 3
        elif encoding == Encoding.UINT_32:
            value = int.from_bytes(data[marker : marker + 4], "little", signed=False)
            marker += 4
        elif encoding == Encoding.UINT_48:
            value = int.from_bytes(data[marker : marker + 6], "little", signed=False)
            marker += 6
        elif encoding == Encoding.ENUM_8:
            value = data[marker]
            marker += 1
        elif encoding == Encoding.STRING:
            length = data[marker]
            value = data[marker + 1 : marker + 1 + length].decode("ascii", errors="ignore")
            marker += 1 + length
        elif encoding == Encoding.UTC:
            value = int.from_bytes(data[marker : marker + 4], "little", signed=False)
            marker += 4
        else:
            raise ValueError(
                f"Unrecognised encoding 0x{encoding:02X} for attribute 0x{attribute:04X}"
            )

        parameters[attribute] = {"type": encoding, "value": value}

    return {"meter": meter_id, "cluster": cluster, "parameters": parameters}
