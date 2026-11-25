"""Helpers shared by the config flow, setup and diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from homeassistant.const import CONF_DEVICE, CONF_HOST, CONF_PORT
from modbus_connection import ModbusSerialParams, ModbusTcpParams

from .const import (
    CONF_BAUDRATE,
    CONF_MODEL,
    CONF_PARITY,
    CONF_STOPBITS,
    CONF_TYPE,
    CONF_UNIT_ID,
    MODELS,
    TYPE_SERIAL,
)


def create_modbus_params(data: Mapping[str, Any]) -> ModbusTcpParams | ModbusSerialParams:
    """Build the link parameters the ``modbus`` integration shares by."""
    if data[CONF_TYPE] == TYPE_SERIAL:
        return ModbusSerialParams(
            device=data[CONF_DEVICE],
            baudrate=data[CONF_BAUDRATE],
            parity=data[CONF_PARITY],
            stopbits=data[CONF_STOPBITS],
        )
    return ModbusTcpParams(host=data[CONF_HOST], port=data[CONF_PORT])


def create_unique_id(data: Mapping[str, Any]) -> str:
    """Identify the device by its link settings and bus address.

    The sensor exposes no serial number that this integration reads, so the link
    plus the unit id is what makes one physical device unique. The same device
    reached through another gateway is a different link and gets its own entry.
    """
    if data[CONF_TYPE] == TYPE_SERIAL:
        link = (
            f"serial:{data[CONF_DEVICE]}:{data[CONF_BAUDRATE]}:"
            f"{data[CONF_PARITY]}:{data[CONF_STOPBITS]}"
        )
    else:
        link = f"tcp:{data[CONF_HOST]}:{data[CONF_PORT]}"
    return f"{link}#{data[CONF_UNIT_ID]}"


def create_title(data: Mapping[str, Any]) -> str:
    """Name the entry after the model the user picked."""
    return MODELS[data[CONF_MODEL]]


def create_link_label(data: Mapping[str, Any]) -> str:
    """What went wrong with, in the words the user typed."""
    if data[CONF_TYPE] == TYPE_SERIAL:
        return str(data[CONF_DEVICE])
    return f"{data[CONF_HOST]}:{data[CONF_PORT]}"


def serial_port_exists(data: Mapping[str, Any]) -> bool:
    """Whether the serial device the user picked is present.

    A path in ``/dev`` that does not exist is a different story from a port that
    exists but will not open: the first is usually a wrong choice in the list, the
    second is a port taken by another program or a permission problem.
    """
    if data[CONF_TYPE] != TYPE_SERIAL:
        return True
    return Path(str(data[CONF_DEVICE])).exists()


def present_serial_ports() -> list[str]:
    """Serial devices worth naming when a port will not open.

    USB adapters show up under ``/dev/serial/by-id`` with a stable name and as
    ``ttyUSB*`` or ``ttyACM*``. UARTs on the board itself are listed too, because
    picking one of those instead of the adapter is a common mistake.
    """
    patterns = ("/dev/serial/by-id/*", "/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyAMA*")
    found: set[str] = set()
    for pattern in patterns:
        found.update(str(path) for path in Path("/dev").glob(pattern.removeprefix("/dev/")))
    return sorted(found)
