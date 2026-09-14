"""Decisiones enemigas sin dependencias de clases, equipo, tablero ni UI.

El llamador entrega solo blancos percibidos y alcanzables. Una llamada por
turno propio; la memoria pertenece a un actor y a un combate.
"""

from dataclasses import dataclass


TAGS = frozenset({"cazador_healer", "rompe_tanque", "asesino_backline",
                  "cobarde", "fanatico", "protector", "oportunista"})


@dataclass(frozen=True)
class PerfilIA:
    cerebro: str = "bestia"
    tags: tuple = ()
    objetivo_prioritario: str | None = None
    intervalo: int = 2
    ignora_provocacion: bool = False

    def __post_init__(self):
        object.__setattr__(self, "tags", tuple(self.tags))
        if self.cerebro not in {"bestia", "soldado", "comandante"}:
            raise ValueError("Cerebro desconocido")
        if len(self.tags) > 3 or len(set(self.tags)) != len(self.tags) or set(self.tags) - TAGS:
            raise ValueError("Usa hasta tres tags conocidos y distintos")
        if type(self.intervalo) is not int or self.intervalo < 1:
            raise ValueError("Intervalo debe ser un entero positivo")
        if {"cobarde", "fanatico"} <= set(self.tags):
            raise ValueError("Cobarde y fanático son incompatibles")


@dataclass(frozen=True)
class BlancoIA:
    id: str
    vida_pct: float  # Fracción 0..1
    distancia: float  # Coste de ruta hasta una casilla de ataque
    defensa: float = 0
    amenaza: float = 0  # Señal observable, normalizada 0..1
    roles: tuple = ()  # Capacidades, independientes del nombre de clase
    linea: str = "frontal"


@dataclass(frozen=True)
class DecisionIA:
    tipo: str
    objetivo_id: str | None
    motivo: str
    reevaluado: bool = False


class CerebroEnemigo:
    def __init__(self, perfil=None):
        self.perfil = perfil or PerfilIA()
        self.turno = 0
        self.ultima_evaluacion = -10**9
        self.objetivo = None
        self.orden = self.perfil.objetivo_prioritario
        self.huida_restante = 0
        self.huida_usada = False

    def elegir(self, vida_pct, enemigos, aliados=(), provocado_por=None):
        self.turno += 1
        p = self.perfil
        enemigos = [b for b in enemigos if b.vida_pct > 0 and b.distancia < float("inf")]
        por_id = {b.id: b for b in enemigos}
        if not enemigos:
            return DecisionIA("esperar", None, "sin_objetivos_validos")
        if ("cobarde" in p.tags and vida_pct < .30 and not self.huida_usada):
            self.huida_restante, self.huida_usada = 2, True
        if self.huida_restante:
            self.huida_restante -= 1
            return DecisionIA("huir", None, "cobarde")
        if provocado_por in por_id and not p.ignora_provocacion:
            return DecisionIA("atacar", provocado_por, "provocacion")
        if "fanatico" in p.tags and self.objetivo in por_id:
            return DecisionIA("atacar", self.objetivo, "fanatico")
        if "protector" in p.tags:
            heridos = [b for b in aliados if 0 < b.vida_pct < .40 and b.distancia < float("inf")]
            if heridos:
                blanco = min(heridos, key=lambda b: (b.vida_pct, b.distancia, b.id))
                return DecisionIA("proteger", blanco.id, "protector")
        reevaluar = (p.cerebro == "bestia" or self.objetivo not in por_id
                     or (p.cerebro == "soldado" and self.orden in por_id and self.objetivo != self.orden)
                     or (p.cerebro == "comandante" and self.turno - self.ultima_evaluacion >= p.intervalo))
        if not reevaluar:
            return DecisionIA("atacar", self.objetivo, "mantener_objetivo")
        candidatos = enemigos
        motivo = p.cerebro
        # El orden de tags configura precedencia; filtros sin coincidencia no bloquean.
        for tag in p.tags:
            preferidos = []
            if tag == "cazador_healer":
                preferidos = [b for b in enemigos if "sanador" in b.roles]
            elif tag == "rompe_tanque":
                preferidos = [max(enemigos, key=lambda b: (b.defensa, -b.distancia, b.id))]
            elif tag == "asesino_backline":
                preferidos = [b for b in enemigos if b.linea == "retaguardia" and "dano" in b.roles]
            elif tag == "oportunista":
                preferidos = [b for b in enemigos if b.vida_pct < .30]
                preferidos.sort(key=lambda b: (b.vida_pct, b.distancia, b.id))
                preferidos = preferidos[:1]
            if preferidos:
                candidatos, motivo = preferidos, tag
                break
        if p.cerebro == "soldado" and self.orden in por_id:
            elegido, motivo = por_id[self.orden], "orden"
        elif p.cerebro == "comandante":
            elegido = max(candidatos, key=lambda b: (2 * b.amenaza + 1 - b.vida_pct
                                                   - .1 * b.distancia, b.id))
        else:
            elegido = min(candidatos, key=lambda b: (b.distancia, b.id))
        if p.cerebro == "soldado" and self.orden is None:
            self.orden = elegido.id
        self.objetivo = elegido.id
        self.ultima_evaluacion = self.turno
        return DecisionIA("atacar", elegido.id, motivo, True)
