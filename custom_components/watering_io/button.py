from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import WateringIoCoordinator
from .entity import WateringEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: WateringIoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SensorRescanButton(coordinator)])


class SensorRescanButton(WateringEntity, ButtonEntity):
    def __init__(self, coordinator: WateringIoCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Sensor rescan"
        self._attr_unique_id = f"{coordinator.device_id}_sensor_rescan"

    async def async_press(self) -> None:
        await self.coordinator.async_publish_rescan()
