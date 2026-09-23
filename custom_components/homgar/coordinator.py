"""Coordinador de datos: lee la nube Homgar cada UPDATE_INTERVAL segundos."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HomgarApi, HomgarAuthError
from .const import DEFAULT_DURATION, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


def _parse_status(status: dict):
    """subDeviceStatus -> (dps, rssi, online). state = 'online,RSSI'."""
    dps: dict[str, str] = {}
    for it in status.get("subDeviceStatus", []) or []:
        dps[it.get("id")] = it.get("value")
    rssi = None
    st = dps.get("state")
    if st:
        parts = str(st).split(",")
        if len(parts) >= 2:
            try:
                rssi = int(parts[1])
            except ValueError:
                rssi = None
    online = str(dps.get("connected", "")).strip() == "1"
    return dps, rssi, online


def _watering_from_d01(d01):
    """Valvula regando? Del DP D01 (hex). Confirmado empiricamente contra el
    aparato real: byte 7 bit 0 = 1 abierto (0x21), 0 cerrado (0x20)."""
    if not d01 or "#" not in str(d01):
        return None
    hexs = str(d01).split("#", 1)[1]
    try:
        b = bytes.fromhex(hexs)
    except ValueError:
        return None
    if len(b) < 8:
        return None
    return bool(b[7] & 0x01)


class HomgarCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: HomgarApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Homgar",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.api = api
        self.entry = entry
        # duracion de riego (min) por valvula, ajustable desde la entidad numero
        self.durations: dict = {}

    async def _async_update_data(self):
        try:
            hubs: dict = {}
            valves: dict = {}
            for home in await self.api.homes():
                hid = home.get("hid")
                for hub in await self.api.devices(hid):
                    mid = hub.get("mid")
                    status = await self.api.device_status(mid)
                    dps, rssi, online = _parse_status(status)
                    hubs[mid] = {
                        "info": hub,
                        "home": home,
                        "rssi": rssi,
                        "online": online,
                        "dps": dps,
                    }
                    for sub in hub.get("subDevices") or []:
                        sid = sub.get("sid")
                        addr = sub.get("addr")
                        d01 = dps.get(f"D{addr:02d}") if isinstance(addr, int) else None
                        valves[sid] = {
                            "info": sub,
                            "hub_mid": mid,
                            "online": online,
                            "d01": d01,
                            "watering": _watering_from_d01(d01),
                            # datos para el control (endpoint controlWorkMode)
                            "product_key": hub.get("productKey"),
                            "device_name": hub.get("deviceName"),
                            "addr": addr,
                            "port": sub.get("portNumber") or addr,
                        }
            return {"hubs": hubs, "valves": valves}
        except HomgarAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"error leyendo la nube Homgar: {err}") from err

    async def set_valve(self, sid, on: bool, duration: int | None = None):
        """Abre (on, riego 'duration') o cierra (off) una valvula."""
        v = (self.data or {}).get("valves", {}).get(sid)
        if not v:
            return
        hub = (self.data or {}).get("hubs", {}).get(v["hub_mid"], {})
        mid = hub.get("info", {}).get("mid", v["hub_mid"])
        if duration is None:
            duration = self.durations.get(sid, DEFAULT_DURATION)
        mode = 1 if on else 0
        dur = duration if on else 0
        await self.api.control_work_mode(
            mid, v["product_key"], v["device_name"], v["addr"], v["port"], mode, dur
        )
        await self.async_request_refresh()
