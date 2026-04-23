"""Binary sensor platform for Smartview 3."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, METER_ROLE_ELECTRIC
from .coordinator import Smartview3Coordinator
from .decoder import Cluster, MeteringParameter


@dataclass(frozen=True, slots=True)
class SmartviewBinaryDescription:
    """Description for Smartview binary entity."""

    key: str
    meter_role: str
    cluster: int
    attribute: int
    bitmask: int
    device_class: BinarySensorDeviceClass | None = None


BINARY_DESCRIPTIONS: tuple[SmartviewBinaryDescription, ...] = (
    SmartviewBinaryDescription(
        key="low_battery",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.STATUS,
        bitmask=0x01,
        device_class=BinarySensorDeviceClass.BATTERY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smartview binary sensors."""
    coordinator: Smartview3Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        Smartview3BinarySensor(coordinator, entry, description)
        for description in BINARY_DESCRIPTIONS
    )


class Smartview3BinarySensor(
    CoordinatorEntity[Smartview3Coordinator], BinarySensorEntity
):
    """Binary sensor based on Smartview status bitmaps."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Smartview3Coordinator,
        entry: ConfigEntry,
        description: SmartviewBinaryDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_translation_key = description.key
        self._attr_name = None
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_class = description.device_class

    @property
    def device_info(self) -> DeviceInfo:
        """Return parent Smartview device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Smartview 3",
            manufacturer="Chameleon Technology",
            model="Smartview 3",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true when status bit indicates low battery."""
        role_map = self.coordinator.data.get("roles", {})
        meter_key = role_map.get(self.entity_description.meter_role)
        if not meter_key:
            return None

        meter_payload = self.coordinator.data.get("meters", {}).get(meter_key, {})
        cluster_payload = meter_payload.get(self.entity_description.cluster, {})
        attribute_data = cluster_payload.get(self.entity_description.attribute)
        if not attribute_data:
            return None

        status_value = int(attribute_data["value"])
        return bool(status_value & self.entity_description.bitmask)
