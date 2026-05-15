# Watering.IO Home Assistant Custom Integration

## `watering_io` MQTT contract integration

This repository contains a custom Home Assistant integration (`custom_components/watering_io`) that consumes the Watering.IO Hub MQTT firmware contract directly (without Home Assistant MQTT Discovery).

### MQTT contract behavior

- Config flow asks for a topic prefix (default: `watering.io`).
- The integration subscribes to:
  - `<prefix>/device/availability`
  - `<prefix>/device/info`
  - `<prefix>/integration/schema`
  - schema-derived status topics (`system`, `pumps`, planter status template, sensor status template)
- `schemaVersion` must be `1`.
- One Home Assistant device is created using `device/info.deviceId` as the stable identifier.
- Entities are created for:
  - System sensors (uptime, Wi-Fi RSSI, bus current, firmware/build diagnostics)
  - Pump binary sensors
  - Per-planter sensors/binary sensors
  - Per-sensor moisture/temperature/online (+ diagnostics)
  - Sensor rescan button that publishes `{}` to `<prefix>/command/sensors/rescan`
- Device availability is driven by `<prefix>/device/availability` payload (`online` / `offline`).
- Parsing is defensive against missing optional fields and malformed JSON payloads.
