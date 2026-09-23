"""Integracion Homgar / RainPoint (riego) para Home Assistant."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HomgarApi
from .const import (
    CONF_AREA_CODE,
    CONF_DEVICE_ID,
    CONF_EMAIL,
    CONF_HOST,
    CONF_ISO,
    CONF_LANGUAGE,
    CONF_PASSWORD,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DOMAIN,
)
from .coordinator import HomgarCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    api = HomgarApi(
        session,
        entry.data.get(CONF_HOST, DEFAULT_HOST),
        DEFAULT_PORT,
        entry.data[CONF_DEVICE_ID],
        token=entry.data.get(CONF_TOKEN, ""),
        refresh_token=entry.data.get(CONF_REFRESH_TOKEN, ""),
        email=entry.data.get(CONF_EMAIL, ""),
        password=entry.data.get(CONF_PASSWORD, ""),
        area_code=entry.data.get(CONF_AREA_CODE, ""),
        isocode=entry.data.get(CONF_ISO, ""),
        language=entry.data.get(CONF_LANGUAGE, ""),
    )
    coordinator = HomgarCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    # si el token rotó durante el primer refresco, guárdalo
    if api.token != entry.data.get(CONF_TOKEN) or api.refresh_token != entry.data.get(
        CONF_REFRESH_TOKEN
    ):
        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_TOKEN: api.token,
                CONF_REFRESH_TOKEN: api.refresh_token,
            },
        )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
