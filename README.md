# Homgar / RainPoint para Home Assistant

Integración **local en tu Home Assistant** para los sistemas de riego **Homgar / RainPoint**
(hubs WiFi y válvulas/temporizadores). Habla directamente con la nube de Homgar
usando tu cuenta de la app, sin depender de ningún puente externo.

Se añade desde **Ajustes → Dispositivos y servicios → Añadir integración → Homgar**
e inicia sesión con el correo y la contraseña de la app.

## Qué crea

Por cada hub y cada válvula aparece un dispositivo con sus entidades:

- **Hub** (p. ej. `HWG0538WRF`): `Conectado`, `Señal` (RSSI, dBm), `Firmware`.
- **Válvula** (p. ej. `WT-07W` / `HTV0535FRF`):
  - `Riego` — **interruptor**: enciende/apaga el riego (abre/cierra la válvula).
  - `Duración riego` — **número ajustable**: tiempo de riego que usa el interruptor
    al encenderse (por defecto 60; se conserva entre reinicios).
  - `Conectado`.
  - `Estado (crudo D01)` — trama de estado en crudo (diagnóstico).
  - `Firmware`.

El estado abierto/cerrado del interruptor se obtiene del estado real del aparato.

## Instalación

### HACS (recomendado)
1. HACS → Integraciones → menú ⋮ → *Repositorios personalizados*.
2. Añade `https://github.com/lindehasseasy/ha-homgar` como *Integration*.
3. Instala **Homgar / RainPoint** y reinicia Home Assistant.

### Manual
Copia `custom_components/homgar` dentro de la carpeta `custom_components` de tu
configuración de Home Assistant y reinicia.

## Configuración

| Campo | Ejemplo | Notas |
|-------|---------|-------|
| Correo o teléfono | `tucuenta@correo.com` | el de la app Homgar |
| Contraseña | — | se guarda en tu Home Assistant |
| Código de área | `34` | España = 34 |
| ISO país | `ES` | |
| Idioma | `es` | |
| Servidor | `region03.homgarus.com` | según tu región |

## Limitación importante: sesión única

La nube de Homgar sólo admite **una sesión activa por cuenta**. Si abres la app del
móvil, Home Assistant pierde la sesión (y al revés). Esta integración guarda tus
credenciales y **vuelve a entrar sola**, así que Home Assistant recupera el control
en el siguiente refresco. Si quieres usar la app y Home Assistant a la vez sin que
se peleen, crea una **segunda cuenta Homgar** e invítala a tu casa/hogar; usa esa
cuenta sólo para Home Assistant.

## Aviso

Proyecto independiente, sin relación con Homgar ni RainPoint. Marcas de sus
respectivos dueños. Úsalo bajo tu responsabilidad.

## Licencia

MIT — ver [LICENSE](LICENSE).
