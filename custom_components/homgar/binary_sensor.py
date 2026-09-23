"""Binary sensors: conectividad del hub y de cada valvula."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import HomgarEntity, hub_device_info, valve_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {"hubs": {}, "valves": {}}
    entities: list[BinarySensorEntity] = []
    for mid, hub in data["hubs"].items():
        entities.append(HubOnline(coordinator, mid, hub["info"]))
    for sid, valve in data["valves"].items():
        entities.append(ValveOnline(coordinator, sid, valve["info"], valve["hub_mid"]))
    async_add_entities(entities)


class HubOnline(HomgarEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, mid, info) -> None:
        super().__init__(coordinator, f"hub_{mid}_online", "Conectado")
        self._mid = mid
        self._attr_unique_id = f"homgar_hub_{mid}_online"
        self._attr_device_info = hub_device_info(mid, info)

    @property
    def is_on(self) -> bool | None:
        hub = (self.coordinator.data or {}).get("hubs", {}).get(self._mid)
        return None if hub is None else bool(hub["online"])


class ValveOnline(HomgarEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, sid, info, hub_mid) -> None:
        super().__init__(coordinator, f"valve_{sid}_online", "Conectado")
        self._sid = sid
        self._attr_unique_id = f"homgar_valve_{sid}_online"
        self._attr_device_info = valve_device_info(sid, info, hub_mid)

    @property
    def is_on(self) -> bool | None:
        v = (self.coordinator.data or {}).get("valves", {}).get(self._sid)
        return None if v is None else bool(v["online"])
