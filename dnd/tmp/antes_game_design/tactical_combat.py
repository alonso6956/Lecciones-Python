"""Combate por rondas y tablero opcional; reutiliza las fórmulas de Dungeon."""

import random
from dataclasses import asdict

from combat_formulas import aplicar_mitigacion_dano
from combat_stats import estadisticas_combate, tirar_dano
from weapon_effects import armadura_tras_penetracion, modificar_golpe, activar_afijo
from tactical_ai import AIController
from tactical_diagnostics import CombatLog, DiagnosticEngine
from tactical_models import ARMAS, BuildManager, Encuentro
from tactical_board import Tablero, distancia
from enemy_ai import BlancoIA, CerebroEnemigo, PerfilIA


class CombatResolver:
    def __init__(self, selecciones, encuentro=None, seed=1234, roster=None, tablero=None):
        self.encuentro = encuentro or Encuentro()
        self.party = BuildManager.crear_party(selecciones, roster)
        self.enemigos = self.encuentro.crear_enemigos()
        self.jefe = self.enemigos[0]  # Alias de compatibilidad para la mecánica del jefe.
        self.cerebros = {a.id: CerebroEnemigo(PerfilIA("bestia" if i == 0 else "soldado",
                            ("oportunista",) if i == 0 else ())) for i, a in enumerate(self.enemigos)}
        self.ia_enemiga = CerebroEnemigo(self.encuentro.perfil_ia) if self.encuentro.perfil_ia else None
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
        self.tablero = Tablero(tablero, [a.id for a in self.party], self.encuentro.ids_enemigos) if tablero is not None else None
        self.vistas = []
        self.maniobras_usadas = set()
        self.inicial = self.estado()

    def estado(self):
        return {"ronda": self.ronda, "party": [a.estado() for a in self.party],
                "enemigos": [a.estado() for a in self.enemigos],
                "jefe": None if self.encuentro.grupo else {**self.jefe.estado(), "escudo": round(self.escudo, 2),
                         "escudo_max": self.encuentro.escudo, "escudo_vence": self.escudo_vence},
                "resultado": self.resultado,
                "tablero": self.tablero.estado() if self.tablero else None}

    def _vista(self, actor=None):
        if self.tablero:
            self.vistas.append({**self.estado(), "actor_id": actor.id if actor else None,
                                "evento": asdict(self.log.eventos[-1]) if self.log.eventos else None})

    def _vivos(self):
        return [a for a in self.party + self.enemigos if a.vivo]

    @staticmethod
    def _alcance(actor):
        inventario = getattr(actor.modelo, "inventario", None)
        return max(1, getattr(inventario.arma_equipada, "alcance", 1)) if inventario else 1

    def _ruta(self, actor, objetivo, alcance):
        ocupados = {self.tablero.posiciones[a.id] for a in self._vivos() if a is not actor}
        return self.tablero.ruta(actor.id, self.tablero.posiciones[objetivo.id], alcance, ocupados)

    def _acercar(self, actor, objetivo, alcance):
        if not self.tablero:
            return True
        campo = self.tablero
        if campo.en_alcance(campo.posiciones[actor.id], campo.posiciones[objetivo.id], alcance):
            return True
        if actor.estados.get("inmovilizado"):
            self._evento("sin_alcance", actor_id=actor.id, objetivo_id=objetivo.id, fuente_tag="inmovilizado")
            return False
        ruta = self._ruta(actor, objetivo, alcance)
        presupuesto = max(2, min(4, int(actor.velocidad / 4)))
        for punto in ruta or []:
            coste = campo.coste(punto)
            if coste > presupuesto:
                break
            presupuesto -= coste
            anterior = campo.posiciones[actor.id]
            campo.posiciones[actor.id] = punto
            self._evento("movimiento", actor_id=actor.id, metadata={"origen": list(anterior), "destino": list(punto), "coste": coste})
            self._vista(actor)
            trampa = "trampa_aliada" if actor in self.enemigos else "trampa_rival"
            if campo.terreno(punto) == trampa:
                del campo.celdas[punto]
                actor.estados["inmovilizado"] = {"vence": self.ronda + 1}
                origen = self.party[0] if actor in self.enemigos else self.jefe
                self._evento("trampa_activada", actor_id=actor.id, metadata={"casilla": list(punto)})
                self._dano(origen, actor, 12, "trampa")
                self._vista(actor)
                break
        if not actor.vivo or self.resultado:
            return False
        llega = campo.en_alcance(campo.posiciones[actor.id], campo.posiciones[objetivo.id], alcance)
        if not llega:
            self._evento("sin_alcance", actor_id=actor.id, objetivo_id=objetivo.id,
                         metadata={"motivo": "ruta_bloqueada" if ruta is None else "aproximacion"})
        return llega

    def _maniobra(self, actor):
        tipo = next((t for t in ("trampa", "humo", "cobertura") if t in actor.habilidades_tacticas), None)
        if not self.tablero or actor.id in self.maniobras_usadas or tipo is None:
            return False
        campo = self.tablero
        objetivo = self._objetivo_cercano(actor, self.enemigos)
        if objetivo is None:
            return False
        punto, rival = campo.posiciones[actor.id], campo.posiciones[objetivo.id]
        if distancia(punto, rival) > 4:
            return False
        if tipo == "humo":
            for p in [punto, *campo.vecinos(punto)]:
                campo.efectos[p] = {"tipo": "humo", "vence": self.ronda + 2}
        elif tipo == "cobertura":
            if campo.terreno(punto) != "suelo":
                return False
            campo.celdas[punto] = "cobertura"
        else:
            ocupados = {campo.posiciones[a.id] for a in self._vivos()}
            candidatas = [(x, y) for x in range(10) for y in range(8)
                          if (x, y) not in ocupados and campo.terreno((x, y)) == "suelo"
                          and distancia(punto, (x, y)) <= 3 and campo.visible(punto, (x, y))]
            if not candidatas:
                return False
            punto = min(candidatas, key=lambda p: (distancia(p, rival), distancia(p, campo.posiciones[actor.id]), p))
            campo.celdas[punto] = "trampa_aliada"
        self.maniobras_usadas.add(actor.id)
        self._evento("campo_modificado", actor_id=actor.id, fuente_tag=tipo, metadata={"casilla": list(punto)})
        return True

    def _evento(self, tipo, **datos):
        return self.log.registrar(self.ronda, tipo, **datos)

    def _golpe(self, actor, objetivo, multiplicador=1):
        """Tirada, evasión, crítico y bloqueo con las estadísticas de Dungeon."""
        bruto = tirar_dano(actor.modelo, self.rng) * multiplicador
        if self.tablero:
            factor, razones = self.tablero.multiplicador(actor.id, objetivo.id, {a.id for a in self._vivos()})
            bruto *= factor
            if razones:
                self._evento("ventaja_posicional", actor_id=actor.id, objetivo_id=objetivo.id,
                             metadata={"factores": razones, "multiplicador": round(factor, 4)})
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
        self._evento("dano_infligido" if objetivo in self.enemigos else "dano_recibido",
                     actor_id=actor.id, objetivo_id=objetivo.id, fuente_tag=tag,
                     cantidad=efectivo, hp_restante_pct=objetivo.hp / objetivo.hp_max * 100)
        if not objetivo.vivo:
            self._evento("muerte", actor_id=actor.id, objetivo_id=objetivo.id,
                         fuente_tag=tag, cantidad=0, hp_restante_pct=0)
        if not self.encuentro.grupo and objetivo is self.jefe and objetivo.vivo and not self.escudo_activado and objetivo.hp <= objetivo.hp_max / 2:
            self.escudo_activado = True
            self.escudo = self.encuentro.escudo
            self.escudo_vence = self.ronda + self.encuentro.ventana_rondas
            self._evento("escudo_activado", actor_id=self.jefe.id, fuente_tag="escudo",
                         cantidad=self.escudo, metadata={"vence_ronda": self.escudo_vence})
        self._comprobar_fin()

    def _comprobar_fin(self):
        if self.resultado:
            return
        if not any(a.vivo for a in self.enemigos):
            self.resultado = "victoria"
        elif not any(a.vivo for a in self.party):
            self.resultado = "derrota"
        if self.resultado:
            self.motivo = ("enemigos_derrotados" if self.encuentro.grupo else "jefe_derrotado") if self.resultado == "victoria" else "party_derrotada"
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
        if self.ia_enemiga:
            blancos = []
            for aliado in vivos:
                coste = 0
                if self.tablero:
                    if not self.tablero.visible(self.tablero.posiciones[self.jefe.id], self.tablero.posiciones[aliado.id]):
                        continue
                    ruta = self._ruta(self.jefe, aliado, 1)
                    if ruta is None:
                        continue
                    coste = sum(self.tablero.coste(p) for p in ruta)
                roles = tuple(aliado.roles_ia) + (("sanador",) if "curar" in aliado.habilidades_tacticas else ())
                blancos.append(BlancoIA(aliado.id, aliado.hp / aliado.hp_max, coste,
                                        aliado.defensa, aliado.ataque / (aliado.ataque + 100), roles, aliado.linea_ia))
            provocacion = self.jefe.estados.get("provocado", {}).get("origen_id")
            decision = self.ia_enemiga.elegir(self.jefe.hp / self.jefe.hp_max, blancos,
                                             provocado_por=provocacion)
            self._evento("decision_ia", actor_id=self.jefe.id, objetivo_id=decision.objetivo_id,
                         metadata=asdict(decision))
            if decision.tipo == "huir":
                self._huir_jefe(vivos)
                return
            if decision.tipo != "atacar":
                return
            objetivo = next(a for a in vivos if a.id == decision.objetivo_id)
            if not self._acercar(self.jefe, objetivo, 1):
                return
        else:
            objetivo = vivos[(self.ronda - 1) % len(vivos)]
        if self.tablero and not self.ia_enemiga:
            def coste_objetivo(aliado):
                ruta = self._ruta(self.jefe, aliado, 1)
                return (sum(self.tablero.coste(p) for p in ruta) if ruta is not None else float("inf"), aliado.id)
            objetivo = min(vivos, key=coste_objetivo)
            if not self._acercar(self.jefe, objetivo, 1):
                return
        self._evento("accion", actor_id=self.jefe.id, objetivo_id=objetivo.id,
                     metadata={"habilidad": "corte_sangriento"})
        dano = self._golpe(self.jefe, objetivo, 0.65 if objetivo.estados.get("muralla") else 1)
        if dano <= 0:
            return
        self._dano(self.jefe, objetivo, dano, "fisico")
        if self.resultado:
            return
        for aliado in self.party:
            if aliado.vivo and (not self.tablero or self.tablero.en_alcance(
                    self.tablero.posiciones[self.jefe.id], self.tablero.posiciones[aliado.id], 2)):
                cargas = min(self.encuentro.sangrado_max, aliado.estados.get("sangrado", {}).get("cargas", 0) + 1)
                aliado.estados["sangrado"] = {"cargas": cargas, "vence": self.ronda + self.encuentro.sangrado_duracion}
                self._evento("estado_aplicado", actor_id=self.jefe.id, objetivo_id=aliado.id,
                             fuente_tag="sangrado", metadata={"cargas": cargas, "duracion": self.encuentro.sangrado_duracion})

    def _huir_jefe(self, enemigos):
        """Retirada local: aumenta distancia mínima; respeta costes y trampas."""
        campo = self.tablero
        if not campo or self.jefe.estados.get("inmovilizado"):
            self._evento("retirada_bloqueada", actor_id=self.jefe.id)
            return
        ocupados = {campo.posiciones[a.id] for a in enemigos}
        presupuesto = max(2, min(4, int(self.jefe.velocidad / 4)))
        def seguridad(p):
            return min(distancia(p, q) for q in ocupados)
        while presupuesto:
            origen = campo.posiciones[self.jefe.id]
            opciones = [p for p in campo.vecinos(origen) if p not in ocupados
                        and campo.coste(p) <= presupuesto and seguridad(p) > seguridad(origen)]
            if not opciones:
                break
            destino = max(opciones, key=lambda p: (seguridad(p), -campo.coste(p), p))
            presupuesto -= campo.coste(destino)
            campo.posiciones[self.jefe.id] = destino
            self._evento("movimiento", actor_id=self.jefe.id, fuente_tag="huida",
                         metadata={"origen": list(origen), "destino": list(destino), "coste": campo.coste(destino)})
            self._vista(self.jefe)
            if campo.terreno(destino) == "trampa_aliada":
                del campo.celdas[destino]
                self.jefe.estados["inmovilizado"] = {"vence": self.ronda + 1}
                self._evento("trampa_activada", actor_id=self.jefe.id, metadata={"casilla": list(destino)})
                self._dano(enemigos[0], self.jefe, 12, "trampa")
                break

    def _objetivo_cercano(self, actor, candidatos):
        def coste(objetivo):
            if not self.tablero:
                return 0
            ruta = self._ruta(actor, objetivo, self._alcance(actor))
            return sum(self.tablero.coste(p) for p in ruta) if ruta is not None else float("inf")
        posibles = [(coste(a), a.id, a) for a in candidatos if a.vivo]
        posibles = [p for p in posibles if p[0] < float("inf")]
        return min(posibles, key=lambda p: p[:2])[2] if posibles else None

    def _accion_enemigo(self, actor):
        blancos = []
        for aliado in self.party:
            if not aliado.vivo:
                continue
            ruta = self._ruta(actor, aliado, self._alcance(actor)) if self.tablero else []
            if ruta is None:
                continue
            coste = sum(self.tablero.coste(p) for p in ruta) if self.tablero else 0
            blancos.append(BlancoIA(aliado.id, aliado.hp / aliado.hp_max, coste, aliado.defensa))
        decision = self.cerebros[actor.id].elegir(actor.hp / actor.hp_max, blancos)
        self._evento("decision_ia", actor_id=actor.id, objetivo_id=decision.objetivo_id, metadata=asdict(decision))
        if decision.tipo != "atacar":
            return
        objetivo = next(a for a in self.party if a.id == decision.objetivo_id)
        if not self._acercar(actor, objetivo, self._alcance(actor)):
            return
        self._evento("accion", actor_id=actor.id, objetivo_id=objetivo.id, metadata={"habilidad": "ataque"})
        self._dano(actor, objetivo, self._golpe(actor, objetivo, .65 if objetivo.estados.get("muralla") else 1), "fisico")

    def _accion_aliado(self, actor):
        if self._maniobra(actor):
            return
        rival = self._objetivo_cercano(actor, self.enemigos)
        if rival is None:
            self._evento("sin_alcance", actor_id=actor.id)
            return
        accion = AIController.elegir(actor, self.party, rival, self.escudo, self.escudo_activado or self.encuentro.grupo)
        objetivo = next((a for a in self.party if a.id == accion.objetivo_id), rival)
        if not objetivo.vivo:
            raise RuntimeError("La IA eligió un objetivo muerto.")
        alcance = 3 if accion.tipo in {"curar", "limpiar"} else self._alcance(actor)
        if accion.tipo != "muralla" and not self._acercar(actor, objetivo, alcance):
            return
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
                if aliado.vivo and (not self.tablero or self.tablero.en_alcance(
                        self.tablero.posiciones[actor.id], self.tablero.posiciones[aliado.id], 2)):
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
        if rival.estados.get("vulnerable"):
            multiplicador *= 1.15
        dano = self._golpe(actor, rival, multiplicador)
        if not dano:
            return
        if self.escudo > 0:
            factor = 4 if accion.tipo == "romper" else arma["ruptura"]
            factor *= 1.25 if actor.seleccion.build == "adaptacion" else 1
            ruptura = round(min(self.escudo, dano * factor), 2)
            self.escudo = round(self.escudo - ruptura, 2)
            self._evento("dano_escudo", actor_id=actor.id, objetivo_id=rival.id,
                         fuente_tag="ruptura", cantidad=ruptura, metadata={"escudo_restante": self.escudo})
            if self.escudo <= 0:
                self.escudo_vence = None
                rival.estados["vulnerable"] = {"vence": self.ronda + 1}
                self._evento("escudo_roto", actor_id=actor.id, objetivo_id=rival.id, fuente_tag="ruptura")
        else:
            self._dano(actor, rival, dano, "fisico")
            efecto = activar_afijo(actor.modelo, rival.modelo, self.rng)
            if efecto:
                rival.modelo.efectos_arma[efecto]["actor_id"] = actor.id

    def paso(self):
        if self.resultado:
            raise ValueError("El combate ya terminó.")
        inicio_eventos = len(self.log.eventos)
        self.vistas = []
        self.ronda += 1
        vivos = [a for a in self.party + self.enemigos if a.vivo]
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
            if actor in self.enemigos:
                if self.encuentro.grupo:
                    self._accion_enemigo(actor)
                else:
                    self._accion_jefe()
                if not self.resultado:
                    for efecto, estado in list(actor.modelo.efectos_arma.items()):
                        origen = next(a for a in self.party if a.id == estado["actor_id"])
                        self._dano(origen, actor, estado["dano"], efecto)
                        estado["turnos"] -= 1
                        if estado["turnos"] <= 0:
                            del actor.modelo.efectos_arma[efecto]
                        if self.resultado:
                            break
            else:
                self._accion_aliado(actor)
            self._vista(actor)
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
        for actor in self.party + self.enemigos:
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
        if self.tablero:
            self.tablero.expirar(self.ronda)
            self._vista()
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
