"""Constants for the Smartview 3 integration."""

from __future__ import annotations

DOMAIN = "smartview3"
PLATFORMS = ["sensor", "binary_sensor"]

CONF_SERIAL_DEVICE = "serial_device"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_GAS_KWH_PER_M3 = "gas_kwh_per_m3"
CONF_ENABLE_DIAGNOSTIC_SENSORS = "enable_diagnostic_sensors"

DEFAULT_SCAN_INTERVAL = 10
DEFAULT_GAS_KWH_PER_M3 = 11.2
DEFAULT_ENABLE_DIAGNOSTIC_SENSORS = False

DEFAULT_BAUDRATE = 115200
DEFAULT_TIMEOUT = 2.0

METER_ROLE_ELECTRIC = "electric"
METER_ROLE_GAS = "gas"

ATTR_METER_MAP = "meter_map"
ATTR_LAST_PACKET_TS = "last_packet_ts"
