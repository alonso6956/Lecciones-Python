"""Carga el catálogo JSON y fabrica objetos de dominio inmutables."""

import json
import sys
from pathlib import Path

from item import Arma, Armadura, Consumible, Material, Secundario


ALIASES_LEGACY = {
    "espada_escudo_hierro": "espada_hierro",
    "Espada y escudo": "espada_hierro",
    "Espada y escudo de hierro": "espada_hierro",
}


def _ruta_recurso(nombre):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / nombre


class ItemFactory:
    def __init__(self, ruta_catalogo=None):
        ruta = Path(ruta_catalogo) if ruta_catalogo else _ruta_recurso("items.json")
        with ruta.open(encoding="utf-8") as archivo:
            entradas = json.load(archivo)["items"]
        self._datos = {entrada["id"]: entrada for entrada in entradas}
        self._ids_por_nombre = {
            entrada["nombre"]: entrada["id"] for entrada in entradas
        }

    def crear(self, identificador):
        identificador = ALIASES_LEGACY.get(identificador, identificador)
        item_id = self._ids_por_nombre.get(identificador, identificador)
        try:
            datos = dict(self._datos[item_id])
        except KeyError as error:
            raise ValueError(f"El ítem {identificador!r} no existe.") from error
        clase = datos.pop("clase")
        if clase == "arma":
            datos["ataque"] = tuple(datos["ataque"])
            dos_manos = datos.pop("dos manos", False)
            if not isinstance(dos_manos, bool):
                raise ValueError(
                    f"El campo 'dos manos' de {datos['nombre']!r} debe ser booleano."
                )
            datos["dos_manos"] = dos_manos
            return Arma(**datos)
        if clase == "secundario":
            return Secundario(**datos)
        if clase == "armadura":
            return Armadura(**datos)
        if clase == "consumible":
            return Consumible(**datos)
        if clase == "material":
            return Material(**datos)
        raise ValueError(f"La clase de ítem {clase!r} no está soportada.")

    def todos(self):
        return [self.crear(item_id) for item_id in self._datos]


item_factory = ItemFactory()
