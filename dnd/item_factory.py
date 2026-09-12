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
        self._instancias = {}
        with _ruta_recurso("crafting.json").open(encoding="utf-8") as archivo:
            crafting = json.load(archivo)
        for grupo, prefijo in (("materiales", "material_"), ("afijos", "")):
            for clave, entrada in crafting[grupo].items():
                item_id = prefijo + clave
                self._datos[item_id] = {"id": item_id, "nombre": entrada["nombre"],
                    "clase": "material", "precio": 0, "descripcion": "Recurso de crafteo obtenido en Dungeon."}

    def registrar_instancia(self, datos):
        """Las instancias se referencian por UUID, nunca por su nombre editable."""
        from copy import deepcopy
        from uuid import UUID
        import math
        if not isinstance(datos, dict):
            raise ValueError("Los datos de la instancia no son válidos.")
        datos = deepcopy(datos)
        identificador = datos.get("id", "")
        if not isinstance(identificador, str) or not identificador.startswith("craft_"):
            raise ValueError("ID de equipo procedural inválido.")
        UUID(identificador[6:])
        arma = self._crear_instancia(datos)
        if type(arma.tier) is not int or not 1 <= arma.tier <= 5:
            raise ValueError("Tier procedural inválido.")
        if type(arma.precio) is not int or arma.precio < 0:
            raise ValueError("Valor de mercado inválido.")
        numeros = [arma.peso, arma.durabilidad]
        if isinstance(arma, Arma):
            if len(arma.ataque) != 2 or any(type(v) is not int for v in arma.ataque) or not 0 < arma.ataque[0] <= arma.ataque[1]:
                raise ValueError("Estadísticas de arma procedural inválidas.")
            numeros += [*arma.ataque, arma.velocidad, arma.critico, arma.penetracion, *arma.distribucion]
            if not 0 <= arma.critico <= 1 or arma.velocidad <= 0:
                raise ValueError("Probabilidad o velocidad inválidas.")
        elif isinstance(arma, Armadura):
            if arma.slot not in {"casco", "pecho", "brazos", "piernas"} or type(arma.defensa) is not int or arma.defensa < 1:
                raise ValueError("Armadura procedural inválida.")
            numeros += [arma.defensa, *arma.bonificaciones.values()]
        else:
            numeros += [arma.probabilidad_bloqueo, arma.porcentaje_dano_bloqueado, *arma.bonificaciones.values()]
            if arma.tipo_secundario != "escudo" or not 0 <= arma.probabilidad_bloqueo <= 1 or not 0 <= arma.porcentaje_dano_bloqueado <= 1:
                raise ValueError("Escudo procedural inválido.")
        if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in numeros):
            raise ValueError("Las estadísticas del equipo deben ser números finitos no negativos.")
        self._instancias[identificador] = datos
        return arma

    @staticmethod
    def _crear_instancia(datos):
        # Las armas previas no tenían discriminador: conserva su formato.
        if "tipo_arma" in datos:
            return Arma(**{**datos, "ataque": tuple(datos["ataque"]), "distribucion": tuple(datos.get("distribucion", ()))})
        if "slot" in datos:
            return Armadura(**datos)
        if "tipo_secundario" in datos:
            return Secundario(**datos)
        raise ValueError("Tipo de equipo procedural inválido.")

    def datos_instancia(self, identificador):
        from copy import deepcopy
        return deepcopy(self._instancias.get(identificador))

    def permite_vault(self, identificador):
        item = self.crear(identificador)
        datos = self._datos.get(item.id, {})
        return datos.get("vault_allowed", True) and not datos.get("bound") and not datos.get("quest_locked")

    def crear(self, identificador):
        if not isinstance(identificador, str):
            raise ValueError("El identificador del objeto debe ser texto.")
        if identificador in self._instancias:
            datos = self._instancias[identificador]
            return self._crear_instancia(datos)
        identificador = ALIASES_LEGACY.get(identificador, identificador)
        item_id = self._ids_por_nombre.get(identificador, identificador)
        try:
            datos = dict(self._datos[item_id])
        except KeyError as error:
            raise ValueError(f"El ítem {identificador!r} no existe.") from error
        clase = datos.pop("clase")
        for politica in ("vault_allowed", "quest_locked", "bound", "stackable", "max_stack"):
            datos.pop(politica, None)
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
