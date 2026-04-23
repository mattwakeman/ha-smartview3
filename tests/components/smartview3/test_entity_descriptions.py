"""Metadata validation tests for Smartview sensor descriptions."""

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from custom_components.smartview3.entity_descriptions import SENSOR_DESCRIPTIONS


def test_energy_and_power_metadata_are_present() -> None:
    by_key = {desc.key: desc for desc in SENSOR_DESCRIPTIONS}

    assert by_key["electric_import_energy"].device_class == SensorDeviceClass.ENERGY
    assert by_key["electric_import_energy"].state_class == SensorStateClass.TOTAL_INCREASING
    assert by_key["gas_energy"].device_class == SensorDeviceClass.ENERGY
    assert by_key["gas_energy"].state_class == SensorStateClass.TOTAL_INCREASING
    assert by_key["electric_power"].device_class == SensorDeviceClass.POWER
    assert by_key["electric_power"].state_class == SensorStateClass.MEASUREMENT


def test_gas_volume_exposes_gas_device_class() -> None:
    gas_volume = next(desc for desc in SENSOR_DESCRIPTIONS if desc.key == "gas_volume")
    assert gas_volume.device_class == SensorDeviceClass.GAS
    assert gas_volume.state_class == SensorStateClass.TOTAL_INCREASING
