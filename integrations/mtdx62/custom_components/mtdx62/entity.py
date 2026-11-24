"""Common base for the sensor's entities."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MODEL, DOMAIN, MANUFACTURER, MODELS
from .coordinator import Mtdx62Coordinator


class Mtdx62Entity(CoordinatorEntity[Mtdx62Coordinator]):
    """An entity of one presence sensor, named after the device.

    The unique id is built from the config entry and the entity key, so renaming
    the device or moving it to another gateway address keeps history intact.
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: Mtdx62Coordinator, key: str) -> None:
        """Attach the entity to the entry's device."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=MODELS[entry.data[CONF_MODEL]],
            name=entry.title,
            sw_version=coordinator.device.readings.app_version,
        )
