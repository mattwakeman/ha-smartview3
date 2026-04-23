"""Sensor descriptions for Smartview 3 entities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfVolume

from .const import METER_ROLE_ELECTRIC, METER_ROLE_GAS
from .decoder import Cluster, MeteringParameter, PrepaymentParameter


@dataclass(frozen=True, slots=True)
class SmartviewSensorDescription:
    """Description for one Smartview mapped sensor."""

    key: str
    meter_role: str
    cluster: int
    attribute: int
    native_unit: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    enabled_default: bool = True
    entity_registry_visible_default: bool = True
    value_fn: Callable[[dict[int, dict[str, Any]], float], float] | None = None

    @property
    def suggested_unit_of_measurement(self) -> str | None:
        """Return the suggested unit of measurement."""
        return self.native_unit

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self.enabled_default

    def get_value(self, cluster_data: dict[int, dict[str, Any]], gas_kwh_per_m3: float) -> float | None:
        """Resolve value from cluster payload."""
        attr_data = cluster_data.get(self.attribute)
        if not attr_data:
            return None
        raw = attr_data["value"]
        if self.value_fn:
            return self.value_fn(cluster_data, gas_kwh_per_m3)
        return float(raw)


def _raw(attr: int) -> Callable[[dict[int, dict[str, Any]], float], float]:
    return lambda cluster_data, _: float(cluster_data[attr]["value"])


def _div(attr: int, divisor: float) -> Callable[[dict[int, dict[str, Any]], float], float]:
    return lambda cluster_data, _: float(cluster_data[attr]["value"]) / divisor


def _bill_to_date(attr: int) -> Callable[[dict[int, dict[str, Any]], float], float]:
    def _inner(cluster_data: dict[int, dict[str, Any]], _: float) -> float:
        trailing = cluster_data.get(MeteringParameter.BILL_DELIVERED_TRAILING_DIGIT)
        if not trailing:
            return float(cluster_data[attr]["value"])
        trailing_digits = int(trailing["value"]) >> 4
        return float(cluster_data[attr]["value"]) / pow(10, trailing_digits)

    return _inner


def _prepayment_currency(attr: int) -> Callable[[dict[int, dict[str, Any]], float], float]:
    return lambda cluster_data, _: float(cluster_data[attr]["value"]) / 100000


def _gas_m3_to_kwh(attr: int) -> Callable[[dict[int, dict[str, Any]], float], float]:
    return lambda cluster_data, factor: (float(cluster_data[attr]["value"]) / 1000) * factor


SENSOR_DESCRIPTIONS: tuple[SmartviewSensorDescription, ...] = (
    SmartviewSensorDescription(
        key="electric_power",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.INSTANTANEOUS_DEMAND,
        native_unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_raw(MeteringParameter.INSTANTANEOUS_DEMAND),
    ),
    SmartviewSensorDescription(
        key="electric_import_energy",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.CURRENT_SUMMATION_DELIVERED,
        native_unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_div(MeteringParameter.CURRENT_SUMMATION_DELIVERED, 1000),
    ),
    SmartviewSensorDescription(
        key="electric_export_energy",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.CURRENT_SUMMATION_RECEIVED,
        native_unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_div(MeteringParameter.CURRENT_SUMMATION_RECEIVED, 1000),
    ),
    SmartviewSensorDescription(
        key="electric_bill_to_date",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.BILL_TO_DATE_DELIVERED,
        value_fn=_bill_to_date(MeteringParameter.BILL_TO_DATE_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="electric_current_day_wh",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.CURRENT_DAY_CONSUMPTION_DELIVERED,
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_raw(MeteringParameter.CURRENT_DAY_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="electric_previous_day_wh",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.PREVIOUS_DAY_CONSUMPTION_DELIVERED,
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_raw(MeteringParameter.PREVIOUS_DAY_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="electric_current_week_wh",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.CURRENT_WEEK_CONSUMPTION_DELIVERED,
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_raw(MeteringParameter.CURRENT_WEEK_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="electric_previous_week_wh",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.PREVIOUS_WEEK_CONSUMPTION_DELIVERED,
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_raw(MeteringParameter.PREVIOUS_WEEK_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="electric_current_month_wh",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.CURRENT_MONTH_CONSUMPTION_DELIVERED,
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_raw(MeteringParameter.CURRENT_MONTH_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="electric_previous_month_wh",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.PREVIOUS_MONTH_CONSUMPTION_DELIVERED,
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_raw(MeteringParameter.PREVIOUS_MONTH_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="gas_volume",
        meter_role=METER_ROLE_GAS,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.CURRENT_SUMMATION_DELIVERED,
        native_unit=UnitOfVolume.CUBIC_METERS,
        device_class=SensorDeviceClass.GAS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_div(MeteringParameter.CURRENT_SUMMATION_DELIVERED, 1000),
    ),
    SmartviewSensorDescription(
        key="gas_energy",
        meter_role=METER_ROLE_GAS,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.CURRENT_SUMMATION_DELIVERED,
        native_unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_gas_m3_to_kwh(MeteringParameter.CURRENT_SUMMATION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="gas_bill_to_date",
        meter_role=METER_ROLE_GAS,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.BILL_TO_DATE_DELIVERED,
        value_fn=_bill_to_date(MeteringParameter.BILL_TO_DATE_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="gas_current_day_wh",
        meter_role=METER_ROLE_GAS,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.CURRENT_DAY_ALTERNATIVE_CONSUMPTION_DELIVERED,
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_raw(MeteringParameter.CURRENT_DAY_ALTERNATIVE_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="gas_previous_day_wh",
        meter_role=METER_ROLE_GAS,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.PREVIOUS_DAY_ALTERNATIVE_CONSUMPTION_DELIVERED,
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_raw(MeteringParameter.PREVIOUS_DAY_ALTERNATIVE_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="gas_current_week_wh",
        meter_role=METER_ROLE_GAS,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.CURRENT_WEEK_ALTERNATIVE_CONSUMPTION_DELIVERED,
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_raw(MeteringParameter.CURRENT_WEEK_ALTERNATIVE_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="gas_previous_week_wh",
        meter_role=METER_ROLE_GAS,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.PREVIOUS_WEEK_ALTERNATIVE_CONSUMPTION_DELIVERED,
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_raw(MeteringParameter.PREVIOUS_WEEK_ALTERNATIVE_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="gas_current_month_wh",
        meter_role=METER_ROLE_GAS,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.CURRENT_MONTH_ALTERNATIVE_CONSUMPTION_DELIVERED,
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_raw(MeteringParameter.CURRENT_MONTH_ALTERNATIVE_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="gas_previous_month_wh",
        meter_role=METER_ROLE_GAS,
        cluster=Cluster.METERING,
        attribute=MeteringParameter.PREVIOUS_MONTH_ALTERNATIVE_CONSUMPTION_DELIVERED,
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_raw(MeteringParameter.PREVIOUS_MONTH_ALTERNATIVE_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="electric_cost_day",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.PREPAYMENT,
        attribute=PrepaymentParameter.CURRENT_DAY_COST_CONSUMPTION_DELIVERED,
        value_fn=_prepayment_currency(PrepaymentParameter.CURRENT_DAY_COST_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="electric_cost_week",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.PREPAYMENT,
        attribute=PrepaymentParameter.CURRENT_WEEK_COST_CONSUMPTION_DELIVERED,
        value_fn=_prepayment_currency(PrepaymentParameter.CURRENT_WEEK_COST_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="electric_cost_month",
        meter_role=METER_ROLE_ELECTRIC,
        cluster=Cluster.PREPAYMENT,
        attribute=PrepaymentParameter.CURRENT_MONTH_COST_CONSUMPTION_DELIVERED,
        value_fn=_prepayment_currency(PrepaymentParameter.CURRENT_MONTH_COST_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="gas_cost_day",
        meter_role=METER_ROLE_GAS,
        cluster=Cluster.PREPAYMENT,
        attribute=PrepaymentParameter.CURRENT_DAY_COST_CONSUMPTION_DELIVERED,
        value_fn=_prepayment_currency(PrepaymentParameter.CURRENT_DAY_COST_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="gas_cost_week",
        meter_role=METER_ROLE_GAS,
        cluster=Cluster.PREPAYMENT,
        attribute=PrepaymentParameter.CURRENT_WEEK_COST_CONSUMPTION_DELIVERED,
        value_fn=_prepayment_currency(PrepaymentParameter.CURRENT_WEEK_COST_CONSUMPTION_DELIVERED),
    ),
    SmartviewSensorDescription(
        key="gas_cost_month",
        meter_role=METER_ROLE_GAS,
        cluster=Cluster.PREPAYMENT,
        attribute=PrepaymentParameter.CURRENT_MONTH_COST_CONSUMPTION_DELIVERED,
        value_fn=_prepayment_currency(PrepaymentParameter.CURRENT_MONTH_COST_CONSUMPTION_DELIVERED),
    ),
)
