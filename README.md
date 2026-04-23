# Smartview 3 Home Assistant Integration

Home Assistant custom integration for UK Smartview 3 IHD/CAD devices connected via USB-FTDI serial adapter.

https://www.in-home-displays.co.uk/wp-content/uploads/2023/08/sv3-brochure.pdf 

## Features

- Direct serial integration with Smartview 3 over `/dev/ttyUSB*` or `/dev/serial/by-id/*`.
- Dynamic meter role detection (no hardcoded meter IDs).
- Full sensor surface for electric, gas, and cost metrics.
- Energy Dashboard compatible sensors for electric import/export and gas energy.

## Installation (HACS)

1. In HACS, add this repository as a custom repository (category: Integration).
2. Install `Smartview 3`.
3. Restart Home Assistant.
4. Add integration from **Settings -> Devices & Services**.

## Hardware

Use a USB-FTDI cable connected to the Smartview 3 UART wiring as documented in the reference project:

- [Tyler-Ward/smart_meter_prometheus_exporter](https://github.com/Tyler-Ward/smart_meter_prometheus_exporter)

## Notes

- Choose `/dev/serial/by-id/*` where available for stable device mapping across reboots.
- A manual path option is available in setup and options flow for edge cases.
