"""Config flow: entra con email + contrasena de Homgar (+ re-autenticacion)."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HomgarApi, HomgarAuthError, gen_device_id
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
    DEFAULT_AREA_CODE,
    DEFAULT_HOST,
    DEFAULT_ISO,
    DEFAULT_LANGUAGE,
    DEFAULT_PORT,
    DOMAIN,
)


async def _try_login(hass, host, email, password, area, iso, lang):
    """Devuelve (device_id, token, refresh) o lanza HomgarAuthError/Exception."""
    device_id = gen_device_id()
    session = async_get_clientsession(hass)
    api = HomgarApi(session, host, DEFAULT_PORT, device_id)
    await api.login(email, password, area, iso, lang)
    return device_id, api.token, api.refresh_token


class HomgarConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._reauth_entry: ConfigEntry | None = None

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            await self.async_set_unique_id(email.lower())
            self._abort_if_unique_id_configured()
            try:
                device_id, token, refresh = await _try_login(
                    self.hass, user_input[CONF_HOST], email, user_input[CONF_PASSWORD],
                    user_input[CONF_AREA_CODE].strip(), user_input[CONF_ISO].strip(),
                    user_input[CONF_LANGUAGE].strip(),
                )
            except HomgarAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Homgar ({email})",
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_AREA_CODE: user_input[CONF_AREA_CODE].strip(),
                        CONF_ISO: user_input[CONF_ISO].strip(),
                        CONF_LANGUAGE: user_input[CONF_LANGUAGE].strip(),
                        CONF_DEVICE_ID: device_id,
                        CONF_TOKEN: token,
                        CONF_REFRESH_TOKEN: refresh,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_AREA_CODE, default=DEFAULT_AREA_CODE): str,
                vol.Required(CONF_ISO, default=DEFAULT_ISO): str,
                vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): str,
                vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._reauth_entry
        assert entry is not None
        if user_input is not None:
            try:
                device_id, token, refresh = await _try_login(
                    self.hass, entry.data.get(CONF_HOST, DEFAULT_HOST),
                    entry.data[CONF_EMAIL], user_input[CONF_PASSWORD],
                    entry.data.get(CONF_AREA_CODE, DEFAULT_AREA_CODE),
                    entry.data.get(CONF_ISO, DEFAULT_ISO),
                    entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                )
            except HomgarAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={
                        **entry.data,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_DEVICE_ID: device_id,
                        CONF_TOKEN: token,
                        CONF_REFRESH_TOKEN: refresh,
                    },
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={"email": entry.data.get(CONF_EMAIL, "")},
            errors=errors,
        )
