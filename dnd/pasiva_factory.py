"""Carga y construye pasivas de arma según su tier."""

import json
import sys
from pathlib import Path

from pasivas import Pasiva


def _ruta_recurso(nombre):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / nombre


class PasivaFactory:
    def __init__(self, ruta_catalogo=None):
        ruta = Path(ruta_catalogo) if ruta_catalogo else _ruta_recurso("pasivas.json")
        with ruta.open(encoding="utf-8") as archivo:
            entradas = json.load(archivo)["pasivas"]
        self._datos = {entrada["id"]: entrada for entrada in entradas}

    def crear(self, pasiva_id, tier):
        try:
            datos = dict(self._datos[pasiva_id])
        except KeyError as error:
            raise ValueError(f"La pasiva {pasiva_id!r} no existe.") from error

        valores_tier = datos.pop("valores_tier")
        try:
            valor = valores_tier[str(tier)]
        except KeyError as error:
            raise ValueError(
                f"La pasiva {pasiva_id!r} no admite el tier {tier}."
            ) from error

        parametros = datos.pop("parametros", {})
        return Pasiva(tier=tier, valor=valor, parametros=parametros, **datos)

    def para_arma(self, arma):
        pasiva_id = getattr(arma, "pasiva_id", None)
        if not pasiva_id:
            return None
        pasiva = self.crear(pasiva_id, arma.tier)
        if pasiva.tipo_arma != arma.tipo_arma:
            raise ValueError(
                f"La pasiva {pasiva.id!r} no corresponde al arma {arma.nombre!r}."
            )
        return pasiva

    def todas(self):
        return [
            self.crear(pasiva_id, tier)
            for pasiva_id, datos in self._datos.items()
            for tier in sorted(map(int, datos["valores_tier"]))
        ]


pasiva_factory = PasivaFactory()
