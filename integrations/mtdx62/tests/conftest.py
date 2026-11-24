"""Shared fixtures for the MTDx62 tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from modbus_connection.mock import MockModbusUnit
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mtdx62.const import (
    CONF_MODEL,
    CONF_TYPE,
    CONF_UNIT_ID,
    DOMAIN,
    MODEL_MTD062,
    TYPE_TCP,
)

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> Generator[None]:
    """Let the harness load this custom component in every test."""
    yield


@pytest.fixture
def entry_data() -> dict[str, object]:
    """Link settings of one sensor on a TCP gateway."""
    return {
        CONF_TYPE: TYPE_TCP,
        "host": "192.168.1.50",
        "port": 502,
        CONF_UNIT_ID: 1,
        CONF_MODEL: MODEL_MTD062,
    }


@pytest.fixture
def mock_entry(entry_data: dict[str, object]) -> MockConfigEntry:
    """A config entry describing that sensor."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="MTD062-MB (5.8 GHz)",
        data=entry_data,
        unique_id="tcp:192.168.1.50:502#1",
    )


@pytest.fixture
def mock_unit() -> MockModbusUnit:
    """A unit whose registers can be seeded per test."""
    from modbus_connection.mock import MockModbusConnection

    return MockModbusConnection().for_unit(1)


@pytest.fixture
def seed_readings(mock_unit: MockModbusUnit) -> MockModbusUnit:
    """Put a person in the room at 2.5 metres in dim light, sensor self-test passed."""
    mock_unit.input[0] = [1, 42, 250, 1, 0x0001, 0x0203, 0x0000, 0x0102]
    return mock_unit
