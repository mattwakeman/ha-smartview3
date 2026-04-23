"""Sensor platform for Smartview 3."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ENABLE_DIAGNOSTIC_SENSORS,
    CONF_GAS_KWH_PER_M3,
    DOMAIN,
    METER_ROLE_ELECTRIC,
    METER_ROLE_GAS,
)
from .coordinator import Smartview3Coordinator
from .decoder import Cluster, PrepaymentParameter
from .entity_descriptions import SENSOR_DESCRIPTIONS, SmartviewSensorDescription


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smartview sensors based on description registry."""
    coordinator: Smartview3Coordinator = hass.data[DOMAIN][entry.entry_id]
    enable_diagnostics = entry.options.get(CONF_ENABLE_DIAGNOSTIC_SENSORS, False)

    entities: list[SensorEntity] = []
    for description in SENSOR_DESCRIPTIONS:
        if not description.enabled_default and not enable_diagnostics:
            continue
        entities.append(Smartview3Sensor(coordinator, entry, description))
    entities.append(
        Smartview3CombinedCostSensor(
            coordinator,
            entry,
            translation_key="total_current_day_cost",
            unique_suffix="total_current_day_cost",
            attribute=PrepaymentParameter.CURRENT_DAY_COST_CONSUMPTION_DELIVERED,
        )
    )
    entities.append(
        Smartview3CombinedCostSensor(
            coordinator,
            entry,
            translation_key="total_current_week_cost",
            unique_suffix="total_current_week_cost",
            attribute=PrepaymentParameter.CURRENT_WEEK_COST_CONSUMPTION_DELIVERED,
        )
    )
    entities.append(
        Smartview3CombinedCostSensor(
            coordinator,
            entry,
            translation_key="total_current_month_cost",
            unique_suffix="total_current_month_cost",
            attribute=PrepaymentParameter.CURRENT_MONTH_COST_CONSUMPTION_DELIVERED,
        )
    )

    async_add_entities(entities)


class Smartview3Sensor(CoordinatorEntity[Smartview3Coordinator], SensorEntity):
    """Representation of a Smartview mapped sensor."""

    def __init__(
        self,
        coordinator: Smartview3Coordinator,
        entry: ConfigEntry,
        description: SmartviewSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.key
        self._attr_native_unit_of_measurement = description.native_unit
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class

    @property
    def device_info(self) -> DeviceInfo:
        """Return info for grouping entities."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Smartview 3",
            manufacturer="Chameleon Technology",
            model="Smartview 3",
        )

    @property
    def native_value(self) -> float | None:
        """Return current value from coordinator snapshot."""
        role_map = self.coordinator.data.get("roles", {})
        meter_key = role_map.get(self.entity_description.meter_role)
        if not meter_key:
            return None

        meter_payload = self.coordinator.data.get("meters", {}).get(meter_key, {})
        cluster_payload = meter_payload.get(self.entity_description.cluster, {})
        if not cluster_payload:
            return None

        gas_factor = float(self._entry.options.get(CONF_GAS_KWH_PER_M3, 11.2))
        return self.entity_description.get_value(cluster_payload, gas_factor)

    @property
    def available(self) -> bool:
        """Return if role has been identified and data exists."""
        role_map = self.coordinator.data.get("roles", {})
        return self.entity_description.meter_role in role_map and super().available

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional diagnostic metadata."""
        return {"meter_role": self.entity_description.meter_role}


class Smartview3CombinedCostSensor(
    CoordinatorEntity[Smartview3Coordinator], SensorEntity
):
    """Combined electric+gas cost sensor for a period."""

    def __init__(
        self,
        coordinator: Smartview3Coordinator,
        entry: ConfigEntry,
        translation_key: str,
        unique_suffix: str,
        attribute: PrepaymentParameter,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attribute = attribute
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
        self._attr_name = unique_suffix

    @property
    def device_info(self) -> DeviceInfo:
        """Return info for grouping entities."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Smartview 3",
            manufacturer="Chameleon Technology",
            model="Smartview 3",
        )

    @property
    def native_value(self) -> float | None:
        """Return combined cost across electric and gas."""
        role_map = self.coordinator.data.get("roles", {})
        electric_meter = role_map.get(METER_ROLE_ELECTRIC)
        gas_meter = role_map.get(METER_ROLE_GAS)

        def _get_cost(meter_key: str | None) -> float | None:
            if not meter_key:
                return None
            meter_payload = self.coordinator.data.get("meters", {}).get(meter_key, {})
            prepay_payload = meter_payload.get(Cluster.PREPAYMENT, {})
            attr = prepay_payload.get(self._attribute)
            if not attr:
                return None
            return float(attr["value"]) / 100000

        electric = _get_cost(electric_meter)
        gas = _get_cost(gas_meter)
        if electric is None and gas is None:
            return None
        return (electric or 0.0) + (gas or 0.0)
