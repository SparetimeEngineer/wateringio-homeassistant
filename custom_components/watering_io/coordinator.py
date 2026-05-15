"""Coordinator for Watering.IO MQTT contract."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN
from .helpers import extract_planter_id, extract_sensor_id

_LOGGER = logging.getLogger(__name__)

SIGNAL_UPDATE = f"{DOMAIN}_update"


@dataclass
class WateringState:
    availability_online: bool = False
    device_info: dict[str, Any] = field(default_factory=dict)
    schema: dict[str, Any] = field(default_factory=dict)
    system_status: dict[str, Any] = field(default_factory=dict)
    pumps_status: dict[str, Any] = field(default_factory=dict)
    planter_status: dict[str, dict[str, Any]] = field(default_factory=dict)
    sensor_status: dict[str, dict[str, Any]] = field(default_factory=dict)
    topic_last_update: dict[str, datetime] = field(default_factory=dict)


class WateringIoCoordinator:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.prefix = entry.data["topic_prefix"].rstrip("/")
        self.state = WateringState()
        self._unsubs: list = []

    async def async_initialize(self) -> None:
        await self._subscribe_base_topics()

    async def async_shutdown(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    @property
    def device_id(self) -> str:
        return self.state.device_info.get("deviceId", "unknown")

    @property
    def device_available(self) -> bool:
        return self.state.availability_online

    def topic_is_stale(self, topic: str, seconds: int = 60) -> bool:
        last = self.state.topic_last_update.get(topic)
        if last is None:
            return True
        return datetime.utcnow() - last > timedelta(seconds=seconds)

    async def async_publish_rescan(self) -> None:
        await mqtt.async_publish(
            self.hass,
            f"{self.prefix}/command/sensors/rescan",
            "{}",
            qos=0,
            retain=False,
        )

    async def _subscribe_base_topics(self) -> None:
        for topic, cb in (
            (f"{self.prefix}/device/availability", self._handle_availability),
            (f"{self.prefix}/device/info", self._handle_device_info),
            (f"{self.prefix}/integration/schema", self._handle_schema),
        ):
            unsub = await mqtt.async_subscribe(self.hass, topic, cb, qos=0)
            self._unsubs.append(unsub)

    async def _subscribe_schema_topics(self) -> None:
        topics = self.state.schema.get("topics", {})
        for key in ("systemStatus", "pumpsStatus"):
            topic = topics.get(key)
            if topic:
                unsub = await mqtt.async_subscribe(self.hass, topic, self._handle_status, qos=0)
                self._unsubs.append(unsub)

        for planter in self.state.schema.get("entities", {}).get("planters", []):
            planter_id = extract_planter_id(planter)
            if not planter_id:
                continue
            template = topics.get("planterStatusTemplate", f"{self.prefix}/planter/{{id}}/status")
            topic = template.replace("{id}", planter_id)
            unsub = await mqtt.async_subscribe(self.hass, topic, self._handle_status, qos=0)
            self._unsubs.append(unsub)

        for sensor in self.state.schema.get("entities", {}).get("sensors", []):
            sensor_id = extract_sensor_id(sensor)
            if not sensor_id:
                continue
            template = topics.get("sensorStatusTemplate", f"{self.prefix}/sensors/{{sensorModbusId}}/status")
            topic = template.replace("{sensorModbusId}", sensor_id)
            unsub = await mqtt.async_subscribe(self.hass, topic, self._handle_status, qos=0)
            self._unsubs.append(unsub)

    @callback
    def _notify(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_UPDATE)

    def _mark_topic_update(self, topic: str) -> None:
        self.state.topic_last_update[topic] = datetime.utcnow()

    @callback
    def _handle_availability(self, msg: ReceiveMessage) -> None:
        self.state.availability_online = msg.payload == "online"
        self._mark_topic_update(msg.topic)
        self._notify()

    @callback
    def _handle_device_info(self, msg: ReceiveMessage) -> None:
        data = self._safe_json(msg.payload)
        if not isinstance(data, dict):
            return
        self.state.device_info = data
        self._mark_topic_update(msg.topic)
        self._upsert_device()
        self._notify()

    @callback
    def _handle_schema(self, msg: ReceiveMessage) -> None:
        data = self._safe_json(msg.payload)
        if not isinstance(data, dict):
            return
        if data.get("schemaVersion") != 1:
            _LOGGER.warning("Unsupported schemaVersion: %s", data.get("schemaVersion"))
            return
        self.state.schema = data
        self._mark_topic_update(msg.topic)
        self.hass.async_create_task(self._subscribe_schema_topics())
        self._notify()

    @callback
    def _handle_status(self, msg: ReceiveMessage) -> None:
        data = self._safe_json(msg.payload)
        if not isinstance(data, dict):
            return
        self._mark_topic_update(msg.topic)

        topics = self.state.schema.get("topics", {})
        if msg.topic == topics.get("systemStatus"):
            self.state.system_status = data
        elif msg.topic == topics.get("pumpsStatus"):
            self.state.pumps_status = data
        elif "/planter/" in msg.topic and msg.topic.endswith("/status"):
            planter_id = str(data.get("id") or msg.topic.split("/planter/")[-1].split("/")[0])
            self.state.planter_status[planter_id] = data
        elif "/sensors/" in msg.topic and msg.topic.endswith("/status"):
            sensor_id = str(data.get("sensorModbusId") or msg.topic.split("/sensors/")[-1].split("/")[0])
            self.state.sensor_status[sensor_id] = data
        self._notify()

    def _safe_json(self, payload: str) -> Any:
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            _LOGGER.warning("Malformed JSON payload received")
            return None

    def _upsert_device(self) -> None:
        device_id = self.state.device_info.get("deviceId")
        if not device_id:
            return
        registry = dr.async_get(self.hass)
        registry.async_get_or_create(
            config_entry_id=self.entry.entry_id,
            identifiers={(DOMAIN, device_id)},
            name=self.state.device_info.get("name", "Watering.IO Hub"),
            model="Watering.IO Hub",
            sw_version=self.state.device_info.get("firmwareVersion"),
            manufacturer="Watering.IO",
        )
