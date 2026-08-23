"""Modelos y fábrica de habilidades desacopladas del catálogo de armas."""

import json
import sys
from dataclasses import dataclass
from pathlib import Path


def _ruta_recurso(nombre):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / nombre


@dataclass(frozen=True)
class Habilidad:
    id: str
    nombre: str
    descripcion: str
    atributo_escalado: str
    tipo_arma_requerida: str
    tipo_efecto: str
    multiplicador_base: float
    bonus_dano_por_nivel: float
    efecto_base: float
    efecto_por_nivel: float
    efecto_por_atributo: float
    efecto_maximo: float
    costo_energia: int
    cooldown_turnos: int
    nivel_maximo: int
    causa_dano: bool = True
    duracion_turnos: int = 0
    numero_golpes: int = 1
    requiere_mano_secundaria_libre: bool = False
    bloquear_mientras_activa: bool = False

    def multiplicador_dano(self, nivel):
        return self.multiplicador_base * (1 + nivel * self.bonus_dano_por_nivel)

    def calcular_efecto(self, nivel, valor_atributo):
        efecto = (
            self.efecto_base
            + nivel * self.efecto_por_nivel
            + valor_atributo * self.efecto_por_atributo
        )
        return min(self.efecto_maximo, efecto)


class HabilidadFactory:
    def __init__(self, ruta_catalogo=None):
        ruta = Path(ruta_catalogo) if ruta_catalogo else _ruta_recurso("skills.json")
        with ruta.open(encoding="utf-8") as archivo:
            entradas = json.load(archivo)["skills"]
        self._datos = {entrada["id"]: entrada for entrada in entradas}

    def crear(self, habilidad_id):
        try:
            return Habilidad(**self._datos[habilidad_id])
        except KeyError as error:
            raise ValueError(f"La habilidad {habilidad_id!r} no existe.") from error

    def todas(self):
        return [self.crear(habilidad_id) for habilidad_id in self._datos]

    def para_tipo_arma(self, tipo_arma):
        return next(
            (
                habilidad
                for habilidad in self.todas()
                if habilidad.tipo_arma_requerida == tipo_arma
            ),
            None,
        )


habilidad_factory = HabilidadFactory()
