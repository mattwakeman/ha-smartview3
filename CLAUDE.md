# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom integration for UK Smartview 3 IHD/CAD devices connected via USB-FTDI serial adapter. It exposes electricity and gas meter data as Home Assistant entities compatible with the Energy Dashboard.

- Domain: `smartview3`
- Minimum HA version: 2026.4.0
- External dependency: `pyserial>=3.5`

## Running Tests

Tests follow Home Assistant integration conventions — no build step required.

```bash
# Run all integration tests
pytest tests/components/smartview3/

# Run a single test file
pytest tests/components/smartview3/test_decoder.py

# Run a single test
pytest tests/components/smartview3/test_decoder.py::test_function_name
```

## Architecture

Data flows linearly through four layers:

```
Serial Port → SerialClient → Coordinator → Decoder → Entities
```

**`serial_client.py`** — Opens the USB serial port and buffers incoming bytes. Extracts complete packets delimited by `0xF1` (start) / `0xF2` (end) frame markers.

**`decoder.py`** — Defines `Cluster` and `Parameter` enums mapping ZigBee/SMETS cluster/attribute IDs to names. Decodes binary payloads (uint8–48, int24, bitmap, enum, string, UTC) into structured dicts.

**`coordinator.py`** — `DataUpdateCoordinator` subclass that polls SerialClient and builds the canonical data shape. Dynamically infers meter roles (electric vs. gas) by inspecting which attributes are present — no hardcoded meter IDs:
- Electric meter: has `INSTANTANEOUS_DEMAND` (cluster `0x0702`, attr `0x0400`)
- Gas meter: has `CURRENT_DAY_ALTERNATIVE_CONSUMPTION_DELIVERED` (cluster `0x0702`, attr `0x0C01`)

**`entity_descriptions.py` + `sensor.py` + `binary_sensor.py`** — Entity definitions. Each `SmartviewSensorEntityDescription` maps a coordinator data path (`meter_role`, `cluster`, `attribute`) to an HA entity with units, device class, state class, and an optional value transform.

**`config_flow.py`** — Two-stage UI: initial setup (serial port device selection) and options flow (scan interval, gas calorific value for kWh conversion, diagnostic sensor visibility).

## Coordinator Data Shape

```python
{
  "meters": {
    "<meter_hex_id>": {
      "<cluster_int>": {
        "<attribute_int>": {"type": <encoding_byte>, "value": <decoded_value>}
      }
    }
  },
  "roles": {
    "electric": "<meter_hex_id>",  # or None
    "gas": "<meter_hex_id>"        # or None
  },
  "last_packet_ts": <float>
}
```

## Test Fixtures

`tests/components/smartview3/fixtures.py` provides:
- `MockSerial` — simulates a serial port with configurable chunked read behaviour
- Packet builder helpers that construct valid `0xF1...0xF2` framed payloads for any cluster/attribute combination

Use these when writing new tests rather than building raw bytes manually.

## Key Constants (`const.py`)

- `DEFAULT_SCAN_INTERVAL = 10` (seconds)
- `DEFAULT_BAUDRATE = 115200`
- `DEFAULT_SERIAL_TIMEOUT = 2.0`
- Config entry keys: `CONF_DEVICE`, `CONF_SCAN_INTERVAL`, `CONF_GAS_CALORIFIC_VALUE`
