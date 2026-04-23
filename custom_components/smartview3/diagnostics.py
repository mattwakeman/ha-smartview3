"""Diagnostics support for Smartview 3."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import Smartview3Coordinator


def _redact_serial_path(path: str) -> str:
    if "/dev/serial/by-id/" in path:
        return "/dev/serial/by-id/<redacted>"
    if path.startswith("/dev/ttyUSB"):
        return "/dev/ttyUSB<redacted>"
    return "<redacted>"


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: Smartview3Coordinator = hass.data[DOMAIN][entry.entry_id]
    data = deepcopy(coordinator.data)

    options = dict(entry.options)
    serial_path = options.get("serial_device", entry.data.get("serial_device", ""))
    if serial_path:
        options["serial_device"] = _redact_serial_path(serial_path)

    return {
        "entry_data": {"serial_device": _redact_serial_path(entry.data.get("serial_device", ""))},
        "entry_options": options,
        "meter_map": dict(coordinator.meter_map),
        "last_data_keys": {
            "roles": list(data.get("roles", {}).keys()),
            "meters": list(data.get("meters", {}).keys()),
        },
    }
