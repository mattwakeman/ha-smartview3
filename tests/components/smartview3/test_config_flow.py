"""Tests for Smartview config and options flows."""

from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow

from custom_components.smartview3.const import (
    CONF_GAS_KWH_PER_M3,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_DEVICE,
    DOMAIN,
)


async def test_user_flow_selects_discovered_device(hass) -> None:
    with patch(
        "custom_components.smartview3.config_flow.list_serial_devices",
        return_value=["/dev/ttyUSB0"],
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"discovered_device": "/dev/ttyUSB0", CONF_SERIAL_DEVICE: ""},
        )
        assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result2["data"][CONF_SERIAL_DEVICE] == "/dev/ttyUSB0"


async def test_user_flow_accepts_manual_device(hass) -> None:
    with patch(
        "custom_components.smartview3.config_flow.list_serial_devices",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"discovered_device": "manual", CONF_SERIAL_DEVICE: "/dev/ttyUSB9"},
        )
        assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result2["data"][CONF_SERIAL_DEVICE] == "/dev/ttyUSB9"
        assert CONF_SCAN_INTERVAL in result2["options"]
        assert CONF_GAS_KWH_PER_M3 in result2["options"]
