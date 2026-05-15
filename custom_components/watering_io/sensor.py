from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SIGNAL_UPDATE, WateringIoCoordinator
from .entity import WateringEntity, WateringPlanterEntity
from .helpers import extract_planter_id, extract_sensor_id

SYSTEM_FIELDS = ["wifiRssi", "busCurrent", "uptime", "firmwareVersion", "buildGit", "buildCommit", "buildDirty", "buildTimeUtc"]
PLANTER_FIELDS = ["moisture", "target", "nextDoseInMs", "state", "valveMask", "dose_ms"]
SENSOR_FIELDS = ["moisture", "temperature", "lastSeenMs", "missedScans"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: WateringIoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WateringSystemSensor(coordinator, f) for f in SYSTEM_FIELDS])

    added_planters: set[str] = set()
    added_sensors: set[str] = set()

    @callback
    def add_dynamic() -> None:
        new_entities = []
        for planter in coordinator.state.schema.get("entities", {}).get("planters", []):
            planter_id = extract_planter_id(planter)
            if not planter_id or planter_id in added_planters:
                continue
            added_planters.add(planter_id)
            for field in PLANTER_FIELDS:
                new_entities.append(WateringPlanterSensor(coordinator, planter_id, field))

        for sensor in coordinator.state.schema.get("entities", {}).get("sensors", []):
            sensor_id = extract_sensor_id(sensor)
            if not sensor_id or sensor_id in added_sensors:
                continue
            added_sensors.add(sensor_id)
            for field in SENSOR_FIELDS:
                new_entities.append(WateringDynamicSensor(coordinator, sensor_id, field))

        for planter_id in coordinator.state.planter_status:
            if planter_id in added_planters:
                continue
            added_planters.add(planter_id)
            for field in PLANTER_FIELDS:
                new_entities.append(WateringPlanterSensor(coordinator, planter_id, field))

        for sensor_id in coordinator.state.sensor_status:
            if sensor_id in added_sensors:
                continue
            added_sensors.add(sensor_id)
            for field in SENSOR_FIELDS:
                new_entities.append(WateringDynamicSensor(coordinator, sensor_id, field))

        if new_entities:
            async_add_entities(new_entities)

    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_UPDATE, add_dynamic))
    add_dynamic()


class WateringSystemSensor(WateringEntity, SensorEntity):
    def __init__(self, coordinator: WateringIoCoordinator, field: str) -> None:
        super().__init__(coordinator)
        self.field = field
        self._attr_name = field
        self._attr_unique_id = f"{coordinator.device_id}_system_{field}"

    @property
    def native_value(self):
        return self.coordinator.state.system_status.get(self.field)


class WateringPlanterSensor(WateringPlanterEntity, SensorEntity):
    def __init__(self, coordinator: WateringIoCoordinator, planter_id: str, field: str) -> None:
        super().__init__(coordinator, planter_id)
        self.field = field
        self._attr_name = f"Planter {planter_id} {field}"
        self._attr_unique_id = f"{coordinator.device_id}_planter_{planter_id}_{field}"

    @property
    def native_value(self):
        return self.coordinator.state.planter_status.get(self.planter_id, {}).get(self.field)


class WateringDynamicSensor(WateringEntity, SensorEntity):
    def __init__(self, coordinator: WateringIoCoordinator, sensor_id: str, field: str) -> None:
        super().__init__(coordinator)
        self.sensor_id = sensor_id
        self.field = field
        self._attr_name = f"Sensor {sensor_id} {field}"
        self._attr_unique_id = f"{coordinator.device_id}_sensor_{sensor_id}_{field}"

    @property
    def native_value(self):
        return self.coordinator.state.sensor_status.get(self.sensor_id, {}).get(self.field)
