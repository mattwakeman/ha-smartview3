"""Coordinator integration-style tests using mocked Smartview device."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from serial import SerialException
from tests.common import MockConfigEntry

from custom_components.smartview3.const import METER_ROLE_ELECTRIC, METER_ROLE_GAS
from custom_components.smartview3.coordinator import Smartview3Coordinator
from custom_components.smartview3.decoder import Cluster, MeteringParameter
from custom_components.smartview3.serial_client import SmartviewSample


@dataclass
class FakeSerialClient:
    """Fake serial client for coordinator tests."""

    batches: list[list[SmartviewSample]]
    fail_once: bool = False
    closed: bool = False
    opened: bool = False
    scan_interval: int = 10

    def open(self) -> None:
        self.opened = True

    def close(self) -> None:
        self.closed = True

    def read_samples(self, max_packets: int = 8) -> list[SmartviewSample]:
        if self.fail_once:
            self.fail_once = False
            raise SerialException("device offline")
        if self.batches:
            return self.batches.pop(0)
        return []


def _sample(meter: bytes, attribute: int, value: int, cluster: int = Cluster.METERING) -> SmartviewSample:
    return SmartviewSample(
        meter=meter,
        cluster=cluster,
        parameters={attribute: {"type": 0x22, "value": value}},
        received_ts=100.0,
    )


@pytest.mark.asyncio
async def test_coordinator_detects_roles_without_hardcoded_ids(hass) -> None:
    entry = MockConfigEntry(domain="smartview3", data={"serial_device": "/dev/ttyUSB0"})
    entry.add_to_hass(hass)
    client = FakeSerialClient(
        batches=[
            [
                _sample(b"\x12\x34", MeteringParameter.INSTANTANEOUS_DEMAND, 450),
                _sample(
                    b"\xAB\xCD",
                    MeteringParameter.CURRENT_DAY_ALTERNATIVE_CONSUMPTION_DELIVERED,
                    1200,
                ),
            ]
        ]
    )
    coordinator = Smartview3Coordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data["roles"][METER_ROLE_ELECTRIC] == "1234"
    assert coordinator.data["roles"][METER_ROLE_GAS] == "abcd"


@pytest.mark.asyncio
async def test_coordinator_recovers_after_disconnect(hass) -> None:
    entry = MockConfigEntry(domain="smartview3", data={"serial_device": "/dev/ttyUSB0"})
    entry.add_to_hass(hass)
    client = FakeSerialClient(
        batches=[[_sample(b"\x12\x34", MeteringParameter.INSTANTANEOUS_DEMAND, 450)]],
        fail_once=True,
    )
    coordinator = Smartview3Coordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    with pytest.raises(Exception):
        await coordinator.async_request_refresh()

    await coordinator.async_request_refresh()
    assert coordinator.last_update_success


@pytest.mark.asyncio
async def test_coordinator_shutdown_closes_device(hass) -> None:
    entry = MockConfigEntry(domain="smartview3", data={"serial_device": "/dev/ttyUSB0"})
    entry.add_to_hass(hass)
    client = FakeSerialClient(batches=[[]])
    coordinator = Smartview3Coordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_shutdown()
    assert client.closed is True
