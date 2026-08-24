"""Entidades de dominio para los objetos del catálogo."""

from dataclasses import dataclass, field


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
    pasiva_id: str = ""
    requisitos: dict = field(default_factory=dict)

    def cumple_requisitos(self, personaje):
        return all(
            getattr(personaje, estadistica, 0) >= minimo
            for estadistica, minimo in self.requisitos.items()
        )

    def factor_escalado(self, fuerza, destreza):
        valor = {"fuerza": fuerza, "destreza": destreza}[
            self.estadistica_escalado
        ]
        return 1 + max(0, valor - 1) * self.crecimiento_por_punto


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
