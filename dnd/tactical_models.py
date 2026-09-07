"""Preparación táctica sobre los modelos y el catálogo originales de Dungeon."""

from dataclasses import dataclass, field
from typing import Any

from character import Personaje
from enemies import Enemigo
from item_factory import item_factory


ROSTER = {
    "aria": {"nombre": "Aria", "rol": "Pícara", "stats": {"fuerza": 4, "destreza": 6, "constitucion": 5},
             "unica": "golpe_preciso", "descripcion": "Golpe preciso: daño concentrado cada 3 rondas."},
    "bruno": {"nombre": "Bruno", "rol": "Guerrero", "stats": {"fuerza": 6, "destreza": 3, "constitucion": 7},
              "unica": "golpe_demoledor", "descripcion": "Golpe demoledor: ataque potente; puede reservar su habilidad para romper escudos."},
    "cora": {"nombre": "Cora", "rol": "Tanque", "stats": {"fuerza": 3, "destreza": 2, "constitucion": 10},
             "unica": "muralla", "descripcion": "Muralla: reduce el daño directo del grupo durante 2 rondas. Puede curar aliados."},
}

BUILDS = {
    "ofensiva": {"nombre": "Ofensiva", "ataque": 1.20, "resistencia_sangrado": 0.0,
                 "descripcion": "+20% ataque y +1 velocidad; mayor presión sin protección contra sangrado."},
    "adaptacion": {"nombre": "Adaptación", "ataque": 1.0, "resistencia_sangrado": 0.65,
                   "descripcion": "65% resistencia al sangrado, limpieza y +25% ruptura; menor daño bruto."},
}

# Extensión táctica del catálogo, sin alterar las pasivas del modo original.
ARMAS = {
    "dagas_hierro": {"velocidad": 3, "critico": 0.15, "ruptura": 0.5, "resistencia_sangrado": 0.0,
                     "descripcion": "+3 velocidad, 15% crítico y +35% daño contra un jefe vulnerable."},
    "maza_hierro": {"velocidad": -1, "critico": 0.0, "ruptura": 1.5, "resistencia_sangrado": 0.0,
                   "descripcion": "Daño pesado: ruptura x1,5; habilita Romper escudo (x4)."},
    "espada_hierro": {"velocidad": 0, "critico": 0.0, "ruptura": 0.5, "resistencia_sangrado": 0.25,
                     "descripcion": "Daño sostenido: ignora 35% de armadura y reduce 25% el sangrado restante."},
}

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


@dataclass
class Actor:
    """Adaptador de combate: el modelo existente sigue siendo dueño de la vida."""

    id: str
    modelo: Any
    ataque: float
    defensa: float
    velocidad: float
    rol: str
    seleccion: Seleccion = None
    resistencia_sangrado: float = 0.0
    estados: dict = field(default_factory=dict)
    cooldowns: dict = field(default_factory=dict)

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
        return {"id": self.id, "nombre": self.modelo.nombre, "rol": self.rol,
                "hp": round(self.hp, 2), "hp_max": self.hp_max,
                "ataque": round(self.ataque, 2), "defensa": self.defensa, "velocidad": self.velocidad,
                "nivel": getattr(self.modelo, "nivel", 1),
                "resistencia_sangrado": round(self.resistencia_sangrado * 100, 2),
                "estados": {key: dict(value) for key, value in self.estados.items()},
                "cooldowns": dict(self.cooldowns)}


@dataclass(frozen=True)
class Encuentro:
    id: str = "guardian_verdugo"
    hp: float = 440
    ataque: float = 22
    defensa: float = 10
    velocidad: float = 12
    escudo: float = 105
    ventana_rondas: int = 2
    sangrado_pct: float = 0.04
    sangrado_duracion: int = 4
    sangrado_max: int = 4
    castigo: float = 155
    limite_rondas: int = 80

    def __post_init__(self):
        if min(self.hp, self.escudo, self.ventana_rondas, self.sangrado_duracion,
               self.sangrado_max, self.limite_rondas) <= 0:
            raise ValueError("Vida, escudo, duraciones y límite deben ser positivos.")
        if min(self.ataque, self.defensa, self.velocidad, self.sangrado_pct, self.castigo) < 0:
            raise ValueError("Los valores de combate no pueden ser negativos.")

    def crear_jefe(self):
        modelo = Enemigo("Guardián", "Verdugo", 6, 3, 8, self.hp, self.hp, "Morning Star", (0, 0), 0)
        return Actor(self.id, modelo, self.ataque, self.defensa, self.velocidad, "Jefe")


class BuildManager:
    @staticmethod
    def validar(selecciones):
        if len(selecciones) != 3 or {s.personaje_id for s in selecciones} != set(ROSTER):
            raise ValueError("Selecciona los tres personajes, sin duplicados.")
        for s in selecciones:
            if s.build not in BUILDS or s.arma not in ARMAS or s.prioridad not in PRIORIDADES:
                raise ValueError("Build, arma o prioridad no válida.")

    @classmethod
    def crear_party(cls, selecciones):
        cls.validar(selecciones)
        party = []
        for s in selecciones:
            datos = ROSTER[s.personaje_id]
            modelo = Personaje(datos["nombre"], s.arma, dict(datos["stats"]))
            arma = item_factory.crear(s.arma)
            tactica = ARMAS[s.arma]
            build = BUILDS[s.build]
            # Promedio del rango de arma, sin nuevas tiradas: azar solo en crítico/iniciativa.
            ataque = (modelo.calcular_dano_base() + sum(arma.ataque) / 2) * 2 * build["ataque"]
            resistencia = 1 - (1 - build["resistencia_sangrado"]) * (1 - tactica["resistencia_sangrado"])
            party.append(Actor(s.personaje_id, modelo, ataque, modelo.calcular_defensa_base(),
                               max(1, modelo.velocidad + tactica["velocidad"] + (s.build == "ofensiva")),
                               datos["rol"], s, resistencia))
        return party


def preparacion_ofensiva():
    return [Seleccion(id) for id in ROSTER]


def preparacion_adaptada():
    return [Seleccion("aria", "adaptacion", "espada_hierro", "tactica"),
            Seleccion("bruno", "adaptacion", "maza_hierro", "tactica"),
            Seleccion("cora", "adaptacion", "espada_hierro", "tactica")]
