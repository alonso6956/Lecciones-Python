"""Resolución 3v1 por rondas; reutiliza la mitigación de Dungeon (constante 22)."""

import random
from dataclasses import asdict

from combat_formulas import aplicar_mitigacion_dano
from combat_stats import estadisticas_combate, tirar_dano
from weapon_effects import armadura_tras_penetracion, modificar_golpe, activar_afijo
from tactical_ai import AIController
from tactical_diagnostics import CombatLog, DiagnosticEngine
from tactical_models import ARMAS, BuildManager, Encuentro


class CombatResolver:
    def __init__(self, selecciones, encuentro=None, seed=1234, roster=None):
        self.encuentro = encuentro or Encuentro()
        self.party = BuildManager.crear_party(selecciones, roster)
        self.jefe = self.encuentro.crear_jefe()
        self.rng = random.Random(seed)
        self.seed = seed
        self.log = CombatLog()
        self.ronda = 0
        self.resultado = None
        self.motivo = None
        self.escudo = 0
        self.escudo_activado = False
        self.escudo_vence = None
        self.frames = []
        self.inicial = self.estado()

    def estado(self):
        return {"ronda": self.ronda, "party": [a.estado() for a in self.party],
                "jefe": {**self.jefe.estado(), "escudo": round(self.escudo, 2),
                         "escudo_max": self.encuentro.escudo, "escudo_vence": self.escudo_vence},
                "resultado": self.resultado}

    def _evento(self, tipo, **datos):
        return self.log.registrar(self.ronda, tipo, **datos)

    def _golpe(self, actor, objetivo, multiplicador=1):
        """Tirada, evasión, crítico y bloqueo con las estadísticas de Dungeon."""
        bruto = tirar_dano(actor.modelo, self.rng) * multiplicador
        datos = estadisticas_combate(objetivo.modelo)
        if self.rng.random() < datos["evasion"]:
            self._evento("esquiva", actor_id=objetivo.id, objetivo_id=actor.id)
            return 0
        pasiva = getattr(actor.modelo, "pasiva_clase", None)
        ignora = bool(pasiva and pasiva.efecto == "ignorar_defensa" and pasiva.ignora_defensa(self.rng.random()))
        bloqueo = 0
        if not ignora and datos["probabilidad_bloqueo"] and self.rng.random() < datos["probabilidad_bloqueo"]:
            bloqueo = datos["porcentaje_dano_bloqueado"]
            self._evento("bloqueo", actor_id=objetivo.id, objetivo_id=actor.id)
        if pasiva and pasiva.efecto == "critico" and self.rng.random() < pasiva.probabilidad:
            bruto = pasiva.calcular_critico(bruto)
            self._evento("critico", actor_id=actor.id, objetivo_id=objetivo.id)
        bruto, critico_arma = modificar_golpe(actor.modelo, objetivo.modelo, bruto, self.rng)
        if critico_arma:
            self._evento("critico", actor_id=actor.id, objetivo_id=objetivo.id)
        return max(1, round(aplicar_mitigacion_dano(
            bruto, bloqueo_escudo=bloqueo, armadura=0 if ignora else armadura_tras_penetracion(actor.modelo, objetivo.defensa))))

    def _dano(self, actor, objetivo, cantidad, tag):
        if not objetivo.vivo:
            return
        efectivo = round(min(objetivo.hp, max(0, cantidad)), 2)
        objetivo.hp = round(objetivo.hp - efectivo, 2)
        self._evento("dano_infligido" if objetivo is self.jefe else "dano_recibido",
                     actor_id=actor.id, objetivo_id=objetivo.id, fuente_tag=tag,
                     cantidad=efectivo, hp_restante_pct=objetivo.hp / objetivo.hp_max * 100)
        if not objetivo.vivo:
            self._evento("muerte", actor_id=actor.id, objetivo_id=objetivo.id,
                         fuente_tag=tag, cantidad=0, hp_restante_pct=0)
        if objetivo is self.jefe and objetivo.vivo and not self.escudo_activado and objetivo.hp <= objetivo.hp_max / 2:
            self.escudo_activado = True
            self.escudo = self.encuentro.escudo
            self.escudo_vence = self.ronda + self.encuentro.ventana_rondas
            self._evento("escudo_activado", actor_id=self.jefe.id, fuente_tag="escudo",
                         cantidad=self.escudo, metadata={"vence_ronda": self.escudo_vence})
        self._comprobar_fin()

    def _comprobar_fin(self):
        if self.resultado:
            return
        if not self.jefe.vivo:
            self.resultado = "victoria"
        elif not any(a.vivo for a in self.party):
            self.resultado = "derrota"
        if self.resultado:
            self.motivo = "jefe_derrotado" if self.resultado == "victoria" else "party_derrotada"
            self._evento(self.resultado, metadata={"motivo": self.motivo})

    def _inicio_turno(self, actor):
        sangrado = actor.estados.get("sangrado")
        if sangrado:
            dano = actor.hp_max * self.encuentro.sangrado_pct * sangrado["cargas"] * (1 - actor.resistencia_sangrado)
            self._evento("tick_sangrado", actor_id=self.jefe.id, objetivo_id=actor.id,
                         fuente_tag="sangrado", metadata={"cargas": sangrado["cargas"]})
            self._dano(self.jefe, actor, dano, "sangrado")

    def _accion_jefe(self):
        if self.jefe.estados.get("vulnerable"):
            self._evento("turno_omitido", actor_id=self.jefe.id, fuente_tag="ruptura",
                         metadata={"motivo": "aturdido_por_ruptura"})
            return
        vivos = [a for a in self.party if a.vivo]
        objetivo = vivos[(self.ronda - 1) % len(vivos)]
        self._evento("accion", actor_id=self.jefe.id, objetivo_id=objetivo.id,
                     metadata={"habilidad": "corte_sangriento"})
        dano = self._golpe(self.jefe, objetivo, 0.65 if objetivo.estados.get("muralla") else 1)
        if dano:
            self._dano(self.jefe, objetivo, dano, "fisico")
        if self.resultado:
            return
        for aliado in self.party:
            if aliado.vivo:
                cargas = min(self.encuentro.sangrado_max, aliado.estados.get("sangrado", {}).get("cargas", 0) + 1)
                aliado.estados["sangrado"] = {"cargas": cargas, "vence": self.ronda + self.encuentro.sangrado_duracion}
                self._evento("estado_aplicado", actor_id=self.jefe.id, objetivo_id=aliado.id,
                             fuente_tag="sangrado", metadata={"cargas": cargas, "duracion": self.encuentro.sangrado_duracion})

    def _accion_aliado(self, actor):
        accion = AIController.elegir(actor, self.party, self.jefe, self.escudo, self.escudo_activado)
        objetivo = next((a for a in self.party if a.id == accion.objetivo_id), self.jefe)
        if not objetivo.vivo:
            raise RuntimeError("La IA eligió un objetivo muerto.")
        self._evento("accion", actor_id=actor.id, objetivo_id=objetivo.id,
                     metadata={"habilidad": accion.tipo, "regla": accion.regla})
        if accion.tipo == "limpiar":
            objetivo.estados.pop("sangrado", None)
            actor.cooldowns["limpiar"] = 3
            self._evento("estado_limpiado", actor_id=actor.id, objetivo_id=objetivo.id, fuente_tag="sangrado")
            return
        if accion.tipo == "curar":
            curado = objetivo.modelo.curar(round(objetivo.hp_max * 0.35, 2))
            actor.cooldowns["curar"] = 3
            self._evento("curacion", actor_id=actor.id, objetivo_id=objetivo.id, cantidad=curado,
                         hp_restante_pct=objetivo.hp / objetivo.hp_max * 100)
            return
        if accion.tipo == "muralla":
            for aliado in self.party:
                if aliado.vivo:
                    aliado.estados["muralla"] = {"vence": self.ronda + 1}
                    self._evento("estado_aplicado", actor_id=actor.id, objetivo_id=aliado.id,
                                 fuente_tag="muralla", metadata={"reduccion_directa": 0.35})
            actor.cooldowns["unica"] = 4
            return
        arma_id = actor.seleccion.arma
        arma = ARMAS[arma_id]
        multiplicador = {"golpe_preciso": 1.8, "golpe_demoledor": 1.6, "romper": 1.1}.get(accion.tipo, 1.0)
        if accion.tipo != "ataque":
            if actor.cooldowns.get("unica", 0):
                raise RuntimeError("La IA eligió una habilidad en cooldown.")
            actor.cooldowns["unica"] = 3
        if self.jefe.estados.get("vulnerable"):
            multiplicador *= 1.15
        dano = self._golpe(actor, self.jefe, multiplicador)
        if not dano:
            return
        if self.escudo > 0:
            factor = 4 if accion.tipo == "romper" else arma["ruptura"]
            factor *= 1.25 if actor.seleccion.build == "adaptacion" else 1
            ruptura = round(min(self.escudo, dano * factor), 2)
            self.escudo = round(self.escudo - ruptura, 2)
            self._evento("dano_escudo", actor_id=actor.id, objetivo_id=self.jefe.id,
                         fuente_tag="ruptura", cantidad=ruptura, metadata={"escudo_restante": self.escudo})
            if self.escudo <= 0:
                self.escudo_vence = None
                self.jefe.estados["vulnerable"] = {"vence": self.ronda + 1}
                self._evento("escudo_roto", actor_id=actor.id, objetivo_id=self.jefe.id, fuente_tag="ruptura")
        else:
            self._dano(actor, self.jefe, dano, "fisico")
            efecto = activar_afijo(actor.modelo, self.jefe.modelo, self.rng)
            if efecto:
                self.jefe.modelo.efectos_arma[efecto]["actor_id"] = actor.id

    def paso(self):
        if self.resultado:
            raise ValueError("El combate ya terminó.")
        inicio_eventos = len(self.log.eventos)
        self.ronda += 1
        vivos = [a for a in self.party + [self.jefe] if a.vivo]
        iniciativas = {a.id: a.velocidad + self.rng.uniform(0, a.velocidad * 0.10) for a in vivos}
        orden = sorted(vivos, key=lambda a: iniciativas[a.id], reverse=True)
        self._evento("iniciativa", metadata={"orden": [a.id for a in orden], "valores": iniciativas})
        for actor in orden:
            if self.resultado:
                break
            if not actor.vivo:
                continue
            self._inicio_turno(actor)
            if self.resultado:
                break
            if not actor.vivo:
                continue
            if actor is self.jefe:
                self._accion_jefe()
                if not self.resultado:
                    for efecto, estado in list(self.jefe.modelo.efectos_arma.items()):
                        origen = next(a for a in self.party if a.id == estado["actor_id"])
                        self._dano(origen, self.jefe, estado["dano"], efecto)
                        estado["turnos"] -= 1
                        if estado["turnos"] <= 0:
                            del self.jefe.modelo.efectos_arma[efecto]
                        if self.resultado:
                            break
            else:
                self._accion_aliado(actor)
        if not self.resultado and self.escudo > 0 and self.ronda >= self.escudo_vence:
            self._evento("escudo_no_roto", actor_id=self.jefe.id, fuente_tag="escudo_no_roto",
                         metadata={"escudo_restante": self.escudo})
            self._evento("castigo_escudo", actor_id=self.jefe.id, fuente_tag="escudo_no_roto")
            self.escudo = 0
            self.escudo_vence = None
            for aliado in self.party:
                if aliado.vivo:
                    bruto = self.encuentro.castigo * (0.65 if aliado.estados.get("muralla") else 1)
                    dano = aplicar_mitigacion_dano(bruto, armadura=aliado.defensa)
                    self._dano(self.jefe, aliado, dano, "escudo_no_roto")
        for actor in self.party + [self.jefe]:
            actor.cooldowns = {k: max(0, v - 1) for k, v in actor.cooldowns.items()}
            for tag, estado in list(actor.estados.items()):
                if estado["vence"] <= self.ronda:
                    del actor.estados[tag]
                    if not self.resultado:
                        self._evento("estado_expirado", objetivo_id=actor.id, fuente_tag=tag)
        if not self.resultado and self.ronda >= self.encuentro.limite_rondas:
            self.resultado = "derrota"
            self.motivo = "limite_seguridad"
            self._evento("derrota", metadata={"motivo": self.motivo})
        frame = {**self.estado(), "eventos": [asdict(e) for e in self.log.eventos[inicio_eventos:]]}
        self.frames.append(frame)
        return frame

    def ejecutar(self):
        while not self.resultado:
            self.paso()
        return self.resumen()

    def resumen(self):
        diagnostico = DiagnosticEngine.analizar(self.log) if self.resultado == "derrota" else None
        if diagnostico and self.motivo == "limite_seguridad":
            diagnostico.update(causa="desgaste_general", mensaje="Se alcanzó el límite de seguridad de rondas.",
                               sugerencia="Revisa el daño de la party y su preparación general.")
        return {"resultado": self.resultado, "motivo": self.motivo, "rondas": self.ronda,
                "supervivientes": [a.id for a in self.party if a.vivo], "seed": self.seed,
                "diagnostico": diagnostico, "inicial": self.inicial, "final": self.estado(),
                "frames": self.frames, "eventos": self.log.serializar()}
