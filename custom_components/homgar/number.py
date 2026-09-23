"""Numero ajustable: duracion del riego al encender el interruptor."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DEFAULT_DURATION, DOMAIN
from .entity import HomgarEntity, valve_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {"valves": {}}
    entities = [
        ValveDuration(coordinator, sid, v["info"], v["hub_mid"])
        for sid, v in data["valves"].items()
    ]
    async_add_entities(entities)


class ValveDuration(HomgarEntity, NumberEntity, RestoreEntity):
    """Minutos de riego que usa el interruptor 'Riego' al encenderse."""

    _attr_icon = "mdi:timer-cog"
    _attr_native_min_value = 1
    _attr_native_max_value = 1440
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "min"

    def __init__(self, coordinator, sid, info, hub_mid) -> None:
        super().__init__(coordinator, f"valve_{sid}_duracion", "Duracion riego")
        self._sid = sid
        self._attr_unique_id = f"homgar_valve_{sid}_duracion"
        self._attr_device_info = valve_device_info(sid, info, hub_mid)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state not in (None, "unknown", "unavailable"):
            try:
                self.coordinator.durations[self._sid] = int(float(last.state))
            except (ValueError, TypeError):
                pass

    @property
    def native_value(self) -> float:
        return self.coordinator.durations.get(self._sid, DEFAULT_DURATION)

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.durations[self._sid] = int(value)
        self.async_write_ha_state()
