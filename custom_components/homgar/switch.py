"""Interruptor de riego: abre/cierra la valvula (controlWorkMode)."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import HomgarEntity, valve_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {"valves": {}}
    entities = [
        ValveSwitch(coordinator, sid, v["info"], v["hub_mid"])
        for sid, v in data["valves"].items()
    ]
    async_add_entities(entities)


class ValveSwitch(HomgarEntity, SwitchEntity):
    _attr_icon = "mdi:sprinkler"

    def __init__(self, coordinator, sid, info, hub_mid) -> None:
        super().__init__(coordinator, f"valve_{sid}_riego", "Riego")
        self._sid = sid
        self._attr_unique_id = f"homgar_valve_{sid}_riego"
        self._attr_device_info = valve_device_info(sid, info, hub_mid)

    @property
    def is_on(self) -> bool | None:
        v = (self.coordinator.data or {}).get("valves", {}).get(self._sid)
        return None if v is None else v.get("watering")

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.set_valve(self._sid, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.set_valve(self._sid, False)
