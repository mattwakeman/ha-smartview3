"""Config flow for Smartview 3."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import NumberSelector, NumberSelectorConfig, SelectSelector, SelectSelectorConfig

from .const import (
    CONF_ENABLE_DIAGNOSTIC_SENSORS,
    CONF_GAS_KWH_PER_M3,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_DEVICE,
    DEFAULT_ENABLE_DIAGNOSTIC_SENSORS,
    DEFAULT_GAS_KWH_PER_M3,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .serial_client import list_serial_devices


def _select_schema(discovered: list[str], default_device: str | None = None) -> vol.Schema:
    options = discovered + ["manual"]
    return vol.Schema(
        {
            vol.Required(
                "discovered_device",
                default=(default_device if default_device in options else discovered[0] if discovered else "manual"),
            ): SelectSelector(SelectSelectorConfig(options=options, mode="dropdown")),
            vol.Optional(CONF_SERIAL_DEVICE, default=default_device or ""): str,
        }
    )


class Smartview3ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smartview 3."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            selected = user_input["discovered_device"]
            manual = user_input.get(CONF_SERIAL_DEVICE, "").strip()
            serial_path = manual if selected == "manual" else selected

            if not serial_path:
                errors["base"] = "serial_device_required"
            else:
                await self.async_set_unique_id(serial_path)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Smartview 3 ({serial_path})",
                    data={CONF_SERIAL_DEVICE: serial_path},
                    options={
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                        CONF_GAS_KWH_PER_M3: DEFAULT_GAS_KWH_PER_M3,
                        CONF_ENABLE_DIAGNOSTIC_SENSORS: DEFAULT_ENABLE_DIAGNOSTIC_SENSORS,
                    },
                )

        discovered = await self.hass.async_add_executor_job(list_serial_devices)
        return self.async_show_form(
            step_id="user",
            data_schema=_select_schema(discovered),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return Smartview3OptionsFlow(config_entry)


class Smartview3OptionsFlow(config_entries.OptionsFlow):
    """Options flow for Smartview 3."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            selected = user_input["discovered_device"]
            manual = user_input.get(CONF_SERIAL_DEVICE, "").strip()
            serial_path = manual if selected == "manual" else selected
            if not serial_path:
                errors["base"] = "serial_device_required"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_SERIAL_DEVICE: serial_path,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        CONF_GAS_KWH_PER_M3: user_input[CONF_GAS_KWH_PER_M3],
                        CONF_ENABLE_DIAGNOSTIC_SENSORS: user_input[CONF_ENABLE_DIAGNOSTIC_SENSORS],
                    },
                )

        current_serial = self._entry.options.get(CONF_SERIAL_DEVICE, self._entry.data.get(CONF_SERIAL_DEVICE))
        discovered = await self.hass.async_add_executor_job(list_serial_devices)
        options = discovered + ["manual"]
        data_schema = vol.Schema(
            {
                vol.Required(
                    "discovered_device",
                    default=(
                        current_serial
                        if current_serial in options
                        else (discovered[0] if discovered else "manual")
                    ),
                ): SelectSelector(SelectSelectorConfig(options=options, mode="dropdown")),
                vol.Optional(CONF_SERIAL_DEVICE, default=current_serial if current_serial not in discovered else ""): str,
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self._entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): NumberSelector(NumberSelectorConfig(min=1, max=120, step=1, mode="box")),
                vol.Required(
                    CONF_GAS_KWH_PER_M3,
                    default=self._entry.options.get(CONF_GAS_KWH_PER_M3, DEFAULT_GAS_KWH_PER_M3),
                ): NumberSelector(NumberSelectorConfig(min=1, max=20, step=0.1, mode="box")),
                vol.Required(
                    CONF_ENABLE_DIAGNOSTIC_SENSORS,
                    default=self._entry.options.get(
                        CONF_ENABLE_DIAGNOSTIC_SENSORS,
                        DEFAULT_ENABLE_DIAGNOSTIC_SENSORS,
                    ),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)
