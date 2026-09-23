"""Entidad base y helpers de device_info para Homgar."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import HomgarCoordinator


def hub_device_info(mid, info: dict) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"hub_{mid}")},
        name=(info.get("name") or f"Hub {mid}").strip(),
        manufacturer=MANUFACTURER,
        model=f"{info.get('model')} ({info.get('displayModel')})",
        sw_version=str(info.get("softVer") or ""),
    )


def valve_device_info(sid, info: dict, hub_mid) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"valve_{sid}")},
        name=(info.get("name") or f"Valvula {sid}").strip(),
        manufacturer=MANUFACTURER,
        model=f"{info.get('model')} ({info.get('displayModel')})",
        sw_version=str(info.get("softVer") or ""),
        via_device=(DOMAIN, f"hub_{hub_mid}"),
    )


class HomgarEntity(CoordinatorEntity[HomgarCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: HomgarCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
