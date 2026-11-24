"""Poll the sensor and decide when it counts as unavailable."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from modbus_connection import ModbusError

from mtdx62 import Mtdx62Device, Readings

from .const import DOMAIN, MAX_CONSECUTIVE_FAILURES, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class Mtdx62Coordinator(DataUpdateCoordinator[Readings]):
    """Read the sensor every few seconds and track how long it stays silent."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, device: Mtdx62Device) -> None:
        """Set up the coordinator for one sensor."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.device = device
        self._failures = 0
        self._unavailable_logged = False
        self._reported_fault: int | None = None

    async def _async_update_data(self) -> Readings:
        """Read the measurements, tolerating a single lost frame."""
        try:
            await self.device.async_update_readings()
        except ModbusError as err:
            self._failures += 1
            if self._failures < MAX_CONSECUTIVE_FAILURES and self.data is not None:
                _LOGGER.debug("%s: poll %s failed, retrying: %s", self.name, self._failures, err)
                return self.data
            self._log_unavailable()
            raise UpdateFailed(f"cannot read {self.name}") from err

        if self._failures:
            self._failures = 0
            if self._unavailable_logged:
                _LOGGER.info("%s: sensor is answering again", self.name)
                self._unavailable_logged = False

        self._log_fault()
        return self.device.readings

    def _log_unavailable(self) -> None:
        """Say the sensor is gone once, not on every failed poll."""
        if not self._unavailable_logged:
            _LOGGER.warning(
                "%s: no answer after %s polls, marking unavailable",
                self.name,
                self._failures,
            )
            self._unavailable_logged = True

    def _log_fault(self) -> None:
        """Report a health code once when it appears and once when it clears."""
        code = self.device.readings.status_code
        if code in (None, 0):
            if self._reported_fault is not None:
                _LOGGER.info("%s: health code back to normal", self.name)
                self._reported_fault = None
            return
        if code != self._reported_fault:
            _LOGGER.warning("%s: sensor reports health code %s", self.name, code)
            self._reported_fault = code


__all__ = ["DOMAIN", "Mtdx62Coordinator"]
