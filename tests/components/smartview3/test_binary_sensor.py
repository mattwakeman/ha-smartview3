"""Tests for Smartview binary sensors."""

from tests.common import MockConfigEntry

from custom_components.smartview3.binary_sensor import Smartview3BinarySensor, SmartviewBinaryDescription
from custom_components.smartview3.const import METER_ROLE_ELECTRIC
from custom_components.smartview3.decoder import Cluster, MeteringParameter


class _FakeCoordinator:
    """Minimal coordinator stub for entity testing."""

    def __init__(self, status_value: int | None) -> None:
        meters = {}
        if status_value is not None:
            meters = {
                "1234": {
                    Cluster.METERING: {
                        MeteringParameter.STATUS: {"value": status_value, "type": 0x19}
                    }
                }
            }
        self.data = {"roles": {METER_ROLE_ELECTRIC: "1234"}, "meters": meters}
        self.last_update_success = True

    def async_add_listener(self, update_callback, context=None):
        return lambda: None


def _build_entity(status_value: int | None) -> Smartview3BinarySensor:
    entry = MockConfigEntry(domain="smartview3", data={"serial_device": "/dev/ttyUSB0"})
    description = SmartviewBinaryDescription(
        key="low_battery",
        name="Low Battery",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.STATUS,
        bitmask=0x01,
    )
    return Smartview3BinarySensor(_FakeCoordinator(status_value), entry, description)


def test_low_battery_on_when_status_bit0_set() -> None:
    entity = _build_entity(0x01)
    assert entity.is_on is True


def test_low_battery_off_when_status_bit0_clear() -> None:
    entity = _build_entity(0x00)
    assert entity.is_on is False


def test_low_battery_unknown_without_status_attribute() -> None:
    entity = _build_entity(None)
    assert entity.is_on is None
