"""Base entities for watering_io."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .coordinator import SIGNAL_UPDATE, WateringIoCoordinator


class WateringEntity(Entity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: WateringIoCoordinator) -> None:
        self.coordinator = coordinator

    @property
    def available(self) -> bool:
        return self.coordinator.device_available

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.device_id)},
            name=self.coordinator.state.device_info.get("name", "Watering.IO Hub"),
            manufacturer="Watering.IO",
            model="Watering.IO Hub",
            sw_version=self.coordinator.state.device_info.get("firmwareVersion"),
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_UPDATE,
                self._async_handle_update,
            )
        )

    def _async_handle_update(self) -> None:
        self.async_write_ha_state()
