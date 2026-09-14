"""Preparación táctica sobre los modelos y el catálogo originales de Dungeon."""

from dataclasses import dataclass, field
from typing import Any

from character import Personaje
from enemies import crear_enemigo
from combat_stats import estadisticas_combate, defensa_total
from item_factory import item_factory
from item import Arma
from tactical_board import MANIOBRAS
from character_roster import deserializar_personaje
from progression import CLASES
from enemy_ai import PerfilIA


ROSTER = {
    "aria": {"nombre": "Aria", "rol": "Pícara", "stats": {"fuerza": 4, "destreza": 6, "constitucion": 5},
             "descripcion": "Personaje de prueba con estadísticas de Dungeon."},
    "bruno": {"nombre": "Bruno", "rol": "Guerrero", "stats": {"fuerza": 6, "destreza": 3, "constitucion": 7},
              "descripcion": "Personaje de prueba con estadísticas de Dungeon."},
    "cora": {"nombre": "Cora", "rol": "Tanque", "stats": {"fuerza": 3, "destreza": 2, "constitucion": 10},
             "descripcion": "Personaje de prueba con estadísticas de Dungeon."},
}

BUILDS = {
    "ofensiva": {"nombre": "Ofensiva", "ataque": 1.0, "resistencia_sangrado": 0.0,
                 "descripcion": "Estadísticas del personaje en Dungeon."},
    "adaptacion": {"nombre": "Adaptación", "ataque": 1.0, "resistencia_sangrado": 0.0,
                   "descripcion": "+25% ruptura del escudo; estadísticas del personaje en Dungeon."},
}

# Propiedades físicas del equipo. Ningún arma concede habilidades.
ARMAS = {
    "dagas_hierro": {"velocidad": 0, "ruptura": 0.5, "descripcion": "Ruptura x0,5."},
    "maza_hierro": {"velocidad": 0, "ruptura": 1.5, "descripcion": "Ruptura x1,5."},
    "espada_hierro": {"velocidad": 0, "ruptura": 0.5, "descripcion": "Ruptura x0,5."},
}
for _arma in item_factory.todos():
    if hasattr(_arma, "ataque"):
        ARMAS.setdefault(_arma.id, {"velocidad": 0, "ruptura": 0.5, "descripcion": "Equipo sin habilidades."})

PRIORIDADES = {
    "agresiva": {"nombre": "Agresiva", "reglas": ["unica", "vulnerable", "romper", "curar", "limpiar"],
                 "descripcion": "Habilidad única → objetivo vulnerable → ruptura → curación → limpieza."},
    "tactica": {"nombre": "Táctica", "reglas": ["limpiar", "curar", "romper", "unica", "vulnerable"],
                "descripcion": "Limpiar sangrado → curar bajo 55% HP → romper escudo → habilidad única → vulnerable."},
}


@dataclass(frozen=True)
class Seleccion:
    personaje_id: str
    build: str = "ofensiva"
    arma: str = "dagas_hierro"
    prioridad: str = "agresiva"
    maniobra: str = "ninguna"


@dataclass
class Actor:
    """Adaptador de combate: el modelo existente sigue siendo dueño de la vida."""

    id: str
    modelo: Any
    rol: str
    seleccion: Seleccion = None
    resistencia_sangrado: float = 0.0
    estados: dict = field(default_factory=dict)
    cooldowns: dict = field(default_factory=dict)
    habilidades_tacticas: tuple = ()
    unica: str = None
    roles_ia: tuple = ()
    linea_ia: str = "frontal"

    @property
    def ataque(self):
        datos = estadisticas_combate(self.modelo)
        return (datos["ataque_minimo"] + datos["ataque_maximo"]) / 2

    @property
    def defensa(self):
        return defensa_total(self.modelo)

    @property
    def velocidad(self):
        return self.modelo.velocidad

    @property
    def hp(self):
        return self.modelo.hp

    @hp.setter
    def hp(self, value):
        self.modelo.hp = max(0, min(self.hp_max, value))

    @property
    def hp_max(self):
        return self.modelo.salud_maxima

    @property
    def vivo(self):
        return self.hp > 0

    def estado(self):
        return {**estadisticas_combate(self.modelo), "id": self.id, "nombre": self.modelo.nombre, "rol": self.rol,
                "hp": round(self.hp, 2), "hp_max": self.hp_max,
                "ataque": round(self.ataque, 2), "defensa": self.defensa, "velocidad": self.velocidad,
                "nivel": getattr(self.modelo, "nivel", 1),
                "resistencia_sangrado": round(self.resistencia_sangrado * 100, 2),
                "estados": {key: dict(value) for key, value in self.estados.items()},
                "cooldowns": dict(self.cooldowns)}


@dataclass(frozen=True)
class Encuentro:
    id: str = "guardian_verdugo"
    raza: str = "Guardián"
    arquetipo: str = "Jefe"
    escudo: float = 105
    ventana_rondas: int = 2
    sangrado_pct: float = 0.04
    sangrado_duracion: int = 4
    sangrado_max: int = 4
    castigo: float = 155
    limite_rondas: int = 80
    perfil_ia: PerfilIA | None = None
    grupo: bool = False

    @property
    def ids_enemigos(self):
        return ["goblin_explorador", "esqueleto_guardia", "bandido_bruto"] if self.grupo else [self.id]

    def crear_enemigos(self):
        if not self.grupo:
            return [self.crear_jefe()]
        return [Actor(id, crear_enemigo(raza, tipo), tipo) for id, raza, tipo in zip(
            self.ids_enemigos, ("Goblin", "Esqueleto", "Bandido"), ("Rogue", "Guerrero", "Bárbaro"))]

    def __post_init__(self):
        if isinstance(self.perfil_ia, dict):
            object.__setattr__(self, "perfil_ia", PerfilIA(**self.perfil_ia))
        if self.perfil_ia is not None and not isinstance(self.perfil_ia, PerfilIA):
            raise ValueError("Perfil de IA inválido")
        if min(self.escudo, self.ventana_rondas, self.sangrado_duracion,
               self.sangrado_max, self.limite_rondas) <= 0:
            raise ValueError("Vida, escudo, duraciones y límite deben ser positivos.")
        if min(self.sangrado_pct, self.castigo) < 0:
            raise ValueError("Los valores de combate no pueden ser negativos.")

    def crear_jefe(self):
        return Actor(self.id, crear_enemigo(self.raza, self.arquetipo), "Jefe")

    def estado(self):
        from dataclasses import asdict
        if self.grupo:
            return {**asdict(self), "nombre": "Patrulla hostil", "es_jefe": False,
                    "enemigos": [a.estado() for a in self.crear_enemigos()]}
        return {**asdict(self), **self.crear_jefe().estado(), "es_jefe": True,
                "enemigos": [self.crear_jefe().estado()]}


class BuildManager:
    @staticmethod
    def validar(selecciones, roster=None):
        for datos in roster or []:
            for custom in datos.get("custom", {}).values():
                arma = item_factory.registrar_instancia(custom)
                if isinstance(arma, Arma):
                    ARMAS.setdefault(arma.id, {"velocidad": 0, "ruptura": 0.5, "descripcion": "Arma fabricada; mismas estadísticas que Dungeon."})
        catalogo = ROSTER if roster is None else {d["id"]: d for d in roster}
        ids = {s.personaje_id for s in selecciones}
        if not 3 <= len(selecciones) <= 6 or len(ids) != len(selecciones) or not ids.issubset(catalogo):
            raise ValueError("Selecciona entre 3 y 6 personajes, sin duplicados.")
        for s in selecciones:
            if s.build not in BUILDS or s.arma not in ARMAS or s.prioridad not in PRIORIDADES:
                raise ValueError("Build, arma o prioridad no válida.")
            if s.maniobra not in MANIOBRAS:
                raise ValueError("Maniobra de campo no válida.")
            if roster is not None:
                modelo = deserializar_personaje(catalogo[s.personaje_id])
                if not modelo.inventario.cantidad(s.arma) or not item_factory.crear(s.arma).cumple_requisitos(modelo):
                    raise ValueError("Solo puedes usar armas compradas por ese personaje y cuyos requisitos cumpla.")

    @classmethod
    def crear_party(cls, selecciones, roster=None):
        cls.validar(selecciones, roster)
        catalogo = ROSTER if roster is None else {d["id"]: d for d in roster}
        party = []
        for s in selecciones:
            datos = catalogo[s.personaje_id]
            if roster is None:
                # Fixtures del simulador aislado; nunca se usan en el servidor.
                modelo = Personaje(datos["nombre"], s.arma, dict(datos["stats"]))
                rol = datos["rol"]
            else:
                modelo = deserializar_personaje(datos)
                anterior = modelo.salud_maxima
                modelo.inventario.equipar(s.arma, modelo)
                modelo.recalcular_por_equipo(anterior)
                modelo.hp = modelo.salud_maxima
                rol = CLASES.get(modelo.clase, {}).get("nombre", "Sin clase")
            actor = Actor(s.personaje_id, modelo, rol, s)
            party.append(actor)
        return party


def preparacion_ofensiva():
    return [Seleccion(id) for id in ROSTER]


def preparacion_adaptada():
    return [Seleccion("aria", "adaptacion", "espada_hierro", "tactica"),
            Seleccion("bruno", "adaptacion", "maza_hierro", "tactica"),
            Seleccion("cora", "adaptacion", "espada_hierro", "tactica")]
