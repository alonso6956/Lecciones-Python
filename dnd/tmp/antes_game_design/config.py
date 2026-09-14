import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path


APP_NAME = "Dungeon"


def resource_path(nombre):
    """Localiza recursos tanto en código fuente como dentro de PyInstaller."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / nombre


@dataclass(frozen=True)
class Configuracion:
    entorno: str
    host: str
    port: int
    debug: bool
    open_browser: bool
    request_logging: bool
    web_dir: Path
    data_dir: Path


def cargar_configuracion():
    entorno_predeterminado = "production" if getattr(sys, "frozen", False) else "development"
    entorno = os.getenv("DUNGEON_ENV", entorno_predeterminado).lower()
    if entorno not in {"development", "production"}:
        entorno = entorno_predeterminado

    with resource_path("config.json").open(encoding="utf-8") as archivo:
        datos = json.load(archivo)[entorno]

    if entorno == "production":
        raiz_datos = Path(os.getenv("LOCALAPPDATA", Path.home())) / APP_NAME
    else:
        raiz_datos = Path(__file__).resolve().parent / ".local"
    raiz_datos.mkdir(parents=True, exist_ok=True)

    return Configuracion(
        entorno=entorno,
        host=datos["host"],
        port=int(os.getenv("DUNGEON_PORT", datos["port"])),
        debug=bool(datos["debug"]),
        open_browser=bool(datos["open_browser"]),
        request_logging=bool(datos["request_logging"]),
        web_dir=resource_path("web"),
        data_dir=raiz_datos,
    )
