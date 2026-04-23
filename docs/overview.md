# Smartview 3 Integration Technical Overview

## Purpose

This custom integration connects a UK Smartview 3 IHD/CAD over USB serial and exposes electric, gas, cost, and status data as Home Assistant entities.

The implementation is designed around:

- dynamic meter discovery (no hardcoded meter IDs),
- Home Assistant Energy Dashboard compatible entities,
- runtime safety (serial I/O off the event loop),
- and testability with mocked devices.

## High-Level Architecture

At runtime, the flow is:

1. Home Assistant loads the config entry.
2. A serial client is created and opened.
3. A data coordinator periodically reads serial bytes.
4. Framed packets are decoded into attributes.
5. Meter roles (`electric` / `gas`) are inferred dynamically.
6. Sensor and binary sensor entities read coordinator snapshots.

Core files:

- `custom_components/smartview3/__init__.py`
- `custom_components/smartview3/coordinator.py`
- `custom_components/smartview3/serial_client.py`
- `custom_components/smartview3/decoder.py`
- `custom_components/smartview3/sensor.py`
- `custom_components/smartview3/binary_sensor.py`

## Entry Setup and Teardown

`__init__.py` wires integration lifecycle:

- `async_setup_entry`:
  - builds `Smartview3SerialClient`,
  - builds `Smartview3Coordinator`,
  - performs first refresh,
  - forwards platforms listed in `const.py` (`sensor`, `binary_sensor`).
- `async_unload_entry`:
  - closes serial resources via coordinator shutdown,
  - unloads platforms,
  - removes coordinator from `hass.data`.

## Configuration Flow

`config_flow.py` provides two UX surfaces:

- initial setup (`async_step_user`)
- options (`Smartview3OptionsFlow`)

Device selection supports:

- discovered `/dev/serial/by-id/*`,
- discovered `/dev/ttyUSB*`,
- manual path entry.

Key options:

- `scan_interval` (seconds),
- `gas_kwh_per_m3` conversion factor,
- `enable_diagnostic_sensors`.

All user-facing setup/options text and entity names are in:

- `custom_components/smartview3/translations/en.json`

## Serial Transport and Frame Handling

`serial_client.py` is responsible for transport and framing:

- opens `pyserial` with configured path and default serial settings,
- reads chunks into an internal buffer,
- extracts packets using start/end markers:
  - `0xF1` start-of-frame,
  - `0xF2` end-of-frame.

The framer tolerates:

- partial frames across reads,
- noise bytes before the start marker.

Each extracted frame is decoded into `SmartviewSample` with:

- `meter` (raw meter ID bytes),
- `cluster`,
- `parameters`,
- receive timestamp.

## Protocol Decoding

`decoder.py` contains protocol constants and parsers.

### Clusters

- `0x000A` time
- `0x0702` metering
- `0x0705` prepayment

### Metering/prepayment attributes

Important attributes include:

- electric instantaneous demand (`0x0400`)
- delivered/received summations (`0x0000`, `0x0001`)
- status bitmap (`0x0200`)
- period consumption fields
- day/week/month cost fields

### Encoding handling

Supported encodings include bitmap, integer, enum, string, and UTC variants.

`decode_data_block` removes frame markers and applies substitution logic (`0xF3`).

`value_decoder` parses attribute tuples into:

```python
{
  "meter": b"...",
  "cluster": <int>,
  "parameters": {
    <attribute_id>: {"type": <encoding>, "value": <decoded_value>}
  }
}
```

## Coordinator Data Model and Role Mapping

`coordinator.py` uses `DataUpdateCoordinator`.

Important behavior:

- serial reads are executed in the executor (`async_add_executor_job`),
- periodic updates use configured `scan_interval`,
- update failures raise `UpdateFailed` for HA health semantics.

Coordinator state shape:

- `meters`: nested map keyed by meter hex -> cluster -> attribute,
- `roles`: role-to-meter map (`electric`, `gas`),
- `last_packet_ts`: latest sample timestamp.

### Dynamic meter-role inference (no hardcoded IDs)

Role assignment heuristics:

- meter with `INSTANTANEOUS_DEMAND` -> electric,
- meter with `CURRENT_DAY_ALTERNATIVE_CONSUMPTION_DELIVERED` -> gas,
- meter with `CURRENT_SUMMATION_RECEIVED` -> electric,
- fallback role assignment if only one role remains unassigned.

## Entity Model

### Sensor entities

`entity_descriptions.py` defines a registry of mapped sensors with:

- translation key,
- target role (`electric` / `gas`),
- cluster/attribute binding,
- unit/device/state classes,
- value transform function.

This includes:

- power,
- import/export totals,
- daily/weekly/monthly usage,
- gas volume and converted gas energy,
- bill-to-date,
- electric/gas day/week/month costs.

### Combined cost sensors

`sensor.py` adds computed combined sensors that sum electric + gas values:

- `total_current_day_cost`
- `total_current_week_cost`
- `total_current_month_cost`

These read each role's prepayment attributes and convert using `/100000`, matching per-fuel cost scaling.

### Battery indicator

`binary_sensor.py` provides `low_battery` using:

- metering status bitmap attribute `0x0200`,
- bitmask `0x01`.

If bit 0 is set, `binary_sensor` is `on`.

### Device registry identity

All entities attach to one HA device:

- name: `Smartview 3`
- manufacturer: `Chameleon Technology`
- model: `Smartview 3`

## Energy Dashboard Compatibility

Energy-facing entities are exposed with required metadata:

- electric import/export totals:
  - `device_class: energy`
  - `state_class: total_increasing`
  - `unit: kWh`
- gas energy total:
  - `device_class: energy`
  - `state_class: total_increasing`
  - `unit: kWh`
- power:
  - `device_class: power`
  - `state_class: measurement`
  - `unit: W`

Gas conversion from meter volume to energy uses configurable `gas_kwh_per_m3`.

## Diagnostics

`diagnostics.py` returns a safe support payload with:

- redacted serial path,
- entry options,
- current meter-role map,
- last data-key summary.

Raw USB paths are masked to avoid leaking host-specific identifiers.

## Localization and User-Facing Strings

The integration uses translation keys for:

- config flow text,
- options flow text,
- sensor names,
- binary sensor names,
- setup errors.

Translation file:

- `custom_components/smartview3/translations/en.json`

## Testing Strategy

Tests live under:

- `tests/components/smartview3/`

Coverage includes:

- packet decode behavior,
- serial framing with fragmented/noisy input,
- config flow and options flow behavior,
- coordinator role discovery and reconnect scenarios,
- entity metadata expectations,
- battery bitmask behavior,
- combined day/week/month cost calculations.

Mock devices and packet builders are in:

- `tests/components/smartview3/fixtures.py`

## Known Design Choices

- Current meter-role mapping is inferred at runtime and kept in-memory for the active process.
- Cost entities are exposed as raw meter-reported cost values (scaled), plus combined totals.
- Integration currently prioritizes local serial transport over external APIs/services.

