"""Personajes confirmados al crearse, avanzar de habitación, comprar o morir.

Las expediciones usan copias: nunca alteran el checkpoint del roster en memoria.
Los slots antiguos se importan sin modificar sus archivos originales.
"""

from copy import deepcopy
from uuid import NAMESPACE_URL, uuid5

from character import Personaje
from inventario import Inventario
from item import Arma
from item_factory import item_factory
from persistence import ErrorGuardado, GestorGuardado
from progression import CLASES
from item_container import SharedVault


MENSAJE_BLOQUEO = "Necesitas crear y subir de nivel al menos a 3 personajes en el calabozo"


def serializar_personaje(jugador):
    inventario = jugador.inventario.serializar()
    return {
        "id": jugador.id, "nombre": jugador.nombre, "nivel": jugador.nivel,
        "arma_equipada": inventario["arma_equipada"],
        "estadisticas": {k: getattr(jugador, k) for k in ("fuerza", "destreza", "constitucion")},
        "clase": jugador.clase, "chispa": jugador.chispa,
        "inventario": [{"id": k, "cantidad": v} for k, v in inventario["items"].items()],
        "equipamiento": inventario["equipamiento"],
        "version_equipamiento": 2,
        "instancias": inventario["instancias"], "custom": inventario["custom"],
        "capacidad_inventario": inventario["capacidad"], "crafting_exp": jugador.crafting_exp,
        "exp": jugador.exp, "oro": jugador.oro,
        "puntos_estadistica": jugador.puntos_estadistica,
        "puntos_habilidad": jugador.puntos_habilidad,
        "habilidades": dict(jugador.habilidades),
    }


def deserializar_personaje(datos):
    """Valida primero y reconstruye vida/equipo; no restaura datos de la run."""
    try:
        stats = datos["estadisticas"]
        if any(type(stats[k]) is not int or stats[k] < 1 for k in ("fuerza", "destreza", "constitucion")):
            raise ValueError("Estadísticas inválidas.")
        if not isinstance(datos["id"], str) or not datos["id"]:
            raise ValueError("ID inválido.")
        if not isinstance(datos["nombre"], str) or not datos["nombre"].strip():
            raise ValueError("Nombre inválido.")
        for custom in datos.get("custom", {}).values():
            item_factory.registrar_instancia(custom)
        arma = item_factory.crear(datos["arma_equipada"])
        if not isinstance(arma, Arma):
            raise ValueError("Arma inválida.")
        jugador = Personaje(datos["nombre"], arma.id, stats)
        jugador.id = datos["id"]
        jugador.crafting_exp = datos.get("crafting_exp", 0)
        if type(jugador.crafting_exp) is not int or jugador.crafting_exp < 0:
            raise ValueError("Experiencia de crafteo inválida.")
        for k in ("nivel", "exp", "oro", "puntos_estadistica", "puntos_habilidad"):
            valor = datos.get(k, 1 if k == "nivel" else 0)
            if type(valor) is not int or valor < (1 if k == "nivel" else 0):
                raise ValueError("Progresión inválida.")
            setattr(jugador, k, valor)
        if jugador.nivel > Personaje.NIVEL_MAXIMO:
            raise ValueError("Nivel inválido.")
        jugador.clase = datos.get("clase")
        jugador.chispa = datos.get("chispa")
        if jugador.clase is not None and (jugador.clase not in CLASES or jugador.nivel < 10):
            raise ValueError("Clase inválida.")
        if jugador.chispa is not None and (not isinstance(jugador.chispa, str) or not jugador.chispa or jugador.nivel < 30):
            raise ValueError("Chispa inválida.")
        entradas = datos["inventario"]
        items = {e["id"]: e["cantidad"] for e in entradas}
        if len(items) != len(entradas) or any(type(v) is not int or v < 1 for v in items.values()):
            raise ValueError("Inventario inválido.")
        jugador.inventario = Inventario.deserializar({
            "items": items, "equipamiento": datos["equipamiento"], "arma_equipada": arma.id,
            "custom": datos.get("custom", {}), "capacidad": datos.get("capacidad_inventario"),
            "version_equipamiento": datos.get("version_equipamiento", 1),
            **({"instancias": datos["instancias"]} if "instancias" in datos else {}),
        })
        if not jugador.inventario.arma_equipada or jugador.inventario.arma_equipada.id != arma.id:
            raise ValueError("Equipo inconsistente.")
        for item_id in jugador.inventario.serializar()["equipamiento"].values():
            if item_id and not item_factory.crear(item_id).cumple_requisitos(jugador):
                raise ValueError("El equipo no cumple los requisitos.")
        jugador.habilidades = {}
        from habilidades import habilidad_factory
        for habilidad_id, nivel in datos.get("habilidades", {}).items():
            habilidad = habilidad_factory.crear(habilidad_id)
            if type(nivel) is not int or not 0 <= nivel <= habilidad.nivel_maximo:
                raise ValueError("Habilidad inválida.")
            jugador.habilidades[habilidad_id] = nivel
        jugador.salud_maxima = jugador.calcular_salud_maxima()
        jugador.hp = jugador.salud_maxima
        return jugador
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        raise ErrorGuardado(f"Personaje guardado inválido: {error}") from error


def migrar_personaje(estado, identificador):
    datos = estado["jugador"]
    if "estadisticas" in datos:
        return serializar_personaje(deserializar_personaje(datos))
    arma_original = datos["arma"]
    jugador = Personaje(datos["nombre"], arma_original, {k: int(datos[k]) for k in ("fuerza", "destreza", "constitucion")})
    jugador.id = str(uuid5(NAMESPACE_URL, identificador))
    inventario = deepcopy(datos.get("inventario"))
    if isinstance(inventario, dict):
        jugador.inventario = Inventario.deserializar(inventario)
    elif isinstance(inventario, list):
        for nombre in inventario:
            jugador.inventario.recolectar(nombre)
    if arma_original in {"Espada y escudo", "Espada y escudo de hierro"}:
        if not jugador.inventario.cantidad("escudo_hierro"):
            jugador.inventario.recolectar("escudo_hierro")
        jugador.inventario.equipar("escudo_hierro", jugador)
    for k in ("nivel", "exp", "oro", "puntos_estadistica", "puntos_habilidad"):
        setattr(jugador, k, int(datos.get(k, getattr(jugador, k))))
    # Los puntos antes invertidos en habilidades de arma quedan disponibles.
    jugador.puntos_habilidad += sum(max(0, int(v)) for v in datos.get("habilidades", {}).values())
    if "puntos_estadistica" not in datos and estado.get("fase") == "nivel":
        jugador.subir_nivel()
    return serializar_personaje(deserializar_personaje(serializar_personaje(jugador)))


class _ArchivoRoster(GestorGuardado):
    TOTAL_SLOTS = 1

    def _rutas(self, slot):
        self._validar_slot(slot)
        return self.directorio / "roster.json", self.directorio / "roster.backup.json"

    @staticmethod
    def _crear_resumen(estado, fecha):
        return {"fecha": fecha, "personajes": len(estado["roster"])}


class CharacterRoster:
    def __init__(self, directorio=None):
        self._personajes = []
        self.vault = SharedVault()
        self.avisos = []
        self.archivo = _ArchivoRoster(directorio) if directorio is not None else None
        if self.archivo and self.archivo.existe():
            estado = self.archivo.cargar(1)
            self.vault = SharedVault(estado.get("shared_vault"))
            entradas = estado.get("roster")
            if not isinstance(entradas, list):
                raise ErrorGuardado("El roster no contiene una lista de personajes.")
            self._personajes = [serializar_personaje(deserializar_personaje(d)) for d in entradas]
            if len({d["id"] for d in self._personajes}) != len(self._personajes):
                raise ErrorGuardado("El roster contiene IDs duplicados.")
        elif self.archivo:
            legacy = GestorGuardado(directorio)
            for slot in range(1, legacy.TOTAL_SLOTS + 1):
                if legacy.existe(slot):
                    try:
                        self._personajes.append(migrar_personaje(legacy.cargar(slot), f"{legacy.directorio.resolve()}/slot/{slot}"))
                    except (ErrorGuardado, ValueError, KeyError, TypeError) as error:
                        self.avisos.append(f"No se pudo importar el slot {slot}: {error}")

    @property
    def personajes(self):
        return deepcopy(self._personajes)

    @property
    def tactico_disponible(self):
        return len(self._personajes) >= 3

    def obtener(self, personaje_id):
        for datos in self._personajes:
            if datos["id"] == personaje_id:
                return deepcopy(datos)
        raise ErrorGuardado("El personaje no existe en el roster.")

    def save_to_disk(self, jugador, vault=None):
        datos = serializar_personaje(jugador)
        deserializar_personaje(datos)
        nuevos = self.personajes
        indice = next((i for i, d in enumerate(nuevos) if d["id"] == jugador.id), len(nuevos))
        if indice == len(nuevos):
            nuevos.append(datos)
        else:
            nuevos[indice] = datos
        identidades = [k for p in nuevos for k in p.get("instancias", {})]
        identidades.extend((vault or self.vault)._instancias)
        if len(identidades) != len(set(identidades)):
            raise ErrorGuardado("Una instancia no puede pertenecer a dos contenedores.")
        if self.archivo:
            self.archivo.guardar(1, {"roster": nuevos, "shared_vault": (vault or self.vault).serializar()})
        self._personajes = nuevos
        if vault is not None:
            self.vault = vault

    def descartar(self, personaje_id):
        """Confirma la eliminación en disco antes de actualizar la lista en memoria."""
        self.obtener(personaje_id)
        nuevos = [d for d in self.personajes if d["id"] != personaje_id]
        if self.archivo:
            self.archivo.guardar(1, {"roster": nuevos, "shared_vault": self.vault.serializar()})
        self._personajes = nuevos

    def listar_slots(self):
        """Adaptador de selección para clientes antiguos; ya no sobrescribe slots."""
        return [{"slot": i, "id": d["id"], "ocupado": True,
                 "resumen": {"personaje": d["nombre"], "nivel": d["nivel"], "habitacion": 1}}
                for i, d in enumerate(self._personajes, 1)]
