"""Coordinator for Smartview 3 data updates."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from serial import SerialException

from .const import (
    ATTR_LAST_PACKET_TS,
    ATTR_METER_MAP,
    METER_ROLE_ELECTRIC,
    METER_ROLE_GAS,
)
from .decoder import Cluster, MeteringParameter
from .serial_client import Smartview3SerialClient, SmartviewSample

_LOGGER = logging.getLogger(__name__)

SmartviewData = dict[str, Any]


class Smartview3Coordinator(DataUpdateCoordinator[SmartviewData]):
    """Coordinate Smartview packet reads and decoded data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        serial_client: Smartview3SerialClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="smartview3",
            update_interval=timedelta(seconds=serial_client.scan_interval),
        )
        self.config_entry = entry
        self.serial_client = serial_client
        self.data = {"meters": {}, "roles": {}, ATTR_LAST_PACKET_TS: None}
        self._meter_map: dict[str, str] = dict(entry.options.get(ATTR_METER_MAP, {}))

    async def async_config_entry_first_refresh(self) -> None:
        """Initialize serial and perform first data refresh."""
        await self.hass.async_add_executor_job(self.serial_client.open)
        await super().async_config_entry_first_refresh()

    async def async_shutdown(self) -> None:
        """Release serial resources."""
        await self.hass.async_add_executor_job(self.serial_client.close)

    async def _async_update_data(self) -> SmartviewData:
        """Read latest serial data."""
        try:
            samples: list[SmartviewSample] = await self.hass.async_add_executor_job(
                self.serial_client.read_samples
            )
        except (SerialException, ValueError) as err:
            raise UpdateFailed(f"Serial read failed: {err}") from err

        # Preserve existing data if no new samples
        meter_data: dict[str, dict[int, dict[int, dict[str, Any]]]] = (
            defaultdict(lambda: defaultdict(dict))
            if not self.data
            else defaultdict(lambda: defaultdict(dict), {
                k: {int_ck: {int_ak: dict(v) for int_ak, v in int_av.items()}
                    for int_ck, int_av in v.items()}
                for k, v in self.data["meters"].items()
            })
        )
        for sample in samples:
            meter_key = sample.meter.hex()
            meter_data[meter_key][sample.cluster].update(sample.parameters)
            self._update_meter_role(meter_key, sample)

        roles = {role: meter for meter, role in self._meter_map.items()}
        last_ts = (
            max((s.received_ts for s in samples), default=self.data.get(ATTR_LAST_PACKET_TS))
            if samples
            else self.data.get(ATTR_LAST_PACKET_TS) if self.data else None
        )
        self.data = {"meters": meter_data, "roles": roles, ATTR_LAST_PACKET_TS: last_ts}
        return self.data

    async def async_request_refresh(self) -> None:
        """Refresh on demand using configured scan interval semantics."""
        await super().async_request_refresh()

    def _update_meter_role(self, meter_key: str, sample: SmartviewSample) -> None:
        """Infer electric/gas role from available parameters."""
        if sample.cluster != Cluster.METERING:
            return

        attrs = sample.parameters.keys()
        if MeteringParameter.INSTANTANEOUS_DEMAND in attrs:
            self._meter_map[meter_key] = METER_ROLE_ELECTRIC
        elif MeteringParameter.CURRENT_DAY_ALTERNATIVE_CONSUMPTION_DELIVERED in attrs:
            self._meter_map[meter_key] = METER_ROLE_GAS
        elif MeteringParameter.CURRENT_SUMMATION_RECEIVED in attrs:
            self._meter_map[meter_key] = METER_ROLE_ELECTRIC
        elif meter_key not in self._meter_map:
            self._meter_map[meter_key] = (
                METER_ROLE_GAS
                if METER_ROLE_GAS not in self._meter_map.values()
                else METER_ROLE_ELECTRIC
            )

    @property
    def meter_map(self) -> Mapping[str, str]:
        """Return meter-to-role map."""
        return self._meter_map
