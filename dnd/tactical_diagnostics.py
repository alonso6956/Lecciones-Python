"""Diagnóstico causal a partir del daño efectivo, sin duplicar ticks ni muertes."""

from collections import defaultdict
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class CombatEvent:
    turno: int
    tipo: str
    actor_id: str = None
    objetivo_id: str = None
    fuente_tag: str = None
    cantidad: float = None
    hp_restante_pct: float = None
    metadata: dict = field(default_factory=dict)


class CombatLog:
    def __init__(self):
        self.eventos = []

    def registrar(self, turno, tipo, **datos):
        evento = CombatEvent(turno, tipo, **datos)
        self.eventos.append(evento)
        return evento

    def serializar(self):
        return [asdict(evento) for evento in self.eventos]


MENSAJES = {
    "sangrado": ("El sangrado fue la principal fuente de daño de la derrota.",
                 "Mejora el daño y entrena al grupo en el calabozo para acortar el combate."),
    "escudo_no_roto": ("El castigo por no romper el escudo dominó el daño recibido.",
                      "Mejora el daño del grupo y elige equipo con mayor ruptura."),
    "dano_directo": ("La party no soportó el daño directo del encuentro.",
                    "Mejora Constitución y equipa armadura comprada en el calabozo."),
    "desgaste_general": ("No hubo una causa dominante clara.",
                         "Revisa las estadísticas y la preparación general del grupo."),
}


def normalizar_causa(tag):
    return {"fisico": "dano_directo", "castigo_escudo": "escudo_no_roto", "escudo": "escudo_no_roto"}.get(tag, tag or "desconocido")


class DiagnosticEngine:
    @staticmethod
    def analizar(log):
        contribuciones = defaultdict(float)
        for evento in log.eventos:
            # Cantidad = HP realmente perdido, acotado por la vida anterior.
            # muerte, tick_sangrado y castigo_escudo son evidencia, no otro daño.
            if evento.tipo == "dano_recibido":
                contribuciones[normalizar_causa(evento.fuente_tag)] += max(0, evento.cantidad or 0)
        total = sum(contribuciones.values())
        causa, porcentaje = "desgaste_general", 0.0
        if total:
            dominante = max(contribuciones, key=contribuciones.get)
            porcentaje = contribuciones[dominante] / total * 100
            if porcentaje >= 40 and dominante in MENSAJES:
                causa = dominante
        mensaje, sugerencia = MENSAJES[causa]
        return {"causa": causa, "contribucion_pct": round(porcentaje, 2), "mensaje": mensaje,
                "sugerencia": sugerencia, "dano_total": round(total, 2),
                "contribuciones": {k: round(v, 2) for k, v in contribuciones.items()},
                "metodo": "Porcentaje del daño efectivo recibido; muertes y marcadores no suman daño adicional."}
