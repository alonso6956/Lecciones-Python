"""Entidades de dominio para los objetos del catálogo."""

from dataclasses import dataclass, field
import math


@dataclass(frozen=True)
class Item:
    id: str
    nombre: str
    precio: int


@dataclass(frozen=True)
class Arma(Item):
    tipo_arma: str
    estadistica_escalado: str
    crecimiento_por_punto: float
    tier: int
    inicial: bool
    ataque: tuple
    dos_manos: bool = False
    requisitos: dict = field(default_factory=dict)
    peso: float = 0
    durabilidad: int = 100
    velocidad: float = 1.0
    critico: float = 0.0
    penetracion: float = 0.0
    alcance: int = 1
    material: str = ""
    perfil: str = ""
    afijo: dict = field(default_factory=dict)
    presupuesto: float = 0
    distribucion: tuple = ()
    bonus_sobrenatural: float = 0.0
    precision: float = 0
    impacto: float = 0
    escalado_fuerza: float | None = None
    dual_wield: bool | None = None
    secundaria_permitida: bool | None = None
    calidad: str = "legacy"
    version_diseno: int = 1
    afijos: tuple = ()

    @property
    def compatible_dual(self):
        return not self.dos_manos and (self.tipo_arma == "daga" if self.dual_wield is None else self.dual_wield)

    @property
    def permite_secundaria(self):
        return not self.dos_manos and self.secundaria_permitida is not False

    @property
    def coeficiente_fuerza(self):
        return self.escalado_fuerza if self.escalado_fuerza is not None else {
            "daga": .40, "espada": .75, "lanza": .80, "maza": 1.0,
        }.get(self.tipo_arma, 1.0)

    def cumple_requisitos(self, personaje):
        return all(
            getattr(personaje, estadistica, 0) >= minimo
            for estadistica, minimo in self.requisitos.items()
        )

    def factor_escalado(self, fuerza, destreza):
        return 1 + self.coeficiente_fuerza * .10 * math.sqrt(max(0, fuerza - 1))


@dataclass(frozen=True)
class Secundario(Item):
    tipo_secundario: str
    tier: int = 1
    probabilidad_bloqueo: float = 0.0
    porcentaje_dano_bloqueado: float = 0.0
    requisitos: dict = field(default_factory=dict)
    peso: float = 0
    durabilidad: int = 100
    bonificaciones: dict = field(default_factory=dict)
    material: str = ""
    perfil: str = ""
    defensa: int = 0
    calidad: str = "legacy"
    version_diseno: int = 1
    absorcion_pasiva: float = 0.10
    bloqueo_activo: float = 0.60

    def cumple_requisitos(self, personaje):
        return all(
            getattr(personaje, estadistica, 0) >= minimo
            for estadistica, minimo in self.requisitos.items()
        )


@dataclass(frozen=True)
class Armadura(Item):
    slot: str
    defensa: int
    requisitos: dict = field(default_factory=dict)
    peso: float = 0
    durabilidad: int = 100
    bonificaciones: dict = field(default_factory=dict)
    tier: int = 1
    material: str = ""
    perfil: str = ""
    calidad: str = "legacy"
    version_diseno: int = 1

    def cumple_requisitos(self, personaje):
        return all(
            getattr(personaje, estadistica, 0) >= minimo
            for estadistica, minimo in self.requisitos.items()
        )


@dataclass(frozen=True)
class Consumible(Item):
    efecto: str
    valor: int


@dataclass(frozen=True)
class Material(Item):
    descripcion: str = ""
