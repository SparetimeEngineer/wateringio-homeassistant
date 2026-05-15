"""Helpers for schema parsing."""

from __future__ import annotations

from typing import Any


def extract_planter_id(item: Any) -> str | None:
    """Extract a planter id from mixed schema formats."""
    if isinstance(item, dict):
        value = item.get("id")
    else:
        value = item
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def extract_sensor_id(item: Any) -> str | None:
    """Extract a sensor modbus id from mixed schema formats."""
    if isinstance(item, dict):
        value = item.get("sensorModbusId")
    else:
        value = item
    if value is None:
        return None
    text = str(value).strip()
    return text or None
