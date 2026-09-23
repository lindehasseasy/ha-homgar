"""Sensores: senal RSSI y firmware del hub; firmware y estado crudo de la valvula.

El estado en vivo de la valvula (bateria, abierto/cerrado) va cifrado en el DP
D01 (hex). De momento se expone crudo; se decodificara de forma empirica sin
inventar los bytes.
"""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import HomgarEntity, hub_device_info, valve_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {"hubs": {}, "valves": {}}
    entities: list[SensorEntity] = []
    for mid, hub in data["hubs"].items():
        entities.append(HubRssi(coordinator, mid, hub["info"]))
        entities.append(HubFirmware(coordinator, mid, hub["info"]))
    for sid, valve in data["valves"].items():
        entities.append(ValveState(coordinator, sid, valve["info"], valve["hub_mid"]))
        entities.append(ValveFirmware(coordinator, sid, valve["info"], valve["hub_mid"]))
    async_add_entities(entities)


class HubRssi(HomgarEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, mid, info) -> None:
        super().__init__(coordinator, f"hub_{mid}_rssi", "Senal")
        self._mid = mid
        self._attr_unique_id = f"homgar_hub_{mid}_rssi"
        self._attr_device_info = hub_device_info(mid, info)

    @property
    def native_value(self):
        hub = (self.coordinator.data or {}).get("hubs", {}).get(self._mid)
        return None if hub is None else hub.get("rssi")


class HubFirmware(HomgarEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, mid, info) -> None:
        super().__init__(coordinator, f"hub_{mid}_fw", "Firmware")
        self._mid = mid
        self._attr_unique_id = f"homgar_hub_{mid}_fw"
        self._attr_device_info = hub_device_info(mid, info)

    @property
    def native_value(self):
        hub = (self.coordinator.data or {}).get("hubs", {}).get(self._mid)
        return None if hub is None else (hub["info"].get("softVer") or None)


class ValveState(HomgarEntity, SensorEntity):
    """Estado crudo D01 (decode de bateria/valvula pendiente, sin inventar)."""

    _attr_icon = "mdi:water"

    def __init__(self, coordinator, sid, info, hub_mid) -> None:
        super().__init__(coordinator, f"valve_{sid}_estado", "Estado (crudo D01)")
        self._sid = sid
        self._attr_unique_id = f"homgar_valve_{sid}_estado"
        self._attr_device_info = valve_device_info(sid, info, hub_mid)

    @property
    def native_value(self):
        v = (self.coordinator.data or {}).get("valves", {}).get(self._sid)
        return None if v is None else (v.get("d01") or "sin dato")


class ValveFirmware(HomgarEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, sid, info, hub_mid) -> None:
        super().__init__(coordinator, f"valve_{sid}_fw", "Firmware")
        self._sid = sid
        self._attr_unique_id = f"homgar_valve_{sid}_fw"
        self._attr_device_info = valve_device_info(sid, info, hub_mid)

    @property
    def native_value(self):
        v = (self.coordinator.data or {}).get("valves", {}).get(self._sid)
        return None if v is None else (v["info"].get("softVer") or None)
