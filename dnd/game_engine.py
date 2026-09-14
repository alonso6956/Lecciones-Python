import random
from combat_stats import defensa_total, tirar_dano, armas_ataque
from weapon_effects import armadura_tras_penetracion, modificar_golpe, activar_afijo, ticks_afijos

from character import Personaje
from character_roster import CharacterRoster, deserializar_personaje, serializar_personaje, migrar_personaje
from progression import comprobar_hitos
from combat_formulas import (
    aplicar_mitigacion_dano,
    calcular_bonus_hack_slash,
    calcular_dano_habilidad,
    calcular_mitigacion_armadura,
)
from enemies import Enemigo, elegir_enemigo
from habilidades import habilidad_factory
from inventario import Inventario
from item import Arma, Armadura, Consumible, Secundario
from item_factory import item_factory
from items import (
    objetos,
    obtener_dano_arma,
)
from initiative import (
    calculateTurnOrder,
    getActionPoints,
    jugador_rompe_prioridad_rapida,
)
from level_system import SistemaNiveles
from state import (
    construir_estado,
    estados_activos_enemigo,
    estados_activos_jugador,
)


class ErrorJuego(ValueError):
    pass


class MotorJuego:
    HABITACIONES_TOTALES = 50
    ENERGIA_MAXIMA = Personaje.ENERGIA_BASE

    @property
    def energia_maxima(self):
        return self.jugador.energia_maxima if self.jugador else self.ENERGIA_MAXIMA

    def __init__(self, rng=None, roster=None):
        self.roster = roster if roster is not None else CharacterRoster()
        self.rng = rng or random.Random()
        self.sistema_niveles = SistemaNiveles(
            nivel_maximo=Personaje.NIVEL_MAXIMO,
        )
        self.reiniciar()

    def reiniciar(self):
        self.jugador = None
        self.fase = "menu"
        self.resultado = None
        self.numero_habitacion = 0
        self.habitacion_anterior = None
        self.enemigo_actual = None
        self.energia = self.energia_maxima
        self.enemigo_dano = 0
        self.enemigo_habilidad = None
        self.aturdimiento_jugador = 0
        self.intencion = None
        self.turno_global = 0
        self.ultimo_actor = None
        self.acumuladores_velocidad = {"jugador": 0, "enemigo": 0}
        self.is_defending = False
        self.contraataque_disponible = False
        self.cooldowns_habilidades = {}
        self.efectos_habilidades = {}
        self.registro = []
        self.eventos = []
        self.siguiente_evento_id = 1

    def nueva_partida(self):
        self.reiniciar()
        self.fase = "inicio"
        self.registro = ["Escribe un nombre para comenzar con una espada básica."]

    def iniciar(self, nombre, arma=None):
        self._exigir_fase("inicio")
        if not isinstance(nombre, str):
            raise ErrorJuego("Debes escribir un nombre.")
        nombre = nombre.strip()[:30]
        if not nombre:
            raise ErrorJuego("Debes escribir un nombre.")
        jugador = Personaje(nombre, "espada_basica", {"fuerza": 1, "destreza": 1, "constitucion": 1})
        # El checkpoint inicial permite volver a intentar la expedición.
        self.roster.save_to_disk(jugador)
        self.cargar_personaje(jugador.id)

    def cargar_personaje(self, personaje_id):
        self.importar_guardado({"jugador": self.roster.obtener(personaje_id)})

    def abandonar(self):
        self.reiniciar()
        self.numero_habitacion = 1
        self._registrar("Vuelves al menú. Tu personaje conserva el último guardado y comenzará en la habitación 1.")

    def elegir_clase(self, clase):
        if not self.jugador or self.fase not in {"nivel", "transicion"}:
            raise ErrorJuego("No puedes elegir clase en este momento.")
        self.jugador.elegir_clase(clase)
        self._registrar(f"Eliges la clase {clase}.")
        self._emitir_evento("clase_elegida", categoria="progresion", clase=clase)
        if self.fase == "nivel":
            self._fase_tras_mejoras()

    def _fase_tras_mejoras(self):
        if self.jugador.puntos_estadistica or (self.jugador.nivel >= 10 and self.jugador.clase is None):
            self.fase = "nivel"
        else:
            self.fase = "combate" if self.enemigo_actual and self.enemigo_actual.hp > 0 else "transicion"

    def _procesar_hitos(self, hitos):
        for hito in hitos:
            mensaje = ("Alcanzas el nivel 10: puedes elegir tu clase." if hito == "elegir_clase"
                       else "Nivel 30: una chispa latente te infesta.")
            self._registrar(mensaje)
            self._emitir_evento(hito, categoria="progresion", actor="jugador", mensaje=mensaje)

    def _registrar(self, mensaje):
        self.registro.append(mensaje)
        self.registro = self.registro[-80:]

    def _emitir_evento(
        self,
        tipo,
        *,
        categoria="combate",
        actor=None,
        objetivo=None,
        mensaje=None,
        **datos,
    ):
        """Publica datos visuales sin convertir la interfaz en autoridad."""
        evento = {
            "id": self.siguiente_evento_id,
            "categoria": categoria,
            "tipo": tipo,
            "actor": actor,
            "objetivo": objetivo,
            "turno": self.turno_global,
            "habitacion": self.numero_habitacion,
            "mensaje": mensaje,
            "datos": datos,
        }
        self.siguiente_evento_id += 1
        self.eventos.append(evento)
        self.eventos = self.eventos[-120:]
        return evento

    def _registrar_evento(self, tipo, mensaje, **datos_evento):
        self._registrar(f"[[{tipo}]] {mensaje}")
        self._emitir_evento(tipo, mensaje=mensaje, **datos_evento)

    def _exigir_fase(self, fase):
        if self.fase != fase:
            raise ErrorJuego("Esa acción no está disponible ahora.")

    def _elegir_habitacion(self):
        return "combate"

    def siguiente_habitacion(self):
        if self.fase != "transicion":
            raise ErrorJuego("Todavía no puedes avanzar.")
        if self.jugador.nivel >= 10 and self.jugador.clase is None:
            raise ErrorJuego("Elige tu clase antes de continuar.")
        self.roster.save_to_disk(self.jugador)
        self._registrar("Progreso guardado al completar la habitación.")
        if self.numero_habitacion >= self.HABITACIONES_TOTALES:
            self._terminar("victoria")
            return
        self.numero_habitacion += 1
        tipo = self._elegir_habitacion()
        self.habitacion_anterior = tipo
        self._registrar(f"Habitación {self.numero_habitacion}: {tipo}.")
        self._iniciar_combate()

    def _iniciar_combate(self):
        enemigo_anterior = self.enemigo_actual
        intencion_anterior = self.intencion
        self.enemigo_actual = elegir_enemigo(self.numero_habitacion, self.rng)
        try:
            # La preparación debe completarse antes de publicar fase combate.
            # Si falla el catálogo, restauramos el estado y nunca enviamos
            # un enemigo parcialmente creado con intención null.
            self._preparar_turno_enemigo()
        except (KeyError, ValueError):
            self.enemigo_actual = enemigo_anterior
            self.intencion = intencion_anterior
            raise
        self.energia = self.energia_maxima
        self.turno_global = 0
        self.ultimo_actor = None
        self.acumuladores_velocidad = {"jugador": 0, "enemigo": 0}
        self.is_defending = False
        self.contraataque_disponible = False
        self.cooldowns_habilidades = {
            habilidad.id: 0 for habilidad in habilidad_factory.todas()
        }
        self.efectos_habilidades = {
            habilidad.id: 0 for habilidad in habilidad_factory.todas()
        }
        self.jugador.establecer_mitigar_dano(0)
        self.fase = "combate"
        self._registrar(
            f"Aparece un {self.enemigo_actual.nombre} con "
            f"{self.enemigo_actual.arma}."
        )

    def _preparar_turno_enemigo(self):
        enemigo = self.enemigo_actual
        self.enemigo_habilidad = None

        disponibles = [
            habilidad_id
            for habilidad_id in enemigo.habilidades
            if enemigo.puede_usar_habilidad(habilidad_id)
            and enemigo.cooldowns_habilidad.get(habilidad_id, 0) == 0
        ]
        if (
            "mitigar_dano" in disponibles
            and enemigo.hp <= enemigo.salud_maxima * 0.75
            and not enemigo.mitigar_dano_activo
        ):
            self.enemigo_habilidad = "mitigar_dano"
        elif "golpe_aplastante" in disponibles:
            self.enemigo_habilidad = "golpe_aplastante"

        if self.enemigo_habilidad:
            habilidad = habilidad_factory.crear(self.enemigo_habilidad)
            self.intencion = f"habilidad:{habilidad.nombre}"
            if not habilidad.causa_dano:
                self.enemigo_dano = 0
                return
            self.enemigo_dano = tirar_dano(enemigo, self.rng)
            return

        self.enemigo_dano = tirar_dano(enemigo, self.rng)
        # La intención no depende de la tirada de daño ni de su escalado.
        # Un poderoso exige una acción de otro tipo antes de poder repetirse.
        tirada = self.rng.random()
        self.intencion = ("rápido" if tirada < .25 else
                          "poderoso" if tirada >= .85 and not enemigo.ultimo_ataque_poderoso else "normal")
        if self.intencion == "poderoso":
            self.enemigo_dano *= 1.5

    def _dano_total_jugador(self):
        return tirar_dano(self.jugador, self.rng)

    def _defensa_total_jugador(self):
        return defensa_total(self.jugador)

    def _evasion_total_jugador(self):
        """Incluye la evasión temporal de Paso veloz cuando está activa."""
        if self.efectos_habilidades.get("paso_veloz", 0) > 0:
            habilidad = habilidad_factory.crear("paso_veloz")
            return habilidad.calcular_efecto(
                self.jugador.nivel_habilidad("paso_veloz"),
                self.jugador.destreza_total,
            )
        return self.jugador.evasion

    def _aplicar_sangrado(self, numero_ataque=None):
        pasiva = self.jugador.pasiva_clase
        if not pasiva or pasiva.efecto != "doble_ataque_sangrado":
            return
        renovado = self.enemigo_actual.sangrado_turnos > 0
        self.enemigo_actual.sangrado_dano = pasiva.dano_sangrado
        self.enemigo_actual.sangrado_turnos = pasiva.duracion_turnos
        origen = f" por el ataque {numero_ataque}" if numero_ataque else ""
        self._registrar_evento(
            "sangrado",
            f"Sangrado {'renovado' if renovado else 'aplicado'}{origen}: "
            f"causará {pasiva.dano_sangrado} de daño "
            "al final del turno enemigo.",
            actor="jugador",
            objetivo="enemigo",
            accion="renovado" if renovado else "aplicado",
            dano=pasiva.dano_sangrado,
            duracion=pasiva.duracion_turnos,
            golpe=numero_ataque,
        )

    def _resolver_sangrado(self):
        enemigo = self.enemigo_actual
        for efecto, dano in ticks_afijos(enemigo):
            self._registrar(f"{efecto.capitalize()} causa {dano} de daño al enemigo.")
            self._emitir_evento("dano", actor="jugador", objetivo="enemigo", dano=dano,
                               fuente=efecto, hp_restante=max(0, enemigo.hp))
        if enemigo.sangrado_turnos <= 0 or enemigo.hp <= 0:
            return
        dano = enemigo.sangrado_dano
        enemigo.hp = max(0, enemigo.hp - dano)
        enemigo.sangrado_turnos = 0
        self._registrar_evento(
            "sangrado",
            f"El sangrado causa {dano} de daño sin mitigación.",
            actor="jugador",
            objetivo="enemigo",
            accion="dano",
            dano=dano,
            hp_restante=max(0, enemigo.hp),
        )

    def _defensa_del_golpe(self, atacante, defensor, dano, **opciones):
        from defense_system import resolver_defensa
        resultado = resolver_defensa(atacante, defensor, dano, rng=self.rng, **opciones)
        actor = "jugador" if defensor is self.jugador else "enemigo"
        objetivo = "enemigo" if actor == "jugador" else "jugador"
        if resultado["ruptura"] and defensor is self.jugador:
            self.is_defending = False
            self._registrar_evento("ruptura_guardia", "La ruptura cancela Defender.", actor=objetivo, objetivo=actor)
        if resultado["parada"]:
            grado = resultado["parada"]
            texto = {"completa": "Parada completa: -50% de daño", "parcial": "Parada parcial: -25% de daño",
                     "debil": "Defensa débil: -10% de daño"}[grado]
            self._registrar_evento("parada", texto + ".", actor=actor, objetivo=objetivo,
                grado=grado, poder_parada=resultado["poder_parada"], presion_ataque=resultado["presion_ataque"])
        if resultado["absorbido"]:
            self._registrar_evento("bloqueo", f"El escudo absorbe {resultado['absorbido']:g} de daño.",
                actor=actor, objetivo=objetivo, absorbido=resultado["absorbido"], activo=resultado["bloqueo_activo"])
        if resultado["pierde_accion"]:
            if defensor is self.jugador:
                self.contraataque_disponible = True
            if atacante is self.enemigo_actual:
                atacante.acciones_perdidas = 1
            else:
                self.aturdimiento_jugador = max(1, self.aturdimiento_jugador)
        return resultado

    def _resolver_ataques_multiples(self, habilidad, nivel_habilidad):
        """Resuelve cada golpe del combo como un ataque completo e independiente."""
        impactos = 0
        esquivados = 0
        dano_total = 0
        golpes_realizados = 0
        pasiva = self.jugador.pasiva_clase
        escudo_enemigo = (
            item_factory.crear(self.enemigo_actual.secundario)
            if self.enemigo_actual.secundario
            else None
        )
        multiplicador_golpe = habilidad.multiplicador_dano(nivel_habilidad)
        for numero_golpe in range(1, habilidad.numero_golpes + 1):
            if self.enemigo_actual.hp <= 0:
                break
            golpes_realizados += 1
            dano_personaje = self._dano_total_jugador()
            dano_golpe = max(
                1,
                round(dano_personaje * multiplicador_golpe),
            )
            bonus_vida_faltante = 0
            if habilidad.id == "hack_slash" and numero_golpe == 3:
                bonus_vida_faltante = calcular_bonus_hack_slash(
                    self.enemigo_actual.hp,
                    self.enemigo_actual.salud_maxima,
                    nivel_habilidad,
                )
                dano_golpe = max(1, round(dano_golpe * (1 + bonus_vida_faltante)))
            if self.rng.random() < self.enemigo_actual.evasion:
                esquivados += 1
                self._registrar(
                    f"{habilidad.nombre}: golpe {numero_golpe}/"
                    f"{habilidad.numero_golpes} esquivado."
                )
                self._emitir_evento(
                    "esquiva",
                    actor="enemigo",
                    objetivo="jugador",
                    habilidad=habilidad.id,
                    golpe=numero_golpe,
                    golpes_totales=habilidad.numero_golpes,
                )
                continue

            if bonus_vida_faltante:
                self._registrar(
                    "El tercer golpe de Hack and Slash aprovecha la vida baja "
                    "del enemigo y causa daño adicional."
                )
                self._emitir_evento(
                    "bonus_vida_faltante",
                    actor="jugador",
                    objetivo="enemigo",
                    habilidad=habilidad.id,
                    golpe=numero_golpe,
                    bonus=bonus_vida_faltante,
                )

            critico = bool(
                pasiva
                and pasiva.efecto == "critico"
                and self.rng.random() < pasiva.probabilidad
            )
            if critico:
                dano_golpe = pasiva.calcular_critico(dano_golpe)
            dano_golpe, critico_arma = modificar_golpe(self.jugador, self.enemigo_actual, dano_golpe, self.rng)
            critico = critico or critico_arma

            defensa_golpe = self._defensa_del_golpe(self.jugador, self.enemigo_actual, dano_golpe, ataque=habilidad)
            dano_golpe = defensa_golpe["dano"]
            bloqueo_exitoso = defensa_golpe["absorbido"] > 0
            recibido = max(
                0,
                round(
                    aplicar_mitigacion_dano(
                        dano_golpe,
                        armadura=armadura_tras_penetracion(self.jugador, self.enemigo_actual.defensa_total),
                    )
                ),
            )
            reduccion = self.enemigo_actual.reduccion_dano_activa()
            if reduccion:
                recibido = max(0, round(recibido * (1 - reduccion)))

            if critico:
                self._registrar_evento(
                    "critico",
                    f"¡Golpe crítico! El golpe {numero_golpe} causa "
                    f"{recibido} de daño.",
                    actor="jugador",
                    objetivo="enemigo",
                    habilidad=habilidad.id,
                    golpe=numero_golpe,
                    dano=recibido,
                )

            self.enemigo_actual.hp = max(0, self.enemigo_actual.hp - recibido)
            activar_afijo(self.jugador, self.enemigo_actual, self.rng)
            impactos += 1
            dano_total += recibido
            self._registrar(
                f"{habilidad.nombre}: golpe {numero_golpe}/"
                f"{habilidad.numero_golpes} causa {recibido} de daño."
            )
            self._emitir_evento(
                "dano",
                actor="jugador",
                objetivo="enemigo",
                habilidad=habilidad.id,
                golpe=numero_golpe,
                golpes_totales=habilidad.numero_golpes,
                dano=recibido,
                critico=critico,
                bloqueo=bloqueo_exitoso,
                hp_restante=max(0, self.enemigo_actual.hp),
            )
        self._registrar(
            f"Usas {habilidad.nombre} (nivel {nivel_habilidad}): "
            f"{impactos}/{golpes_realizados} golpes impactan y causan "
            f"{dano_total} de daño"
            + (
                f"; {esquivados} "
                f"{'fue esquivado' if esquivados == 1 else 'fueron esquivados'}."
                if esquivados
                else "."
            )
        )
        self._emitir_evento(
            "combo_resuelto",
            actor="jugador",
            objetivo="enemigo",
            habilidad=habilidad.id,
            nivel=nivel_habilidad,
            golpes=golpes_realizados,
            impactos=impactos,
            esquivados=esquivados,
            dano_total=dano_total,
        )

    def _ataque_basico(self):
        """Las manos resuelven daño, crítico, bloqueo, penetración y afijos propios."""
        golpes = armas_ataque(self.jugador)
        pasiva = self.jugador.pasiva_clase
        if len(golpes) == 1 and pasiva and pasiva.efecto == "doble_ataque_sangrado":
            golpes *= pasiva.numero_ataques
        enemigo = self.enemigo_actual
        escudo = item_factory.crear(enemigo.secundario) if enemigo.secundario else None
        for numero, (arma, factor) in enumerate(golpes, 1):
            if enemigo.hp <= 0:
                break
            if self.rng.random() < enemigo.evasion:
                self._registrar_evento("esquiva", f"El enemigo esquiva el golpe de {arma.nombre}.",
                    actor="enemigo", objetivo="jugador", golpe=numero, golpes_totales=len(golpes))
                continue
            ignora = bool(pasiva and pasiva.efecto == "ignorar_defensa" and pasiva.ignora_defensa(self.rng.random()))
            bruto = tirar_dano(self.jugador, self.rng, arma) * factor
            critico_pasiva = bool(pasiva and pasiva.efecto == "critico" and self.rng.random() < pasiva.probabilidad)
            if critico_pasiva:
                bruto = pasiva.calcular_critico(bruto)
            bruto, critico = modificar_golpe(self.jugador, enemigo, bruto, self.rng, arma)
            defensa_golpe = self._defensa_del_golpe(self.jugador, enemigo, bruto, arma=arma, ignora=ignora)
            bloqueado = defensa_golpe["absorbido"] > 0
            dano = aplicar_mitigacion_dano(defensa_golpe["dano"],
                armadura=0 if ignora else armadura_tras_penetracion(self.jugador, enemigo.defensa_total, arma))
            dano = max(0, round(dano * (1 - enemigo.reduccion_dano_activa())))
            enemigo.hp = max(0, enemigo.hp - dano)
            activar_afijo(self.jugador, enemigo, self.rng, arma)
            self._registrar_evento("dano", f"{arma.nombre}: golpe {numero}/{len(golpes)} causa {dano} de daño.",
                actor="jugador", objetivo="enemigo", golpe=numero, golpes_totales=len(golpes),
                arma_id=arma.id, dano=dano, critico=critico or critico_pasiva,
                bloqueo=bloqueado, hp_restante=enemigo.hp)
            if pasiva and pasiva.efecto == "doble_ataque_sangrado":
                self._aplicar_sangrado(numero)

    def _accion_jugador(self, accion, habilidad_id=None):
        # isDefending vence al comenzar una nueva acción propia, nunca cuando
        # el jugador recibe un golpe. Si vuelve a defender, se reactiva para
        # todos los ataques que ocurran antes de su siguiente acción.
        self.is_defending = False
        contraataque = getattr(self, "contraataque_disponible", False)
        self.contraataque_disponible = False
        dano = 0
        defensa_extra = 0
        ataques_evitar = 0
        dano_ya_mitigado = False
        habilidad = None
        defensa_ignorada = False

        if accion == "atacar":
            self.energia = min(self.energia_maxima, self.energia + 1)
            self._ataque_basico()
            return 0, 0
        elif accion == "defender":
            self.energia = min(self.energia_maxima, self.energia + 1)
            self.is_defending = True
            self._registrar(
                "Adoptas una defensa activa con tu arma o escudo y recuperas energía."
            )
            return defensa_extra, ataques_evitar
        else:
            habilidad = habilidad_factory.crear(habilidad_id)
            nivel_habilidad = self.jugador.nivel_habilidad(habilidad_id)
            if nivel_habilidad < 1:
                raise ErrorJuego("La habilidad todavía está bloqueada.")
            if not self.jugador.puede_usar_habilidad(habilidad_id):
                raise ErrorJuego("La habilidad no pertenece a tu clase o no está aprendida.")
            if self.cooldowns_habilidades.get(habilidad_id, 0) > 0:
                self._registrar(
                    "La habilidad entró en cooldown: realizas un ataque normal."
                )
                return self._accion_jugador("atacar")
            if (
                habilidad.bloquear_mientras_activa
                and self.jugador.mitigar_dano_activo
            ):
                raise ErrorJuego(
                    f"{habilidad.nombre} ya está activa durante "
                    f"{self.jugador.mitigar_dano_turnos} turno(s)."
                )
            if self.energia < habilidad.costo_energia:
                self._registrar(
                    "Sin energía para repetir la habilidad: realizas un ataque normal."
                )
                return self._accion_jugador("atacar")
            self.energia -= habilidad.costo_energia
            valor_atributo = self.jugador.estadistica_total(
                habilidad.atributo_escalado
            )
            if habilidad.tipo_efecto == "ataques_multiples":
                self.cooldowns_habilidades[habilidad_id] = (
                    habilidad.cooldown_turnos
                )
                self._resolver_ataques_multiples(habilidad, nivel_habilidad)
                return defensa_extra, ataques_evitar
            if habilidad.causa_dano:
                pasiva = self.jugador.pasiva_clase
                defensa_ignorada = bool(
                    pasiva
                    and pasiva.efecto == "ignorar_defensa"
                    and pasiva.ignora_defensa(self.rng.random())
                )
                escudo = self.jugador.inventario.secundario_equipado
                from defense_system import durabilidad_escudo
                bloqueo_exitoso = bool(habilidad.id == "bloqueo_contraataque" and contraataque
                    and durabilidad_escudo(self.jugador) > 0)
                if bloqueo_exitoso:
                    self._registrar_evento(
                        "bloqueo",
                        "¡Bloqueo! Bloqueo y contraataque obtiene "
                        f"+{round(escudo.bloqueo_activo * 100)}% "
                        "de daño adicional.",
                        actor="jugador",
                        objetivo="enemigo",
                        habilidad=habilidad.id,
                        porcentaje_dano=escudo.bloqueo_activo,
                    )
                dano = calcular_dano_habilidad(
                    dano_base=self.jugador.DANO_BASE,
                    dano_arma=self.rng.randint(*self.jugador.inventario.arma_equipada.ataque),
                    habilidad=habilidad,
                    nivel_habilidad=nivel_habilidad,
                    valor_atributo=valor_atributo,
                    fuerza=self.jugador.fuerza_total,
                    escalado_arma=self.jugador.inventario.arma_equipada.coeficiente_fuerza,
                    defensa_objetivo=0, solo_bruto=True,
                    constitucion_objetivo=self.enemigo_actual.constitucion,
                    bloqueo_exitoso=bloqueo_exitoso,
                    porcentaje_dano_bloqueado=(
                        getattr(escudo, "bloqueo_activo", 0)
                    ),
                )
                dano_ya_mitigado = True
            efecto = habilidad.calcular_efecto(
                nivel_habilidad,
                valor_atributo,
                self.jugador.inventario.secundario_equipado,
            )
            if habilidad.tipo_efecto == "defensa":
                defensa_extra = round(efecto)
            elif habilidad.tipo_efecto == "reduccion_dano":
                self.jugador.activar_mitigar_dano(habilidad.duracion_turnos)
                self.efectos_habilidades[habilidad_id] = habilidad.duracion_turnos
            elif habilidad.tipo_efecto == "evasion_temporal":
                self.efectos_habilidades[habilidad_id] = habilidad.duracion_turnos
                self.cooldowns_habilidades[habilidad_id] = (
                    habilidad.cooldown_turnos
                )
                self._registrar(
                    f"Usas {habilidad.nombre}: tu evasión sube al "
                    f"{round(efecto * 100)}% hasta el final del turno enemigo."
                )
                return defensa_extra, ataques_evitar
            elif habilidad.tipo_efecto in {"no_escape", "bloqueo_contraataque"}:
                pass
            else:
                ataques_evitar = int(self.rng.random() < efecto)
            self.cooldowns_habilidades[habilidad_id] = habilidad.cooldown_turnos
            if not habilidad.causa_dano:
                porcentaje = round(efecto * 100)
                self._registrar(
                    f"Usas {habilidad.nombre} (nivel {nivel_habilidad}): reduces "
                    f"el daño recibido un {porcentaje}% durante "
                    f"{habilidad.duracion_turnos} turnos."
                )
                return defensa_extra, ataques_evitar
            mensaje = f"Usas {habilidad.nombre} (nivel {nivel_habilidad}) y"

        pasiva = self.jugador.pasiva_clase
        if habilidad is None:
            defensa_ignorada = bool(
                pasiva
                and pasiva.efecto == "ignorar_defensa"
                and pasiva.ignora_defensa(self.rng.random())
            )

        recibido_enemigo = dano
        reduccion_enemiga = self.enemigo_actual.reduccion_dano_activa()
        if defensa_ignorada:
            self._registrar_evento(
                "defensa_ignorada",
                "¡Defensa ignorada! El ataque atraviesa armadura y escudo.",
                actor="jugador",
                objetivo="enemigo",
                arma=self.jugador.arma,
            )
        numero_ataques = (
            pasiva.numero_ataques
            if pasiva and pasiva.efecto == "doble_ataque_sangrado"
            else 1
        )
        impactos = 0
        dano_total = 0
        for numero_ataque in range(1, numero_ataques + 1):
            if self.enemigo_actual.hp <= 0:
                break
            segunda_daga_normal = bool(
                habilidad
                and habilidad.id == "corte_certero"
                and numero_ataque == 2
            )
            dano_ataque = recibido_enemigo
            mensaje_ataque = mensaje
            ataque_normal_independiente = bool(
                segunda_daga_normal
                or habilidad is None
            )
            if ataque_normal_independiente:
                dano_ataque = (
                    dano
                    if habilidad is None and numero_ataques == 1
                    else self._dano_total_jugador()
                )
                if segunda_daga_normal:
                    mensaje_ataque = "La segunda daga ataca normalmente"
            if (
                (
                    segunda_daga_normal
                    or not getattr(habilidad, "inesquivable", False)
                )
                and self.rng.random() < self.enemigo_actual.evasion
            ):
                self._registrar(
                    f"{mensaje_ataque}: ataque "
                    f"{numero_ataque}/{numero_ataques} esquivado."
                )
                self._emitir_evento(
                    "esquiva",
                    actor="enemigo",
                    objetivo="jugador",
                    habilidad=habilidad.id if habilidad else None,
                    golpe=numero_ataque,
                    golpes_totales=numero_ataques,
                )
                continue
            critico = bool(
                pasiva
                and pasiva.efecto == "critico"
                and self.rng.random() < pasiva.probabilidad
            )
            if critico:
                dano_ataque = pasiva.calcular_critico(dano_ataque)
            dano_ataque, critico_arma = modificar_golpe(self.jugador, self.enemigo_actual, dano_ataque, self.rng)
            critico = critico or critico_arma

            defensa_golpe = self._defensa_del_golpe(self.jugador, self.enemigo_actual, dano_ataque,
                ataque=None if segunda_daga_normal else habilidad, ignora=defensa_ignorada)
            bloqueo_enemigo = defensa_golpe["absorbido"] > 0
            dano_ataque = max(0, round(aplicar_mitigacion_dano(defensa_golpe["dano"],
                armadura=0 if defensa_ignorada else armadura_tras_penetracion(self.jugador, self.enemigo_actual.defensa_total))
                * (1 - reduccion_enemiga)))

            if critico:
                self._registrar_evento(
                    "critico",
                    f"¡Golpe crítico! {dano_ataque} de daño.",
                    actor="jugador",
                    objetivo="enemigo",
                    habilidad=habilidad.id if habilidad else None,
                    golpe=numero_ataque,
                    dano=dano_ataque,
                )
            self.enemigo_actual.hp = max(0, self.enemigo_actual.hp - dano_ataque)
            activar_afijo(self.jugador, self.enemigo_actual, self.rng)
            impactos += 1
            dano_total += dano_ataque
            self._registrar(
                f"{mensaje_ataque}: ataque {numero_ataque}/{numero_ataques} causa "
                f"{dano_ataque} de daño."
            )
            self._emitir_evento(
                "dano",
                actor="jugador",
                objetivo="enemigo",
                habilidad=habilidad.id if habilidad else None,
                golpe=numero_ataque,
                golpes_totales=numero_ataques,
                dano=dano_ataque,
                critico=critico,
                bloqueo=bloqueo_enemigo,
                defensa_ignorada=defensa_ignorada,
                hp_restante=max(0, self.enemigo_actual.hp),
            )
            if numero_ataques > 1 and self.enemigo_actual.hp > 0:
                self._aplicar_sangrado(numero_ataque)
        if impactos and numero_ataques > 1:
            self._registrar(
                f"Doble ataque: {impactos}/{numero_ataques} impactos, "
                f"{dano_total} de daño total."
            )
        return defensa_extra, ataques_evitar

    def _actualizar_habilidades_enemigo(self, habilidad_usada=None):
        enemigo = self.enemigo_actual
        enemigo.cooldowns_habilidad = {
            habilidad_id: max(0, turnos - 1)
            for habilidad_id, turnos in enemigo.cooldowns_habilidad.items()
        }
        enemigo.efectos_habilidad = {
            habilidad_id: max(0, turnos - 1)
            for habilidad_id, turnos in enemigo.efectos_habilidad.items()
        }
        if habilidad_usada:
            habilidad = habilidad_factory.crear(habilidad_usada)
            enemigo.cooldowns_habilidad[habilidad_usada] = habilidad.cooldown_turnos

    def _accion_enemigo(self, defensa_extra):
        if self.enemigo_actual.acciones_perdidas:
            self.enemigo_actual.acciones_perdidas -= 1
            self._registrar_evento("accion_perdida", "El enemigo pierde su siguiente acción por la defensa activa.",
                actor="enemigo", objetivo="enemigo")
            self._actualizar_habilidades_enemigo()
            self._preparar_turno_enemigo()
            return
        habilidad_id = self.enemigo_habilidad
        habilidad = habilidad_factory.crear(habilidad_id) if habilidad_id else None
        self.enemigo_actual.ultimo_ataque_poderoso = self.intencion == "poderoso"
        if habilidad and not habilidad.causa_dano:
            if (
                habilidad.bloquear_mientras_activa
                and self.enemigo_actual.habilidad_activa(habilidad_id)
            ):
                # Una intención restaurada o desactualizada no consume la acción:
                # se elige y ejecuta otra inmediatamente.
                self._preparar_turno_enemigo()
                return self._accion_enemigo(defensa_extra)
            self._actualizar_habilidades_enemigo(habilidad_id)
            self.enemigo_actual.efectos_habilidad[
                habilidad_id
            ] = habilidad.duracion_turnos
            efecto = habilidad.calcular_efecto(
                self.enemigo_actual.nivel_habilidad(habilidad_id),
                getattr(self.enemigo_actual, habilidad.atributo_escalado),
                (
                    item_factory.crear(self.enemigo_actual.secundario)
                    if self.enemigo_actual.secundario
                    else None
                ),
            )
            self._registrar(
                f"El {self.enemigo_actual.nombre} usa {habilidad.nombre}: "
                f"reduce un {round(efecto * 100)}% del daño durante "
                f"{habilidad.duracion_turnos} turnos."
            )
            self._emitir_evento(
                "efecto_activado",
                actor="enemigo",
                objetivo="enemigo",
                habilidad=habilidad.id,
                efecto=habilidad.tipo_efecto,
                valor=efecto,
                duracion=habilidad.duracion_turnos,
            )
            self._preparar_turno_enemigo()
            return

        if self.rng.random() < self._evasion_total_jugador():
            self._registrar("¡Esquivaste el ataque!")
            self._emitir_evento(
                "esquiva",
                actor="jugador",
                objetivo="enemigo",
                habilidad=habilidad.id if habilidad else None,
            )
            self._actualizar_habilidades_enemigo(habilidad_id)
            self._preparar_turno_enemigo()
            return
        if habilidad:
            bruto = calcular_dano_habilidad(
                dano_base=self.enemigo_actual.calcular_dano_base(), dano_arma=obtener_dano_arma(self.enemigo_actual.arma, self.rng),
                habilidad=habilidad, nivel_habilidad=self.enemigo_actual.nivel_habilidad(habilidad_id),
                valor_atributo=getattr(self.enemigo_actual, habilidad.atributo_escalado),
                defensa_objetivo=0, solo_bruto=True, fuerza=self.enemigo_actual.fuerza,
                escalado_arma=item_factory.crear(self.enemigo_actual.arma).coeficiente_fuerza,
                constitucion_objetivo=self.jugador.constitucion_total)
        else:
            bruto = self.enemigo_dano
        defensa_golpe = self._defensa_del_golpe(self.enemigo_actual, self.jugador, bruto,
            defendiendo=self.is_defending, rapido=self.intencion == "rápido" or getattr(habilidad, "rapido", False),
            poderoso=self.intencion == "poderoso", ataque=habilidad)
        bloqueo_exitoso = defensa_golpe["absorbido"] > 0
        defensa = self._defensa_total_jugador() + defensa_extra
        dano_tras_defensa = aplicar_mitigacion_dano(defensa_golpe["dano"],
            armadura=armadura_tras_penetracion(self.enemigo_actual, defensa))
        reduccion = 0
        for efecto_id, turnos in self.efectos_habilidades.items():
            if turnos <= 0:
                continue
            habilidad_efecto = habilidad_factory.crear(efecto_id)
            if habilidad_efecto.tipo_efecto != "reduccion_dano":
                continue
            nivel = self.jugador.nivel_habilidad(efecto_id)
            atributo = self.jugador.estadistica_total(
                habilidad_efecto.atributo_escalado
            )
            reduccion += habilidad_efecto.calcular_efecto(
                nivel,
                atributo,
                self.jugador.inventario.secundario_equipado,
            )
        reduccion = min(0.90, reduccion)
        recibido = max(0, round(dano_tras_defensa * (1 - reduccion)))
        self.jugador.hp -= recibido
        self._emitir_evento(
            "dano",
            actor="enemigo",
            objetivo="jugador",
            habilidad=habilidad.id if habilidad else None,
            dano=recibido,
            bloqueo=bloqueo_exitoso,
            reduccion=reduccion,
            hp_restante=max(0, self.jugador.hp),
        )
        if habilidad:
            self._registrar(
                f"El {self.enemigo_actual.nombre} usa {habilidad.nombre} y "
                f"causa {recibido} de daño."
            )
            efecto = habilidad.calcular_efecto(
                self.enemigo_actual.nivel_habilidad(habilidad_id),
                getattr(self.enemigo_actual, habilidad.atributo_escalado),
            )
            if habilidad.tipo_efecto == "aturdimiento" and self.rng.random() < efecto:
                self.aturdimiento_jugador = 1
                self._registrar_evento(
                    "aturdimiento",
                    "¡Aturdimiento! Perderás una acción.",
                    actor="enemigo",
                    objetivo="jugador",
                    habilidad=habilidad.id,
                    duracion=1,
                )
        else:
            self._registrar(
                f"El {self.enemigo_actual.nombre} ataca y causa {recibido} de daño."
            )
        self._actualizar_habilidades_enemigo(habilidad_id)
        if self.jugador.hp > 0:
            self._preparar_turno_enemigo()

    def actuar(self, accion, habilidad_id=None):
        self._exigir_fase("combate")
        if accion not in {"atacar", "defender", "habilidad", "usar_item"}:
            raise ErrorJuego("Acción de combate no válida.")

        if accion == "usar_item":
            try:
                consumible = item_factory.crear(habilidad_id)
            except ValueError as error:
                raise ErrorJuego(str(error)) from error
            if not isinstance(consumible, Consumible):
                raise ErrorJuego("Ese ítem no es consumible.")
            if self.jugador.inventario.cantidad(consumible.id) < 1:
                raise ErrorJuego("No tienes ese consumible.")
            if self.jugador.hp >= self.jugador.salud_maxima:
                raise ErrorJuego("Ya tienes la vida al máximo.")

        if accion == "habilidad" and habilidad_id == "paso_veloz":
            habilidad = habilidad_factory.crear(habilidad_id)
            if self.jugador.nivel_habilidad(habilidad_id) < 1:
                raise ErrorJuego("La habilidad todavía está bloqueada.")
            if not self.jugador.puede_usar_habilidad(habilidad_id):
                raise ErrorJuego("La habilidad no pertenece a tu clase.")
            if self.cooldowns_habilidades.get(habilidad_id, 0) > 0:
                raise ErrorJuego("La habilidad todavía está en cooldown.")
            if self.efectos_habilidades.get(habilidad_id, 0) > 0:
                raise ErrorJuego(f"{habilidad.nombre} ya está activa.")
            if self.energia < habilidad.costo_energia:
                raise ErrorJuego("No tienes energía suficiente.")

            self.energia -= habilidad.costo_energia
            self.cooldowns_habilidades[habilidad_id] = habilidad.cooldown_turnos
            self.efectos_habilidades[habilidad_id] = habilidad.duracion_turnos
            efecto = habilidad.calcular_efecto(
                self.jugador.nivel_habilidad(habilidad_id),
                self.jugador.destreza_total,
            )
            self._registrar(
                f"Usas {habilidad.nombre}: tu evasión sube al "
                f"{round(efecto * 100)}%. Elige ahora tu acción."
            )
            return

        nuevos_cooldowns = {
            identificador: max(0, turnos - 1)
            for identificador, turnos in self.cooldowns_habilidades.items()
        }
        nuevos_efectos = {
            identificador: (
                turnos
                if identificador == "paso_veloz"
                else max(0, turnos - 1)
            )
            for identificador, turnos in self.efectos_habilidades.items()
        }
        if accion == "habilidad":
            try:
                habilidad = habilidad_factory.crear(habilidad_id)
            except ValueError as error:
                raise ErrorJuego(str(error)) from error
            if self.jugador.nivel_habilidad(habilidad_id) < 1:
                raise ErrorJuego("La habilidad todavía está bloqueada.")
            if (
                habilidad.bloquear_mientras_activa
                and self.jugador.mitigar_dano_activo
            ):
                raise ErrorJuego(
                    f"{habilidad.nombre} ya está activa durante "
                    f"{self.jugador.mitigar_dano_turnos} turno(s)."
                )
            if not self.jugador.puede_usar_habilidad(habilidad_id):
                raise ErrorJuego("La habilidad no pertenece a tu clase.")
            if nuevos_cooldowns.get(habilidad_id, 0) > 0:
                raise ErrorJuego("La habilidad todavía está en cooldown.")
            if self.energia < habilidad.costo_energia:
                raise ErrorJuego("No tienes energía suficiente.")
        self.cooldowns_habilidades = nuevos_cooldowns
        self.efectos_habilidades = nuevos_efectos
        self.jugador.establecer_mitigar_dano(
            nuevos_efectos.get("mitigar_dano", 0)
        )

        self.turno_global += 1
        cola, self.acumuladores_velocidad = calculateTurnOrder(
            self.jugador.velocidad,
            self.enemigo_actual.velocidad,
            ataque_enemigo_rapido=self.intencion == "rápido",
            ataque_enemigo_poderoso=self.intencion == "poderoso",
            ultimo_actor=self.ultimo_actor,
            acumuladores=self.acumuladores_velocidad,
        )
        if accion == "usar_item":
            # La poción adelanta una acción propia, incluso frente a ataques
            # rápidos. Las acciones extra conservan su orden y su cantidad.
            cola.remove("jugador")
            cola.insert(0, "jugador")
        defensa_extra = 0
        ataques_evitar = 0
        item_usado = False
        self._registrar(
            f"Turno {self.turno_global}: "
            f"{cola.count('jugador')} acción(es) del jugador y "
            f"{cola.count('enemigo')} del enemigo."
        )
        self._emitir_evento(
            "turno_iniciado",
            actor="sistema",
            objetivo=None,
            accion=accion,
            habilidad=habilidad_id if accion == "habilidad" else None,
            acciones_jugador=cola.count("jugador"),
            acciones_enemigo=cola.count("enemigo"),
            orden=list(cola),
        )

        for entidad in cola:
            self.ultimo_actor = entidad
            modelo = self.jugador if entidad == "jugador" else self.enemigo_actual
            recuperado = modelo.regenerar()
            if recuperado:
                self._registrar_evento("curacion", f"{modelo.nombre} regenera {recuperado:g} HP.",
                    actor=entidad, objetivo=entidad, cantidad=recuperado, fuente="regeneracion", hp_restante=modelo.hp)
            if entidad == "jugador":
                if self.aturdimiento_jugador:
                    self.aturdimiento_jugador -= 1
                    self.is_defending = False
                    self.contraataque_disponible = False
                    self._registrar_evento(
                        "aturdimiento",
                        "Estás aturdido y pierdes esta acción.",
                        actor="jugador",
                        objetivo="jugador",
                        accion="accion_perdida",
                        duracion_restante=self.aturdimiento_jugador,
                    )
                    continue
                if accion == "usar_item" and not item_usado:
                    try:
                        item, recuperado = self.jugador.inventario.usar(
                            habilidad_id,
                            self.jugador,
                        )
                    except ValueError as error:
                        raise ErrorJuego(str(error)) from error
                    item_usado = True
                    self.is_defending = False
                    self.contraataque_disponible = False
                    self._registrar(
                        f"Usas {item.nombre} y recuperas {recuperado} de vida."
                    )
                    self._emitir_evento(
                        "curacion",
                        actor="jugador",
                        objetivo="jugador",
                        item=item.id,
                        cantidad=recuperado,
                        hp_restante=self.jugador.hp,
                    )
                    continue
                if accion == "usar_item":
                    # La poción ocupa solamente la primera acción disponible;
                    # cualquier acción extra por Velocidad es un ataque normal.
                    bonus, evita = self._accion_jugador("atacar")
                elif (
                    accion == "habilidad"
                    and (
                        (
                            habilidad.bloquear_mientras_activa
                            and self.jugador.mitigar_dano_activo
                        )
                        or (
                            not habilidad.consume_accion
                            and self.efectos_habilidades.get(habilidad.id, 0) > 0
                        )
                    )
                ):
                    # Si la Velocidad concede acciones extra, la postura se
                    # activa una sola vez y las restantes se usan para atacar.
                    bonus, evita = self._accion_jugador("atacar")
                else:
                    bonus, evita = self._accion_jugador(accion, habilidad_id)
                defensa_extra += bonus
                ataques_evitar += evita
                if self.enemigo_actual.hp <= 0:
                    self._resolver_victoria()
                    return
            elif ataques_evitar:
                ataques_evitar -= 1
                self._registrar(f"El {self.enemigo_actual.nombre} pierde su ataque.")
                self._preparar_turno_enemigo()
                self.efectos_habilidades["paso_veloz"] = 0
                self._resolver_sangrado()
                if self.enemigo_actual.hp <= 0:
                    self._resolver_victoria()
                    return
            else:
                self._accion_enemigo(defensa_extra)
                self.efectos_habilidades["paso_veloz"] = 0
                self._resolver_sangrado()
                if self.enemigo_actual.hp <= 0:
                    self._resolver_victoria()
                    return
                if self.jugador.hp <= 0:
                    self._preparar_respawn()
                    return

    def _preparar_respawn(self):
        """Conserva la progresión permanente antes de descartar la expedición."""
        nombre = self.jugador.nombre
        self.jugador.hp = 0
        self.fase = "muerte"
        # Si falla el disco, mantenemos al personaje para reintentar el guardado.
        self.roster.save_to_disk(self.jugador)
        self.reiniciar()
        self.numero_habitacion = 1
        self._registrar(f"{nombre} ha caído. Su experiencia, oro y progreso se han guardado. La próxima expedición comenzará en la habitación 1.")
        self._emitir_evento("derrota", categoria="progresion", actor="jugador")

    def respawn(self):
        self._exigir_fase("muerte")
        self._preparar_respawn()

    def _subir_nivel_jugador(self):
        energia_anterior = self.energia_maxima
        self._procesar_hitos(self.jugador.subir_nivel())
        aumento = self.energia_maxima - energia_anterior
        self.energia = min(self.energia_maxima, self.energia + aumento)
        if aumento:
            self._registrar(f"Tu energía máxima aumenta a {self.energia_maxima} (+{aumento}).")

    def _resolver_victoria(self):
        enemigo = self.enemigo_actual
        oro = self.rng.randint(*enemigo.oro)
        self.jugador.oro += oro
        self.jugador.ganar_exp(enemigo.exp)
        from crafting import botin_crafteo
        for item_id, cantidad in botin_crafteo(self.rng):
            item = self.jugador.inventario.recolectar(item_id, cantidad)
            self._registrar(f"Recoges {item.nombre} x{cantidad} para crafteo.")
        enemigo.hp = 0
        self._registrar(
            f"Derrotas al {enemigo.nombre}: +{oro} oro, +{enemigo.exp} EXP."
        )
        self._emitir_evento(
            "victoria",
            categoria="progresion",
            actor="jugador",
            objetivo="enemigo",
            enemigo=enemigo.nombre,
            oro=oro,
            experiencia=enemigo.exp,
        )
        if self.sistema_niveles.puede_subir(self.jugador):
            self._subir_nivel_jugador()
            self.fase = "nivel"
            self._registrar(
                f"Alcanzas el nivel {self.jugador.nivel}: recibes 1 punto "
                "de estadística y 1 de habilidad."
            )
        else:
            self.fase = "transicion"

    def subir_nivel(self, estadistica):
        self._exigir_fase("nivel")
        try:
            self.jugador.asignar_atributo(estadistica)
        except ValueError as error:
            raise ErrorJuego(str(error)) from error
        self._registrar(f"Asignas +1 a {estadistica}.")
        if self.sistema_niveles.puede_subir(self.jugador):
            self._subir_nivel_jugador()
            self._registrar(
                f"Alcanzas el nivel {self.jugador.nivel}: recibes otro punto "
                "de estadística y de habilidad."
            )
        else:
            self._fase_tras_mejoras()

    def mejorar_habilidad(self, habilidad_id):
        if self.fase in {"menu", "inicio", "combate", "muerte", "fin"}:
            raise ErrorJuego("No puedes mejorar habilidades en este momento.")
        try:
            habilidad = self.jugador.mejorar_habilidad(habilidad_id)
        except ValueError as error:
            raise ErrorJuego(str(error)) from error
        nivel = self.jugador.nivel_habilidad(habilidad_id)
        self._registrar(
            f"{habilidad.nombre} ahora es nivel "
            f"{nivel}/{habilidad.nivel_maximo}."
        )

    def equipar_item(self, item_id, slot=None):
        if self.fase in {"menu", "inicio", "combate", "muerte", "fin"}:
            raise ErrorJuego("No puedes cambiar equipo en este momento.")
        try:
            salud_anterior = self.jugador.salud_maxima
            item = self.jugador.inventario.equipar(item_id, self.jugador, slot)
            self.jugador.recalcular_por_equipo(salud_anterior)
        except ValueError as error:
            raise ErrorJuego(str(error)) from error
        self._registrar(f"Equipas {item.nombre}.")

    def desequipar_item(self, slot):
        if self.fase in {"menu", "inicio", "combate", "muerte", "fin"}:
            raise ErrorJuego("No puedes cambiar equipo en este momento.")
        try:
            salud_anterior = self.jugador.salud_maxima
            item = self.jugador.inventario.desequipar(slot)
            self.jugador.recalcular_por_equipo(salud_anterior)
        except ValueError as error:
            raise ErrorJuego(str(error)) from error
        self._registrar(f"Desequipas {item.nombre}.")

    def usar_item(self, item_id):
        if self.fase in {"menu", "inicio", "muerte", "fin"}:
            raise ErrorJuego("No puedes usar ese ítem en este momento.")
        if self.fase == "combate":
            return self.actuar("usar_item", item_id)
        try:
            item, recuperado = self.jugador.inventario.usar(item_id, self.jugador)
        except ValueError as error:
            raise ErrorJuego(str(error)) from error
        self._registrar(f"Usas {item.nombre} y recuperas {recuperado} de vida.")

    def comprar(self, categoria, nombre, personaje_id=None, cantidad=1):
        self._exigir_fase("menu")
        from shop import Shop
        return Shop(self.roster).comprar(personaje_id, categoria, nombre, cantidad)

    def _terminar(self, resultado):
        self.fase = "fin"
        self.resultado = resultado
        mensaje = "Encontraste la salida." if resultado == "victoria" else "Has muerto."
        self._registrar(mensaje)

    def exportar_guardado(self):
        """Solo progresión permanente. Nunca incluye vida, habitación o buffs."""
        if not self.jugador:
            raise ErrorJuego("No hay un personaje activo.")
        return {"jugador": serializar_personaje(self.jugador)}

    def importar_guardado(self, datos):
        entrada = datos.get("jugador")
        if not isinstance(entrada, dict):
            raise ErrorJuego("El guardado no contiene un personaje.")
        if "estadisticas" not in entrada:
            entrada = migrar_personaje(datos, "legacy/" + str(entrada.get("nombre", "")))
        jugador = deserializar_personaje(entrada)
        # Preparamos en otro motor para no publicar una carga parcial si falla.
        nuevo = MotorJuego(self.rng, self.roster)
        nuevo.jugador = jugador
        nuevo.numero_habitacion = 1
        nuevo.habitacion_anterior = "combate"
        nuevo._iniciar_combate()
        nuevo._procesar_hitos(comprobar_hitos(jugador))
        if jugador.puntos_estadistica or (jugador.nivel >= 10 and jugador.clase is None):
            nuevo.fase = "nivel"
        self.__dict__.update(nuevo.__dict__)

    def _estados_activos_jugador(self):
        return estados_activos_jugador(self)

    def _estados_activos_enemigo(self):
        return estados_activos_enemigo(self)

    def estado(self):
        return construir_estado(self)
