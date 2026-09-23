"""Constantes de la integracion Homgar / RainPoint."""
from __future__ import annotations

DOMAIN = "homgar"

# API de la nube Homgar (reverse de la app oficial com.baldr.homgar).
# El host es regional; region03 = cuentas con areaCode 34 (Espana). Se puede
# cambiar en las opciones si tu cuenta es de otra region.
DEFAULT_HOST = "region03.homgarus.com"
DEFAULT_PORT = 1443
SIGN_SECRET = b"5963618179b5782a255f576e5c861921"
APP_VERSION = "2.25.2084"

# Config entry
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_AREA_CODE = "area_code"
CONF_ISO = "isocode"
CONF_LANGUAGE = "language"
CONF_HOST = "host"
CONF_DEVICE_ID = "device_id"
CONF_TOKEN = "token"
CONF_REFRESH_TOKEN = "refresh_token"

DEFAULT_AREA_CODE = "34"
DEFAULT_ISO = "ES"
DEFAULT_LANGUAGE = "es"

UPDATE_INTERVAL = 60  # segundos entre lecturas de la nube
DEFAULT_DURATION = 60  # duracion de riego por defecto al encender (ajustable)

MANUFACTURER = "Homgar / RainPoint"
