# Watering.IO Home Assistant Custom Integration

## HACS Installation

1. Open HACS > **Integrations**.
2. Open the menu > **Custom repositories**.
3. Add this repository URL and select category **Integration**.
4. Search for **Watering.IO Hub** and install it.
5. Restart Home Assistant.
6. Go to **Settings > Devices & services > Add integration** and add **Watering.IO Hub**.
7. Enter the MQTT topic prefix. The default is `watering.io`.

> Important: your hub must publish retained messages to `<prefix>/device/availability`, `<prefix>/device/info`, and `<prefix>/integration/schema`.

## MQTT Contract Integration

This repository contains a custom Home Assistant integration (`custom_components/watering_io`) that consumes the Watering.IO Hub MQTT firmware contract directly, without Home Assistant MQTT Discovery.

The integration subscribes to:

- `<prefix>/device/availability`
- `<prefix>/device/info`
- `<prefix>/integration/schema`
- schema-derived status topics for system, pumps, planters, and sensors

Entities are created for:

- System sensors: uptime, Wi-Fi RSSI, bus current, firmware/build diagnostics
- Pump binary sensors
- Per-planter sensors and binary sensors
- Per-sensor moisture/temperature/online diagnostics
- Sensor rescan button publishing `{}` to `<prefix>/command/sensors/rescan`

## Dashboard Card

The integration bundles a Lovelace custom card for a single planter:

```yaml
type: custom:watering-io-planter-card
name: Tomatoes
crop: tomato
moisture_entity: sensor.planter_1_moisture
target_entity: sensor.planter_1_target
online_entity: binary_sensor.planter_1_online
watering_entity: binary_sensor.planter_1_watering
state_entity: sensor.planter_1_state
```

Available crop presets:

- `generic`
- `tomato`
- `basil`
- `lettuce`
- `chili`
- `strawberry`
- `cucumber`
- `herbs`

### Add The Card Resource

After installing or updating the integration and restarting Home Assistant, add this dashboard resource:

```text
URL: /watering_io_static/watering-io-planter-card.js?v=0.1.7
Resource type: JavaScript module
```

In the Home Assistant UI this is under **Settings > Dashboards > Resources**.

The card also appears in the visual card picker as **Watering.IO Planter**. Use explicit entity IDs for each planter card so the dashboard remains stable even if entity names are customized.
