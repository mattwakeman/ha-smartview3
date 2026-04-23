"""Tests for Smartview sensors."""

from tests.common import MockConfigEntry

from custom_components.smartview3.const import METER_ROLE_ELECTRIC, METER_ROLE_GAS
from custom_components.smartview3.decoder import Cluster, PrepaymentParameter
from custom_components.smartview3.sensor import Smartview3CombinedCostSensor


class _FakeCoordinator:
    """Minimal coordinator stub for sensor testing."""

    def __init__(
        self,
        electric_cost_day: int | None,
        gas_cost_day: int | None,
        electric_cost_week: int | None = None,
        gas_cost_week: int | None = None,
        electric_cost_month: int | None = None,
        gas_cost_month: int | None = None,
    ) -> None:
        meters = {}
        if electric_cost_day is not None or electric_cost_week is not None or electric_cost_month is not None:
            electric_prepay = {}
            if electric_cost_day is not None:
                electric_prepay[PrepaymentParameter.CURRENT_DAY_COST_CONSUMPTION_DELIVERED] = {
                    "value": electric_cost_day,
                    "type": 0x22,
                }
            if electric_cost_week is not None:
                electric_prepay[PrepaymentParameter.CURRENT_WEEK_COST_CONSUMPTION_DELIVERED] = {
                    "value": electric_cost_week,
                    "type": 0x22,
                }
            if electric_cost_month is not None:
                electric_prepay[PrepaymentParameter.CURRENT_MONTH_COST_CONSUMPTION_DELIVERED] = {
                    "value": electric_cost_month,
                    "type": 0x22,
                }
            meters["1234"] = {
                Cluster.PREPAYMENT: electric_prepay
            }
        if gas_cost_day is not None or gas_cost_week is not None or gas_cost_month is not None:
            gas_prepay = {}
            if gas_cost_day is not None:
                gas_prepay[PrepaymentParameter.CURRENT_DAY_COST_CONSUMPTION_DELIVERED] = {
                    "value": gas_cost_day,
                    "type": 0x22,
                }
            if gas_cost_week is not None:
                gas_prepay[PrepaymentParameter.CURRENT_WEEK_COST_CONSUMPTION_DELIVERED] = {
                    "value": gas_cost_week,
                    "type": 0x22,
                }
            if gas_cost_month is not None:
                gas_prepay[PrepaymentParameter.CURRENT_MONTH_COST_CONSUMPTION_DELIVERED] = {
                    "value": gas_cost_month,
                    "type": 0x22,
                }
            meters["abcd"] = {
                Cluster.PREPAYMENT: gas_prepay
            }

        self.data = {
            "roles": {METER_ROLE_ELECTRIC: "1234", METER_ROLE_GAS: "abcd"},
            "meters": meters,
        }
        self.last_update_success = True

    def async_add_listener(self, update_callback, context=None):
        return lambda: None


def _entity(
    translation_key: str,
    unique_suffix: str,
    attribute: PrepaymentParameter,
    electric_cost_day: int | None,
    gas_cost_day: int | None,
    electric_cost_week: int | None = None,
    gas_cost_week: int | None = None,
    electric_cost_month: int | None = None,
    gas_cost_month: int | None = None,
) -> Smartview3CombinedCostSensor:
    entry = MockConfigEntry(domain="smartview3", data={"serial_device": "/dev/ttyUSB0"})
    return Smartview3CombinedCostSensor(
        _FakeCoordinator(
            electric_cost_day=electric_cost_day,
            gas_cost_day=gas_cost_day,
            electric_cost_week=electric_cost_week,
            gas_cost_week=gas_cost_week,
            electric_cost_month=electric_cost_month,
            gas_cost_month=gas_cost_month,
        ),
        entry,
        translation_key=translation_key,
        unique_suffix=unique_suffix,
        attribute=attribute,
    )


def test_total_current_day_cost_sums_electric_and_gas() -> None:
    entity = _entity(
        translation_key="total_current_day_cost",
        unique_suffix="total_current_day_cost",
        attribute=PrepaymentParameter.CURRENT_DAY_COST_CONSUMPTION_DELIVERED,
        electric_cost_day=120000,
        gas_cost_day=355000,
    )
    assert entity.native_value == 4.75


def test_total_current_day_cost_returns_single_side_when_other_missing() -> None:
    entity = _entity(
        translation_key="total_current_day_cost",
        unique_suffix="total_current_day_cost",
        attribute=PrepaymentParameter.CURRENT_DAY_COST_CONSUMPTION_DELIVERED,
        electric_cost_day=120000,
        gas_cost_day=None,
    )
    assert entity.native_value == 1.2


def test_total_current_day_cost_unknown_when_both_missing() -> None:
    entity = _entity(
        translation_key="total_current_day_cost",
        unique_suffix="total_current_day_cost",
        attribute=PrepaymentParameter.CURRENT_DAY_COST_CONSUMPTION_DELIVERED,
        electric_cost_day=None,
        gas_cost_day=None,
    )
    assert entity.native_value is None


def test_total_current_week_cost_sums_electric_and_gas() -> None:
    entity = _entity(
        translation_key="total_current_week_cost",
        unique_suffix="total_current_week_cost",
        attribute=PrepaymentParameter.CURRENT_WEEK_COST_CONSUMPTION_DELIVERED,
        electric_cost_day=None,
        gas_cost_day=None,
        electric_cost_week=230000,
        gas_cost_week=170000,
    )
    assert entity.native_value == 4.0


def test_total_current_month_cost_sums_electric_and_gas() -> None:
    entity = _entity(
        translation_key="total_current_month_cost",
        unique_suffix="total_current_month_cost",
        attribute=PrepaymentParameter.CURRENT_MONTH_COST_CONSUMPTION_DELIVERED,
        electric_cost_day=None,
        gas_cost_day=None,
        electric_cost_month=999000,
        gas_cost_month=111000,
    )
    assert entity.native_value == 11.1
