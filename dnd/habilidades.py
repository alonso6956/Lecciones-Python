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
    inesquivable: bool = False
    inbloqueable: bool = False
    usa_mitigacion_escudo: bool = False
    consume_accion: bool = True

    def multiplicador_dano(self, nivel):
        return self.multiplicador_base * (1 + nivel * self.bonus_dano_por_nivel)

    def bonus_probabilidad_bloqueo(self, nivel):
        """Bono de bloqueo propio de Bloqueo y contraataque por nivel."""
        if self.id != "bloqueo_contraataque":
            return 0.0
        nivel_efectivo = max(1, min(nivel, self.nivel_maximo))
        return 0.20 + nivel_efectivo * 0.10

    def calcular_efecto(self, nivel, valor_atributo, escudo=None):
        if self.usa_mitigacion_escudo:
            porcentaje_bloqueado = getattr(
                escudo,
                "porcentaje_dano_bloqueado",
                0.0,
            )
            nivel_efectivo = max(0, min(nivel, self.nivel_maximo))
            mitigacion_por_nivel = porcentaje_bloqueado / 2
            return min(
                self.efecto_maximo,
                mitigacion_por_nivel * nivel_efectivo,
            )
        efecto = (
            self.efecto_base
            + nivel * self.efecto_por_nivel
            + valor_atributo * self.efecto_por_atributo
        )
        return min(self.efecto_maximo, efecto)

    def descripcion_interfaz(self, nivel, valor_atributo, escudo=None):
        """Describe resultados concretos sin exponer ecuaciones internas."""
        nivel = max(1, nivel)
        if self.id == "paso_veloz":
            evasion = round(self.calcular_efecto(nivel, valor_atributo) * 100)
            return (
                f"Eleva la evasión al {evasion}% hasta finalizar el siguiente "
                "turno enemigo. Activarla no consume la acción; después puedes "
                "atacar o usar otra habilidad."
            )
        if self.id == "corte_certero":
            dano = round(self.multiplicador_dano(nivel) * 100)
            return (
                f"El primer golpe inflige {dano}% de daño y es inesquivable "
                "e inbloqueable, pero respeta la armadura. La segunda daga "
                "realiza un ataque normal."
            )
        if self.id == "bloqueo_contraataque":
            probabilidad_base = getattr(escudo, "probabilidad_bloqueo", 0)
            probabilidad_adicional = self.bonus_probabilidad_bloqueo(nivel)
            probabilidad_total = round(
                min(1.0, probabilidad_base + probabilidad_adicional) * 100
            )
            bloqueado = round(
                getattr(escudo, "porcentaje_dano_bloqueado", 0) * 100
            )
            return (
                "Contraataca con el daño del arma y gana 5% de daño por "
                f"punto de Constitución. Tiene {probabilidad_total}% de "
                f"bloquear durante este ataque; "
                f"al hacerlo obtiene {bloqueado}% de daño adicional."
            )
        if self.id == "mitigar_dano":
            reduccion = round(
                self.calcular_efecto(nivel, valor_atributo, escudo) * 100
            )
            return (
                f"Reduce {reduccion}% del daño recibido durante 3 turnos, "
                "de forma independiente de la armadura."
            )
        if self.id == "hack_slash":
            dano_total = round(self.multiplicador_dano(nivel) * 300)
            return (
                f"Realiza 3 ataques independientes que infligen {dano_total}% "
                "de daño combinado y pueden ser críticos. El tercer golpe gana "
                "5% adicional si el objetivo está por 70% de vida, 10% si "
                "está por 50% y 20% si está por 30%."
            )
        if self.id == "golpe_aplastante":
            dano = round(self.multiplicador_dano(nivel) * 100)
            aturdimiento = round(self.calcular_efecto(nivel, valor_atributo) * 100)
            return (
                f"Inflige {dano}% de daño y tiene {aturdimiento}% de "
                "probabilidad de aturdir."
            )
        return self.descripcion


class HabilidadFactory:
    def __init__(self, ruta_catalogo=None):
        ruta = Path(ruta_catalogo) if ruta_catalogo else _ruta_recurso("skills.json")
        with ruta.open(encoding="utf-8") as archivo:
            entradas = json.load(archivo)["skills"]
        self._datos = {entrada["id"]: entrada for entrada in entradas}
        self._aplicar_rediseno_habilidades()

    def _aplicar_rediseno_habilidades(self):
        """Mantiene los ajustes de diseño junto al modelo de habilidades."""
        corte_certero = self._datos.get("corte_certero")
        if corte_certero:
            corte_certero.update(
                nombre="Corte certero (No Escape)",
                descripcion=(
                    "No Escape: golpe 100% inesquivable e inbloqueable."
                ),
                tipo_efecto="no_escape",
                efecto_base=0,
                efecto_por_nivel=0,
                efecto_por_atributo=0,
                efecto_maximo=0,
                inesquivable=True,
                inbloqueable=True,
            )

        bloqueo_contraataque = self._datos.get("bloqueo_contraataque")
        if bloqueo_contraataque:
            bloqueo_contraataque.update(
                descripcion=(
                    "Contraataca con probabilidad de bloqueo aumentada; si "
                    "bloquea, suma como daño el porcentaje bloqueado por el "
                    "escudo. Escala 5% por punto de Constitución."
                ),
                tipo_efecto="bloqueo_contraataque",
                efecto_base=0,
                efecto_por_nivel=0,
                efecto_por_atributo=0,
                efecto_maximo=0,
            )

        mitigar_dano = self._datos.get("mitigar_dano")
        if mitigar_dano:
            mitigar_dano.update(
                descripcion=(
                    "Reduce durante 3 turnos, por cada nivel, un valor igual "
                    "a la mitad del porcentaje de daño bloqueado por el escudo."
                ),
                efecto_base=0,
                efecto_por_nivel=0,
                efecto_por_atributo=0,
                efecto_maximo=1,
                usa_mitigacion_escudo=True,
            )

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
