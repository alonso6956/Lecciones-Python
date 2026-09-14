"""Evaluador de primera coincidencia. No depende de la presentación."""

from dataclasses import dataclass

from tactical_models import PRIORIDADES


@dataclass(frozen=True)
class Accion:
    tipo: str
    objetivo_id: str
    regla: str


class AIController:
    @staticmethod
    def elegir(actor, aliados, jefe, escudo, escudo_activado=False):
        def disponible(habilidad):
            return actor.cooldowns.get(habilidad, 0) == 0

        vivos = [aliado for aliado in aliados if aliado.vivo]
        for regla in PRIORIDADES[actor.seleccion.prioridad]["reglas"]:
            if regla == "limpiar" and "limpiar" in actor.habilidades_tacticas and actor.seleccion.build == "adaptacion" and disponible("limpiar"):
                afectados = vivos if "curar" in actor.habilidades_tacticas else [actor]
                afectados = [a for a in afectados if a.estados.get("sangrado", {}).get("cargas", 0) >= 2]
                if afectados:
                    objetivo = max(afectados, key=lambda a: a.estados["sangrado"]["cargas"])
                    return Accion("limpiar", objetivo.id, regla)
            elif regla == "curar" and "curar" in actor.habilidades_tacticas and disponible("curar"):
                objetivo = min(vivos, key=lambda a: a.hp / a.hp_max)
                if objetivo.hp / objetivo.hp_max < 0.55:
                    return Accion("curar", objetivo.id, regla)
            elif regla == "romper" and escudo > 0 and disponible("unica"):
                if "romper" in actor.habilidades_tacticas:
                    return Accion("romper", jefe.id, regla)
            elif regla == "unica" and actor.unica and disponible("unica"):
                # Táctica reserva el recurso del guerrero hasta la ventana del escudo.
                if "romper" in actor.habilidades_tacticas and actor.seleccion.prioridad == "tactica" and not escudo_activado:
                    continue
                return Accion(actor.unica, actor.id if actor.unica == "muralla" else jefe.id, regla)
            elif regla == "vulnerable" and jefe.estados.get("vulnerable"):
                return Accion("ataque", jefe.id, regla)
        return Accion("ataque", jefe.id, "basico")
