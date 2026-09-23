"""Cliente async de la nube Homgar / RainPoint para Home Assistant.

Habla la misma API REST que la app oficial: host regional homgarus.com, cada
peticion firmada con X-Signature = HmacMD5. Login por email+contrasena (la
contrasena se envia como MD5, igual que la app). El token de sesion se renueva
solo con el refreshToken.

Solo LECTURA de estado. No implementa control de riego a proposito.
"""
from __future__ import annotations

import hashlib
import hmac
import random
import re
import string
import time
import uuid

import aiohttp

from .const import APP_VERSION, SIGN_SECRET


class HomgarAuthError(Exception):
    """Credenciales invalidas o token no renovable."""


class HomgarApiError(Exception):
    """Error generico de la API."""


def md5_hex(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def gen_device_id() -> str:
    """Un deviceId estable para esta instalacion (como el que crea la app)."""
    return "ha-" + uuid.uuid4().hex


class HomgarApi:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        device_id: str,
        token: str = "",
        refresh_token: str = "",
        email: str = "",
        password: str = "",
        area_code: str = "",
        isocode: str = "",
        language: str = "",
    ) -> None:
        self._session = session
        self._base = f"https://{host}:{port}"
        self._device_id = device_id
        self._token = token
        self._refresh_token = refresh_token
        # credenciales para re-login automatico (la nube Homgar es de una sola
        # sesion: si el usuario abre la app, el token de HA muere; con esto HA
        # vuelve a entrar solo).
        self._email = email
        self._password = password
        self._area_code = area_code
        self._isocode = isocode
        self._language = language

    @property
    def token(self) -> str:
        return self._token

    @property
    def refresh_token(self) -> str:
        return self._refresh_token

    @property
    def device_id(self) -> str:
        return self._device_id

    # ---------- firma ----------
    def _headers(self, with_body: bool = False) -> dict[str, str]:
        ts = int(time.time())
        nonce = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(24))
        digits = re.sub(r"[^0-9]", "", self._device_id)
        msg = f"appCode=1&deviceId={self._device_id}&nonce={nonce}&timestamp={ts}&{digits}{ts}"
        sig = hmac.new(SIGN_SECRET, msg.encode(), hashlib.md5).hexdigest()
        h = {
            "X-Device-ID": self._device_id,
            "X-Signature": sig,
            "X-Timestamp": str(ts),
            "X-Nonce": nonce,
            "lang": "es",
            "version": APP_VERSION,
            "appCode": "1",
            "sceneType": "1",
            "User-Agent": "okhttp/4.9.2",
        }
        if self._token:
            h["auth"] = self._token
        if with_body:
            h["Content-Type"] = "application/json; charset=utf-8"
        return h

    async def _call(self, method: str, path: str, body=None, _retry: bool = True):
        headers = self._headers(body is not None)
        async with self._session.request(
            method, self._base + path, json=body, headers=headers,
            timeout=aiohttp.ClientTimeout(total=25),
        ) as resp:
            data = await resp.json(content_type=None)
        code = data.get("code")
        if code == 1001 and _retry:  # NOT_TOKEN -> refrescar o re-login
            if not await self._recuperar_sesion():
                return data
            return await self._call(method, path, body, _retry=False)
        return data

    async def _recuperar_sesion(self) -> bool:
        """Intenta refrescar el token; si no, re-login con las credenciales."""
        if self._refresh_token:
            try:
                await self.refresh()
                return True
            except HomgarAuthError:
                pass
        if self._email and self._password:
            try:
                await self.login(self._email, self._password, self._area_code,
                                 self._isocode, self._language)
                return True
            except HomgarAuthError:
                return False
        return False

    async def control_work_mode(self, mid, product_key, device_name, addr,
                                port, mode: int, duration: int) -> dict:
        """Abre/cierra un puerto de valvula. mode=1 abrir (con duration),
        mode=0 cerrar. Reproduce el comando real de la app (capturado)."""
        body = {
            "deviceName": device_name,
            "productKey": product_key,
            "mid": str(mid),
            "addr": addr,
            "port": port,
            "mode": mode,
            "duration": duration,
            "param": "",
        }
        return await self._call("POST", "/app/device/controlWorkMode", body)

    # ---------- auth ----------
    async def login(
        self, email: str, password: str, area_code: str, isocode: str, language: str
    ) -> None:
        """Entra con email+contrasena y guarda token/refreshToken."""
        body = {
            "areaCode": area_code,
            "phoneOrEmail": email,
            "password": md5_hex(password),
            "pushId": "",
            "deviceType": 1,
            "deviceModel": "HomeAssistant",
            "language": language,
            "isocode": isocode,
            "deviceId": self._device_id,
            "osVersion": 30,
        }
        data = await self._call("POST", "/app/auth/login", body, _retry=False)
        if data.get("code") != 0:
            raise HomgarAuthError(data.get("msg") or f"login code {data.get('code')}")
        d = data.get("data") or {}
        self._token = d.get("token", "")
        self._refresh_token = d.get("refreshToken", "")
        if not self._token:
            raise HomgarAuthError("login sin token en la respuesta")

    async def refresh(self) -> None:
        data = await self._call(
            "POST", "/auth/basic/app/token/refresh",
            {"refreshToken": self._refresh_token}, _retry=False,
        )
        d = data.get("data") or {}
        if not d.get("token"):
            raise HomgarAuthError("no se pudo renovar el token")
        self._token = d["token"]
        self._refresh_token = d.get("refreshToken", self._refresh_token)

    # ---------- lecturas ----------
    async def homes(self) -> list[dict]:
        data = await self._call("GET", "/app/member/appHome/list")
        return data.get("data") or []

    async def devices(self, hid) -> list[dict]:
        data = await self._call("GET", f"/app/device/getDeviceByHid?hid={hid}")
        return data.get("data") or []

    async def device_status(self, hub_mid) -> dict:
        data = await self._call("GET", f"/app/device/getDeviceStatus?mid={hub_mid}")
        return data.get("data") or {}
