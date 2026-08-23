import random

from character import Personaje
from combat_formulas import calcular_dano_habilidad
from enemies import Enemigo, elegir_enemigo
from habilidades import habilidad_factory
from inventario import Inventario
from item import Arma, Armadura, Consumible, Secundario
from item_factory import item_factory
from items import (
    objetos,
    obtener_dano_arma,
)
from level_system import SistemaNiveles


class ErrorJuego(ValueError):
    pass


def getActionPoints(velocidad, velocidad_rival, acumulador=0):
    """Devuelve acciones y remanente de iniciativa para el siguiente ciclo.

    Se suman los puntos de ventaja en cada ciclo y cada 6 puntos acumulados
    generan una acción extra. Así, +2 Velocidad sigue dando una acción cada
    tres ciclos, mientras ventajas grandes actúan desde el primer ciclo en vez
    de quedar retenidas hasta un burst artificial en el turno global 3.
    """
    if acumulador < 0:
        raise ValueError("El acumulador de velocidad no puede ser negativo.")
    ventaja = max(0, velocidad - velocidad_rival)
    acciones_extra, remanente = divmod(acumulador + ventaja, 6)
    return 1 + acciones_extra, remanente


def jugador_rompe_prioridad_rapida(velocidad_jugador, velocidad_enemigo):
    """Solo una Velocidad estrictamente mayor rompe la prioridad rápida."""
    return velocidad_jugador > velocidad_enemigo


def calculateTurnOrder(
    velocidad_jugador,
    velocidad_enemigo,
    ataque_enemigo_rapido=False,
    ultimo_actor=None,
    acumuladores=None,
):
    """Construye una cola sin remanentes entre ciclos de iniciativa.

    Un ataque rápido conserva prioridad salvo en empates ya iniciados: cuando
    las velocidades coinciden, ``ultimo_actor`` fuerza alternancia estricta y
    evita que una cola termine y la siguiente empiece con el mismo actor.
    """
    acumuladores = acumuladores or {"jugador": 0, "enemigo": 0}
    acciones_jugador, resto_jugador = getActionPoints(
        velocidad_jugador,
        velocidad_enemigo,
        acumuladores.get("jugador", 0),
    )
    acciones_enemigo, resto_enemigo = getActionPoints(
        velocidad_enemigo,
        velocidad_jugador,
        acumuladores.get("enemigo", 0),
    )
    puntos = {
        "jugador": acciones_jugador,
        "enemigo": acciones_enemigo,
    }
    nuevos_acumuladores = {
        "jugador": resto_jugador,
        "enemigo": resto_enemigo,
    }

    # Con velocidades idénticas no existen puntos extra. La primera posición
    # se asigna al opuesto del último actor para impedir E,E entre dos colas.
    if velocidad_jugador == velocidad_enemigo:
        if ultimo_actor == "jugador":
            return ["enemigo", "jugador"], nuevos_acumuladores
        if ultimo_actor == "enemigo":
            return ["jugador", "enemigo"], nuevos_acumuladores
        primero = "enemigo" if ataque_enemigo_rapido else "jugador"
        segundo = "jugador" if primero == "enemigo" else "enemigo"
        return [primero, segundo], nuevos_acumuladores

    if ataque_enemigo_rapido and not jugador_rompe_prioridad_rapida(
        velocidad_jugador,
        velocidad_enemigo,
    ):
        prioridad = ["enemigo", "jugador"]
    else:
        prioridad = sorted(
            puntos,
            key=lambda entidad: (
                velocidad_jugador if entidad == "jugador" else velocidad_enemigo
            ),
            reverse=True,
        )
    cola = [
        entidad
        for entidad in prioridad
        for _ in range(puntos[entidad])
    ]
    return cola, nuevos_acumuladores


class MotorJuego:
    HABITACIONES_TOTALES = 50
    ENERGIA_MAXIMA = 3

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.sistema_niveles = SistemaNiveles(
            exp_por_nivel=30,
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
        self.energia = self.ENERGIA_MAXIMA
        self.enemigo_dano = 0
        self.enemigo_habilidad = None
        self.aturdimiento_jugador = 0
        self.intencion = None
        self.turno_global = 0
        self.ultimo_actor = None
        self.acumuladores_velocidad = {"jugador": 0, "enemigo": 0}
        self.is_defending = False
        self.cooldowns_habilidades = {}
        self.efectos_habilidades = {}
        self.registro = []

    def nueva_partida(self):
        self.reiniciar()
        self.fase = "inicio"
        self.registro = ["Elige un nombre y un arma para comenzar."]

    def iniciar(self, nombre, arma):
        self._exigir_fase("inicio")
        nombre = str(nombre).strip()
        if not nombre:
            raise ErrorJuego("Debes escribir un nombre.")
        if arma not in objetos["armas"] or not objetos["armas"][arma].get(
            "inicial",
            False,
        ):
            raise ErrorJuego("El arma inicial no es válida.")
        stats = {"fuerza": 1, "destreza": 1, "constitucion": 1}
        self.jugador = Personaje(nombre, arma, stats)
        self.fase = "transicion"
        self.registro = [f"{nombre} entra al calabozo con {arma}."]
        self.siguiente_habitacion()

    def _registrar(self, mensaje):
        self.registro.append(mensaje)
        self.registro = self.registro[-80:]

    def _exigir_fase(self, fase):
        if self.fase != fase:
            raise ErrorJuego("Esa acción no está disponible ahora.")

    def _elegir_habitacion(self):
        if self.numero_habitacion == self.HABITACIONES_TOTALES:
            return "combate"
        disponibles = ["combate"]
        precio_minimo = min(
            datos["precio"]
            for categoria in objetos.values()
            for datos in categoria.values()
        )
        if self.jugador.oro >= precio_minimo and self.habitacion_anterior != "tienda":
            disponibles.append("tienda")
        return self.rng.choice(disponibles)

    def siguiente_habitacion(self):
        if self.fase not in {"transicion", "tienda"}:
            raise ErrorJuego("Todavía no puedes avanzar.")
        if self.numero_habitacion >= self.HABITACIONES_TOTALES:
            self._terminar("victoria")
            return
        self.numero_habitacion += 1
        tipo = self._elegir_habitacion()
        self.habitacion_anterior = tipo
        self._registrar(f"Habitación {self.numero_habitacion}: {tipo}.")
        if tipo == "combate":
            self._iniciar_combate()
        else:
            self.enemigo_actual = None
            self.fase = "tienda"
            self._registrar("Un mercader te ofrece sus productos.")

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
        self.energia = self.ENERGIA_MAXIMA
        self.turno_global = 0
        self.ultimo_actor = None
        self.acumuladores_velocidad = {"jugador": 0, "enemigo": 0}
        self.is_defending = False
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
            dano_arma = obtener_dano_arma(enemigo.arma, self.rng)
            self.enemigo_dano = enemigo.calcular_dano_base() + dano_arma
            return

        dano_arma = obtener_dano_arma(enemigo.arma, self.rng)
        self.enemigo_dano = enemigo.calcular_dano_base() + dano_arma
        minimo, maximo = objetos["armas"][enemigo.arma]["ataque"]
        minimo += enemigo.calcular_dano_base()
        maximo += enemigo.calcular_dano_base()
        tercio = (maximo - minimo) / 3
        if self.enemigo_dano <= minimo + tercio:
            self.intencion = "rápido"
        elif self.enemigo_dano >= maximo - tercio:
            self.intencion = "poderoso"
        else:
            self.intencion = "normal"

    def _dano_total_jugador(self):
        return (
            self.jugador.calcular_dano_base()
            + obtener_dano_arma(self.jugador.arma, self.rng)
        )

    def _defensa_total_jugador(self):
        return (
            self.jugador.calcular_defensa_base()
            + self.jugador.inventario.defensa_equipo()
            + round(self.jugador.bonus_pasivo_habilidad("defensa"))
        )

    def _resolver_ataques_multiples(self, habilidad, nivel_habilidad):
        """Resuelve golpes basados en daño escalado del personaje y arma."""
        impactos = 0
        esquivados = 0
        dano_total = 0
        golpes_realizados = 0
        for _ in range(habilidad.numero_golpes):
            if self.enemigo_actual.hp <= 0:
                break
            golpes_realizados += 1
            dano_personaje = self._dano_total_jugador()
            dano_golpe = max(
                1,
                round(dano_personaje * habilidad.multiplicador_base),
            )
            if self.rng.random() < self.enemigo_actual.evasion:
                esquivados += 1
                continue
            reduccion = self.enemigo_actual.reduccion_dano_activa()
            recibido = max(1, round(dano_golpe * (1 - reduccion)))
            self.enemigo_actual.hp -= recibido
            impactos += 1
            dano_total += recibido
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

    def _accion_jugador(self, accion, habilidad_id=None):
        # isDefending vence al comenzar una nueva acción propia, nunca cuando
        # el jugador recibe un golpe. Si vuelve a defender, se reactiva para
        # todos los ataques que ocurran antes de su siguiente acción.
        self.is_defending = False
        dano = 0
        defensa_extra = 0
        ataques_evitar = 0
        dano_ya_mitigado = False

        if accion == "atacar":
            dano = self._dano_total_jugador()
            mensaje = "Atacas"
        elif accion == "defender":
            self.energia = min(self.ENERGIA_MAXIMA, self.energia + 1)
            self.is_defending = True
            self._registrar(
                f"Defiendes con {self._defensa_total_jugador() * 2} de defensa "
                "y recuperas energía."
            )
            return defensa_extra, ataques_evitar
        else:
            habilidad = habilidad_factory.crear(habilidad_id)
            nivel_habilidad = self.jugador.nivel_habilidad(habilidad_id)
            if nivel_habilidad < 1:
                raise ErrorJuego("La habilidad todavía está bloqueada.")
            if not self.jugador.puede_usar_habilidad(habilidad_id):
                requisito_adicional = (
                    " y la mano secundaria libre"
                    if habilidad.requiere_mano_secundaria_libre
                    else ""
                )
                raise ErrorJuego(
                    f"{habilidad.nombre} requiere un arma de tipo "
                    f"{habilidad.tipo_arma_requerida}{requisito_adicional}."
                )
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
                dano = calcular_dano_habilidad(
                    dano_base=self.jugador.DANO_BASE,
                    dano_arma=obtener_dano_arma(self.jugador.arma, self.rng),
                    habilidad=habilidad,
                    nivel_habilidad=nivel_habilidad,
                    valor_atributo=valor_atributo,
                    defensa_objetivo=self.enemigo_actual.defensa_total,
                    constitucion_objetivo=self.enemigo_actual.constitucion,
                )
                dano_ya_mitigado = True
            efecto = habilidad.calcular_efecto(nivel_habilidad, valor_atributo)
            if habilidad.tipo_efecto == "defensa":
                defensa_extra = round(efecto)
            elif habilidad.tipo_efecto == "reduccion_dano":
                self.jugador.activar_mitigar_dano(habilidad.duracion_turnos)
                self.efectos_habilidades[habilidad_id] = habilidad.duracion_turnos
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

        recibido_enemigo = (
            dano
            if dano_ya_mitigado
            else max(1, dano - self.enemigo_actual.defensa_total)
        )
        reduccion_enemiga = self.enemigo_actual.reduccion_dano_activa()
        if reduccion_enemiga:
            recibido_enemigo = max(
                1,
                round(recibido_enemigo * (1 - reduccion_enemiga)),
            )
        if self.rng.random() < self.enemigo_actual.evasion:
            self._registrar("¡El enemigo esquivó el ataque!")
            return defensa_extra, ataques_evitar
        self.enemigo_actual.hp -= recibido_enemigo
        self._registrar(f"{mensaje} causas {recibido_enemigo} de daño.")
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
        habilidad_id = self.enemigo_habilidad
        habilidad = habilidad_factory.crear(habilidad_id) if habilidad_id else None
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
            )
            self._registrar(
                f"El {self.enemigo_actual.nombre} usa {habilidad.nombre}: "
                f"reduce un {round(efecto * 100)}% del daño durante "
                f"{habilidad.duracion_turnos} turnos."
            )
            self._preparar_turno_enemigo()
            return

        if self.rng.random() < self.jugador.evasion:
            self._registrar("¡Esquivaste el ataque!")
            self._actualizar_habilidades_enemigo(habilidad_id)
            self._preparar_turno_enemigo()
            return
        defensa = self._defensa_total_jugador()
        if self.is_defending:
            # No se consume aquí: cada ataque previo al siguiente turno del
            # jugador se enfrenta a su defensa total duplicada.
            defensa *= 2
        defensa += defensa_extra
        if habilidad:
            dano_tras_defensa = calcular_dano_habilidad(
                dano_base=3,
                dano_arma=obtener_dano_arma(self.enemigo_actual.arma, self.rng),
                habilidad=habilidad,
                nivel_habilidad=self.enemigo_actual.nivel_habilidad(habilidad_id),
                valor_atributo=getattr(
                    self.enemigo_actual, habilidad.atributo_escalado
                ),
                defensa_objetivo=defensa,
                constitucion_objetivo=self.jugador.constitucion_total,
            )
        else:
            dano_tras_defensa = max(1, self.enemigo_dano - defensa)
        reduccion = 0
        for habilidad_id, turnos in self.efectos_habilidades.items():
            if turnos <= 0:
                continue
            habilidad = habilidad_factory.crear(habilidad_id)
            if habilidad.tipo_efecto != "reduccion_dano":
                continue
            nivel = self.jugador.nivel_habilidad(habilidad_id)
            atributo = self.jugador.estadistica_total(habilidad.atributo_escalado)
            reduccion += habilidad.calcular_efecto(nivel, atributo)
        reduccion = min(0.90, reduccion)
        recibido = max(1, round(dano_tras_defensa * (1 - reduccion)))
        self.jugador.hp -= recibido
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
                self._registrar("El golpe te deja aturdido: perderás una acción.")
        else:
            self._registrar(
                f"El {self.enemigo_actual.nombre} ataca y causa {recibido} de daño."
            )
        self._actualizar_habilidades_enemigo(habilidad_id)
        if self.jugador.hp > 0:
            self._preparar_turno_enemigo()

    def actuar(self, accion, habilidad_id=None):
        self._exigir_fase("combate")
        if accion == "tecnica":
            arma = self.jugador.inventario.arma_equipada
            habilidad = habilidad_factory.para_tipo_arma(arma.tipo_arma)
            if not habilidad:
                raise ErrorJuego("El arma principal no tiene una técnica asociada.")
            habilidad_id = habilidad.id
            accion = "habilidad"
        if accion not in {"atacar", "defender", "habilidad"}:
            raise ErrorJuego("Acción de combate no válida.")

        nuevos_cooldowns = {
            identificador: max(0, turnos - 1)
            for identificador, turnos in self.cooldowns_habilidades.items()
        }
        nuevos_efectos = {
            identificador: max(0, turnos - 1)
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
                requisito_adicional = (
                    " y la mano secundaria libre"
                    if habilidad.requiere_mano_secundaria_libre
                    else ""
                )
                raise ErrorJuego(
                    f"{habilidad.nombre} requiere un arma de tipo "
                    f"{habilidad.tipo_arma_requerida}{requisito_adicional}."
                )
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
            ultimo_actor=self.ultimo_actor,
            acumuladores=self.acumuladores_velocidad,
        )
        defensa_extra = 0
        ataques_evitar = 0
        self._registrar(
            f"Turno {self.turno_global}: "
            f"{cola.count('jugador')} acción(es) del jugador y "
            f"{cola.count('enemigo')} del enemigo."
        )

        for entidad in cola:
            self.ultimo_actor = entidad
            if entidad == "jugador":
                if self.aturdimiento_jugador:
                    self.aturdimiento_jugador -= 1
                    self.is_defending = False
                    self._registrar("Estás aturdido y pierdes esta acción.")
                    continue
                if (
                    accion == "habilidad"
                    and habilidad.bloquear_mientras_activa
                    and self.jugador.mitigar_dano_activo
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
            else:
                self._accion_enemigo(defensa_extra)
                if self.jugador.hp <= 0:
                    self._preparar_respawn()
                    return

    def _preparar_respawn(self):
        """Detiene el combate para que la derrota sea visible antes de renacer."""
        self.jugador.hp = 0
        self.fase = "muerte"
        self.resultado = "derrota"
        self._registrar("Has caído en el calabozo.")

    def _respawn(self):
        """Reinicia la expedición sin reemplazar ni degradar al personaje."""
        self._exigir_fase("muerte")
        self.jugador.hp = self.jugador.salud_maxima
        self.resultado = None
        self.numero_habitacion = 1
        self.habitacion_anterior = "combate"
        self.enemigo_actual = None
        self.energia = self.ENERGIA_MAXIMA
        self.enemigo_dano = 0
        self.enemigo_habilidad = None
        self.aturdimiento_jugador = 0
        self.intencion = None
        self.turno_global = 0
        self.ultimo_actor = None
        self.acumuladores_velocidad = {"jugador": 0, "enemigo": 0}
        self.is_defending = False
        self._registrar(
            "Despiertas recuperado al inicio del calabozo; conservas tu progreso."
        )
        self._iniciar_combate()

    def respawn(self):
        self._respawn()

    def _resolver_victoria(self):
        enemigo = self.enemigo_actual
        oro = self.rng.randint(*enemigo.oro)
        self.jugador.oro += oro
        self.jugador.ganar_exp(enemigo.exp)
        enemigo.hp = 0
        self._registrar(
            f"Derrotas al {enemigo.nombre}: +{oro} oro, +{enemigo.exp} EXP."
        )
        if self.sistema_niveles.puede_subir(self.jugador):
            self.jugador.subir_nivel()
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
            self.jugador.subir_nivel()
            self._registrar(
                f"Alcanzas el nivel {self.jugador.nivel}: recibes otro punto "
                "de estadística y de habilidad."
            )
        else:
            self.fase = "transicion"

    def mejorar_habilidad(self, habilidad_id):
        if self.fase in {"menu", "inicio", "combate", "fin"}:
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

    def equipar_item(self, item_id):
        if self.fase in {"menu", "inicio", "combate", "fin"}:
            raise ErrorJuego("No puedes cambiar equipo en este momento.")
        try:
            salud_anterior = self.jugador.salud_maxima
            item = self.jugador.inventario.equipar(item_id, self.jugador)
            self.jugador.recalcular_por_equipo(salud_anterior)
        except ValueError as error:
            raise ErrorJuego(str(error)) from error
        self._registrar(f"Equipas {item.nombre}.")

    def desequipar_item(self, slot):
        if self.fase in {"menu", "inicio", "combate", "fin"}:
            raise ErrorJuego("No puedes cambiar equipo en este momento.")
        try:
            salud_anterior = self.jugador.salud_maxima
            item = self.jugador.inventario.desequipar(slot)
            self.jugador.recalcular_por_equipo(salud_anterior)
        except ValueError as error:
            raise ErrorJuego(str(error)) from error
        self._registrar(f"Desequipas {item.nombre}.")

    def usar_item(self, item_id):
        if self.fase in {"menu", "inicio", "combate", "fin"}:
            raise ErrorJuego("No puedes usar ese ítem en este momento.")
        try:
            item, recuperado = self.jugador.inventario.usar(item_id, self.jugador)
        except ValueError as error:
            raise ErrorJuego(str(error)) from error
        self._registrar(f"Usas {item.nombre} y recuperas {recuperado} de vida.")

    def comprar(self, categoria, nombre):
        self._exigir_fase("tienda")
        if categoria not in objetos or nombre not in objetos[categoria]:
            raise ErrorJuego("Ese producto no existe.")
        datos = objetos[categoria][nombre]
        if self.jugador.oro < datos["precio"]:
            raise ErrorJuego("No tienes oro suficiente.")
        item = item_factory.crear(datos["id"])
        self.jugador.oro -= datos["precio"]
        self.jugador.inventario.recolectar(item.id)
        if isinstance(item, (Arma, Secundario, Armadura)) and item.cumple_requisitos(
            self.jugador
        ):
            salud_anterior = self.jugador.salud_maxima
            self.jugador.inventario.equipar(item.id, self.jugador)
            self.jugador.recalcular_por_equipo(salud_anterior)
            self._registrar(f"Compras y equipas {nombre}.")
        elif isinstance(item, (Arma, Secundario, Armadura)):
            self._registrar(f"Compras {nombre}; aún no puedes equiparlo.")
        elif isinstance(item, Consumible):
            self._registrar(f"Compras {nombre} y la guardas en el inventario.")

    def _terminar(self, resultado):
        self.fase = "fin"
        self.resultado = resultado
        mensaje = "Encontraste la salida." if resultado == "victoria" else "Has muerto."
        self._registrar(mensaje)

    def exportar_guardado(self):
        """Genera una instantánea JSON del loop, incluso durante un combate."""
        jugador = None
        if self.jugador:
            jugador = {
                "nombre": self.jugador.nombre,
                "arma": self.jugador.arma,
                "inventario": self.jugador.inventario.serializar(),
                "habilidades": dict(self.jugador.habilidades),
                "puntos_estadistica": self.jugador.puntos_estadistica,
                "puntos_habilidad": self.jugador.puntos_habilidad,
                "fuerza": self.jugador.fuerza,
                "destreza": self.jugador.destreza,
                "constitucion": self.jugador.constitucion,
                "salud_maxima": self.jugador.salud_maxima,
                "hp": max(0, self.jugador.hp),
                "nivel": self.jugador.nivel,
                "oro": self.jugador.oro,
                "exp": self.jugador.exp,
                "mitigar_dano_activo": self.jugador.mitigar_dano_activo,
                "mitigar_dano_turnos": self.jugador.mitigar_dano_turnos,
            }
        enemigo = None
        if self.enemigo_actual:
            enemigo = vars(self.enemigo_actual).copy()
            enemigo["hp"] = max(0, enemigo["hp"])
        return {
            "fase": self.fase,
            "resultado": self.resultado,
            "numero_habitacion": self.numero_habitacion,
            "habitacion_anterior": self.habitacion_anterior,
            "energia": self.energia,
            "enemigo_dano": self.enemigo_dano,
            "enemigo_habilidad": self.enemigo_habilidad,
            "aturdimiento_jugador": self.aturdimiento_jugador,
            "intencion": self.intencion,
            "turno_global": self.turno_global,
            "ultimo_actor": self.ultimo_actor,
            "acumuladores_velocidad": self.acumuladores_velocidad,
            "is_defending": self.is_defending,
            "cooldowns_habilidades": dict(self.cooldowns_habilidades),
            "efectos_habilidades": dict(self.efectos_habilidades),
            "registro": self.registro,
            "jugador": jugador,
            "enemigo": enemigo,
        }

    def importar_guardado(self, datos):
        """Valida y restaura una instantánea; no modifica el motor si falla."""
        try:
            fase = datos["fase"]
            habitacion = int(datos["numero_habitacion"])
            jugador_datos = datos["jugador"]
            enemigo_datos = datos.get("enemigo")
            if fase not in {
                "combate",
                "nivel",
                "transicion",
                "tienda",
                "muerte",
                "fin",
            }:
                raise ValueError
            if not 1 <= habitacion <= self.HABITACIONES_TOTALES:
                raise ValueError
            if not isinstance(jugador_datos, dict):
                raise ValueError
            arma_original = jugador_datos["arma"]
            equipo_legacy = arma_original in {
                "Espada y escudo",
                "Espada y escudo de hierro",
            }
            arma = "Espada de hierro" if equipo_legacy else arma_original
            if arma not in objetos["armas"]:
                raise ValueError

            jugador = Personaje(
                str(jugador_datos["nombre"])[:30],
                arma,
                {
                    "fuerza": int(jugador_datos["fuerza"]),
                    "destreza": int(jugador_datos["destreza"]),
                    "constitucion": int(jugador_datos["constitucion"]),
                },
            )
            inventario_datos = jugador_datos.get("inventario")
            if isinstance(inventario_datos, list):
                # Compatibilidad con la lista de nombres de versiones anteriores.
                inventario = Inventario()
                for nombre_item in dict.fromkeys(inventario_datos or [arma]):
                    inventario.recolectar(nombre_item)
                if inventario.cantidad(arma) < 1:
                    inventario.recolectar(arma)
                jugador.inventario = inventario
                jugador.inventario.equipar(arma, jugador)
                if equipo_legacy:
                    jugador.inventario.recolectar("Escudo de hierro")
                    jugador.inventario.equipar("Escudo de hierro", jugador)
            elif inventario_datos is not None:
                inventario_datos = {
                    **inventario_datos,
                    "items": dict(inventario_datos.get("items", {})),
                }
                if equipo_legacy or any(
                    item_id in inventario_datos["items"]
                    for item_id in (
                        "espada_escudo_hierro",
                        "Espada y escudo",
                        "Espada y escudo de hierro",
                    )
                ):
                    cantidad_escudos = max(
                        1,
                        inventario_datos["items"].get("escudo_hierro", 0),
                    )
                    inventario_datos["items"]["escudo_hierro"] = cantidad_escudos
                    equipamiento = dict(inventario_datos.get("equipamiento", {}))
                    equipamiento.setdefault("mano_secundaria", "escudo_hierro")
                    inventario_datos["equipamiento"] = equipamiento
                jugador.inventario = Inventario.deserializar(inventario_datos)
                if not jugador.inventario.arma_equipada:
                    jugador.inventario.equipar(arma, jugador)
            jugador.salud_maxima = jugador.calcular_salud_maxima()

            habilidades_guardadas = jugador_datos.get("habilidades")
            if habilidades_guardadas is not None:
                ids_validos = {habilidad.id for habilidad in habilidad_factory.todas()}
                if (
                    not isinstance(habilidades_guardadas, dict)
                    or not set(habilidades_guardadas).issubset(ids_validos)
                ):
                    raise ValueError
                for habilidad_id, nivel_habilidad in habilidades_guardadas.items():
                    habilidad = habilidad_factory.crear(habilidad_id)
                    nivel_habilidad = int(nivel_habilidad)
                    if not 0 <= nivel_habilidad <= habilidad.nivel_maximo:
                        raise ValueError
                    jugador.habilidades[habilidad_id] = nivel_habilidad
            jugador.puntos_estadistica = int(
                jugador_datos.get("puntos_estadistica", 0)
            )
            jugador.puntos_habilidad = int(jugador_datos.get("puntos_habilidad", 0))
            for atributo in ("hp", "nivel", "oro", "exp"):
                setattr(jugador, atributo, int(jugador_datos[atributo]))
            if "puntos_estadistica" not in jugador_datos and fase == "nivel":
                # En el formato anterior el nivel se otorgaba al elegir el stat.
                jugador.subir_nivel()
            if min(jugador.fuerza, jugador.destreza, jugador.constitucion) < 1:
                raise ValueError
            if (
                not 1 <= jugador.nivel <= Personaje.NIVEL_MAXIMO
                or jugador.oro < 0
                or jugador.exp < 0
            ):
                raise ValueError
            if jugador.puntos_estadistica < 0 or jugador.puntos_habilidad < 0:
                raise ValueError
            if not 0 <= jugador.hp <= jugador.salud_maxima:
                raise ValueError

            if enemigo_datos and enemigo_datos.get("arma") in {
                "Espada y escudo",
                "Espada y escudo de hierro",
            }:
                enemigo_datos = {
                    **enemigo_datos,
                    "arma": "Espada de hierro",
                    "secundario": "Escudo de hierro",
                }
            if enemigo_datos:
                # La velocidad es derivada de DEX; se ignora el valor redundante
                # presente en guardados de versiones anteriores.
                enemigo_datos = {**enemigo_datos}
                enemigo_datos.pop("velocidad", None)
            enemigo = Enemigo(**enemigo_datos) if enemigo_datos else None
            if fase == "combate" and enemigo is None:
                raise ValueError
            if enemigo:
                ids_habilidades_enemigo = {
                    habilidad.id for habilidad in habilidad_factory.todas()
                }
                if enemigo.arma not in objetos["armas"]:
                    raise ValueError
                if enemigo.secundario:
                    secundario = item_factory.crear(enemigo.secundario)
                    if not isinstance(secundario, Secundario):
                        raise ValueError
                if min(enemigo.fuerza, enemigo.destreza, enemigo.constitucion) < 1:
                    raise ValueError
                if not 0 <= enemigo.hp <= enemigo.salud_maxima:
                    raise ValueError
                if not set(enemigo.habilidades).issubset(ids_habilidades_enemigo):
                    raise ValueError
                for habilidad_id, nivel_habilidad in enemigo.habilidades.items():
                    habilidad = habilidad_factory.crear(habilidad_id)
                    if not 1 <= nivel_habilidad <= habilidad.nivel_maximo:
                        raise ValueError
                if any(
                    not isinstance(turnos, int) or turnos < 0
                    for turnos in (
                        *enemigo.cooldowns_habilidad.values(),
                        *enemigo.efectos_habilidad.values(),
                    )
                ):
                    raise ValueError
            energia = int(datos["energia"])
            turno_global = int(datos["turno_global"])
            ultimo_actor = datos.get("ultimo_actor")
            acumuladores_velocidad = datos.get(
                "acumuladores_velocidad",
                {"jugador": 0, "enemigo": 0},
            )
            is_defending = datos.get("is_defending", False)
            cooldowns_habilidades = datos.get(
                "cooldowns_habilidades",
                {habilidad.id: 0 for habilidad in habilidad_factory.todas()},
            )
            efectos_habilidades = datos.get(
                "efectos_habilidades",
                {habilidad.id: 0 for habilidad in habilidad_factory.todas()},
            )
            ids_habilidades = {
                habilidad.id for habilidad in habilidad_factory.todas()
            }
            cooldowns_habilidades = {
                habilidad_id: cooldowns_habilidades.get(habilidad_id, 0)
                for habilidad_id in ids_habilidades
            }
            efectos_habilidades = {
                habilidad_id: efectos_habilidades.get(habilidad_id, 0)
                for habilidad_id in ids_habilidades
            }
            if not 0 <= energia <= self.ENERGIA_MAXIMA or turno_global < 0:
                raise ValueError
            if ultimo_actor not in {None, "jugador", "enemigo"}:
                raise ValueError
            if (
                not isinstance(acumuladores_velocidad, dict)
                or set(acumuladores_velocidad) != {"jugador", "enemigo"}
                or any(
                    not isinstance(valor, int) or not 0 <= valor < 6
                    for valor in acumuladores_velocidad.values()
                )
            ):
                raise ValueError
            if not isinstance(is_defending, bool):
                raise ValueError
            if (
                not isinstance(cooldowns_habilidades, dict)
                or set(cooldowns_habilidades)
                != ids_habilidades
                or any(
                    not isinstance(turnos, int) or turnos < 0
                    for turnos in cooldowns_habilidades.values()
                )
            ):
                raise ValueError
            if (
                not isinstance(efectos_habilidades, dict)
                or set(efectos_habilidades) != ids_habilidades
                or any(
                    not isinstance(turnos, int) or turnos < 0
                    for turnos in efectos_habilidades.values()
                )
            ):
                raise ValueError
            mitigar_dano_turnos = int(
                jugador_datos.get(
                    "mitigar_dano_turnos",
                    efectos_habilidades.get("mitigar_dano", 0),
                )
            )
            mitigar_dano_activo = jugador_datos.get(
                "mitigar_dano_activo",
                mitigar_dano_turnos > 0,
            )
            if (
                not isinstance(mitigar_dano_activo, bool)
                or mitigar_dano_activo != (mitigar_dano_turnos > 0)
                or not 0
                <= mitigar_dano_turnos
                <= habilidad_factory.crear("mitigar_dano").duracion_turnos
                or mitigar_dano_turnos
                != efectos_habilidades.get("mitigar_dano", 0)
            ):
                raise ValueError
            enemigo_habilidad = datos.get("enemigo_habilidad")
            aturdimiento_jugador = int(datos.get("aturdimiento_jugador", 0))
            if aturdimiento_jugador < 0:
                raise ValueError
            if enemigo_habilidad is not None and (
                enemigo is None or enemigo_habilidad not in enemigo.habilidades
            ):
                raise ValueError
        except (KeyError, TypeError, ValueError) as error:
            raise ErrorJuego("La partida guardada contiene datos inválidos.") from error

        self.jugador = jugador
        self.fase = fase
        self.resultado = datos.get("resultado")
        self.numero_habitacion = habitacion
        self.habitacion_anterior = datos.get("habitacion_anterior")
        self.enemigo_actual = enemigo
        self.energia = energia
        self.enemigo_dano = int(datos.get("enemigo_dano", 0))
        self.enemigo_habilidad = enemigo_habilidad
        self.aturdimiento_jugador = aturdimiento_jugador
        self.intencion = datos.get("intencion")
        self.turno_global = turno_global
        self.ultimo_actor = ultimo_actor
        self.acumuladores_velocidad = acumuladores_velocidad
        self.is_defending = is_defending
        self.cooldowns_habilidades = cooldowns_habilidades
        self.efectos_habilidades = efectos_habilidades
        self.jugador.establecer_mitigar_dano(mitigar_dano_turnos)
        if self.fase == "combate" and self.intencion not in {
            "rápido",
            "normal",
            "poderoso",
        } and not str(self.intencion).startswith("habilidad:"):
            self._preparar_turno_enemigo()
        self.registro = [str(linea) for linea in datos.get("registro", [])][-80:]
        self._registrar("Partida cargada correctamente.")

    def estado(self):
        armas_iniciales = [
            {"nombre": nombre, **datos}
            for nombre, datos in objetos["armas"].items()
            if datos.get("inicial", False)
        ]
        datos = {
            "fase": self.fase,
            "resultado": self.resultado,
            "habitacion": self.numero_habitacion,
            "habitaciones_totales": self.HABITACIONES_TOTALES,
            "registro": self.registro,
            "armas_iniciales": armas_iniciales,
            "jugador": None,
            "enemigo": None,
            "tienda": objetos if self.fase == "tienda" else None,
        }
        if self.jugador:
            j = self.jugador
            dano_base = j.calcular_dano_base()
            ataque_arma = objetos["armas"][j.arma]["ataque"]
            datos["jugador"] = {
                "nombre": j.nombre,
                "arma": j.arma,
                "inventario": j.inventario.estado(j),
                "equipamiento": j.inventario.estado_equipamiento(),
                "hp": max(0, j.hp),
                "salud_maxima": j.salud_maxima,
                "energia": self.energia,
                "energia_maxima": self.ENERGIA_MAXIMA,
                "nivel": j.nivel,
                "nivel_maximo": self.sistema_niveles.nivel_maximo,
                "exp": j.exp,
                "exp_siguiente_nivel": (
                    self.sistema_niveles.experiencia_siguiente_nivel(j)
                ),
                "oro": j.oro,
                "fuerza": j.fuerza_total,
                "destreza": j.destreza_total,
                "constitucion": j.constitucion_total,
                "stats_base": {
                    "fuerza": j.fuerza,
                    "destreza": j.destreza,
                    "constitucion": j.constitucion,
                },
                "bonus_equipo": j.inventario.bonificaciones_atributos(),
                "puntos_estadistica": j.puntos_estadistica,
                "puntos_habilidad": j.puntos_habilidad,
                "dano_base": dano_base,
                "ataque_minimo": dano_base + ataque_arma[0],
                "ataque_maximo": dano_base + ataque_arma[1],
                "defensa": self._defensa_total_jugador(),
                "velocidad": j.velocidad,
                "evasion": j.evasion,
                "defendiendo": self.is_defending,
                "mitigar_dano_activo": j.mitigar_dano_activo,
                "mitigar_dano_turnos": j.mitigar_dano_turnos,
                "ataque_arma": ataque_arma,
                "habilidades": [
                    {
                        "id": habilidad.id,
                        "nombre": habilidad.nombre,
                        "descripcion": habilidad.descripcion,
                        "nivel": j.nivel_habilidad(habilidad.id),
                        "nivel_maximo": habilidad.nivel_maximo,
                        "atributo": habilidad.atributo_escalado,
                        "arma_requerida": habilidad.tipo_arma_requerida,
                        "desbloqueada": j.nivel_habilidad(habilidad.id) > 0,
                        "cumple_requisito": j.cumple_requisitos_habilidad(
                            habilidad.id
                        ),
                        "cumple_tipo_equipo": j.inventario.cumple_tipo_equipo(
                            habilidad.tipo_arma_requerida
                        ),
                        "mano_secundaria_libre": (
                            j.inventario.secundario_equipado is None
                        ),
                        "costo_energia": habilidad.costo_energia,
                        "cooldown": self.cooldowns_habilidades.get(habilidad.id, 0),
                        "bonus_dano": habilidad.bonus_dano_por_nivel
                        * j.nivel_habilidad(habilidad.id),
                        "efecto": habilidad.calcular_efecto(
                            max(1, j.nivel_habilidad(habilidad.id)),
                            j.estadistica_total(habilidad.atributo_escalado),
                        ),
                        "tipo_efecto": habilidad.tipo_efecto,
                        "numero_golpes": habilidad.numero_golpes,
                        "dano_total_por_golpe": habilidad.multiplicador_base,
                        "requiere_mano_secundaria_libre": (
                            habilidad.requiere_mano_secundaria_libre
                        ),
                        "causa_dano": habilidad.causa_dano,
                        "duracion": habilidad.duracion_turnos,
                        "turnos_activos": self.efectos_habilidades.get(
                            habilidad.id,
                            0,
                        ),
                        "activa": (
                            j.mitigar_dano_activo
                            if habilidad.id == "mitigar_dano"
                            else self.efectos_habilidades.get(habilidad.id, 0) > 0
                        ),
                    }
                    for habilidad in habilidad_factory.todas()
                ],
            }
        if self.enemigo_actual and self.fase in {
            "combate",
            "nivel",
            "transicion",
            "muerte",
        }:
            enemigo = self.enemigo_actual
            datos["enemigo"] = {
                "nombre": enemigo.nombre,
                "raza": enemigo.raza,
                "arquetipo": enemigo.arquetipo,
                "hp": max(0, enemigo.hp),
                "hp_maxima": enemigo.salud_maxima,
                "fuerza": enemigo.fuerza,
                "destreza": enemigo.destreza,
                "constitucion": enemigo.constitucion,
                "velocidad": enemigo.velocidad,
                "evasion": enemigo.evasion,
                "arma": enemigo.arma,
                "secundario": enemigo.secundario,
                "habilidades": [
                    {
                        "id": habilidad_id,
                        "nombre": habilidad_factory.crear(habilidad_id).nombre,
                        "nivel": nivel,
                        "cooldown": enemigo.cooldowns_habilidad.get(
                            habilidad_id, 0
                        ),
                        "turnos_activos": enemigo.efectos_habilidad.get(
                            habilidad_id, 0
                        ),
                        "activa": enemigo.habilidad_activa(habilidad_id),
                    }
                    for habilidad_id, nivel in enemigo.habilidades.items()
                ],
                "intencion": self.intencion if self.fase == "combate" else None,
            }
        return datos
