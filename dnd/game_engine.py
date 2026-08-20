import random

from character import Personaje
from combat_formulas import calcular_dano_habilidad
from enemies import Enemigo, calcular_velocidad_enemigo, elegir_enemigo
from items import (
    objetos,
    obtener_dano_arma,
    obtener_defensa_arma,
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
    HABITACIONES_TOTALES = 49
    ENERGIA_MAXIMA = 3
    ATURDIMIENTO_MAXIMO = 0.80

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.sistema_niveles = SistemaNiveles(exp_por_nivel=30, nivel_maximo=10)
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
        self.intencion = None
        self.turno_global = 0
        self.ultimo_actor = None
        self.acumuladores_velocidad = {"jugador": 0, "enemigo": 0}
        self.is_defending = False
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
        self.fase = "combate"
        self._registrar(
            f"Aparece un {self.enemigo_actual.nombre} con "
            f"{self.enemigo_actual.arma}."
        )

    def _preparar_turno_enemigo(self):
        enemigo = self.enemigo_actual
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
            + obtener_defensa_arma(self.jugador.arma)
        )

    def _accion_jugador(self, accion):
        # isDefending vence al comenzar una nueva acción propia, nunca cuando
        # el jugador recibe un golpe. Si vuelve a defender, se reactiva para
        # todos los ataques que ocurran antes de su siguiente acción.
        self.is_defending = False
        arma = objetos["armas"][self.jugador.arma]
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
            if self.energia < 2:
                self._registrar(
                    "Sin energía para repetir la técnica: realizas un ataque normal."
                )
                return self._accion_jugador("atacar")
            self.energia -= 2
            dano = calcular_dano_habilidad(
                dano_base=self.jugador.DANO_BASE,
                dano_arma=obtener_dano_arma(self.jugador.arma, self.rng),
                nombre_arma=self.jugador.arma,
                fuerza=self.jugador.fuerza,
                destreza=self.jugador.destreza,
                defensa_objetivo=self.enemigo_actual.defensa_total,
                constitucion_objetivo=self.enemigo_actual.constitucion,
            )
            dano_ya_mitigado = True
            tipo = arma["tipo_tecnica"]
            if tipo == "constitucion":
                defensa_extra = self.jugador.constitucion + 2
            elif tipo == "destreza":
                probabilidad = min(0.75, 0.20 + self.jugador.destreza * 0.05)
                ataques_evitar = int(self.rng.random() < probabilidad)
            else:
                probabilidad = min(
                    self.ATURDIMIENTO_MAXIMO,
                    arma["tier"] * 0.10 + self.jugador.fuerza * 0.05,
                )
                ataques_evitar = int(self.rng.random() < probabilidad)
            mensaje = f"Usas {arma['tecnica']} y"

        recibido_enemigo = (
            dano
            if dano_ya_mitigado
            else max(1, dano - self.enemigo_actual.defensa_total)
        )
        if self.rng.random() < self.enemigo_actual.evasion:
            self._registrar("¡El enemigo esquivó el ataque!")
            return defensa_extra, ataques_evitar
        self.enemigo_actual.hp -= recibido_enemigo
        self._registrar(f"{mensaje} causas {recibido_enemigo} de daño.")
        return defensa_extra, ataques_evitar

    def _accion_enemigo(self, defensa_extra):
        if self.rng.random() < self.jugador.evasion:
            self._registrar("¡Esquivaste el ataque!")
            self._preparar_turno_enemigo()
            return
        defensa = self._defensa_total_jugador()
        if self.is_defending:
            # No se consume aquí: cada ataque previo al siguiente turno del
            # jugador se enfrenta a su defensa total duplicada.
            defensa *= 2
        defensa += defensa_extra
        recibido = max(1, self.enemigo_dano - defensa)
        self.jugador.hp -= recibido
        self._registrar(
            f"El {self.enemigo_actual.nombre} ataca y causa {recibido} de daño."
        )
        if self.jugador.hp > 0:
            self._preparar_turno_enemigo()

    def actuar(self, accion):
        self._exigir_fase("combate")
        if accion not in {"atacar", "defender", "tecnica"}:
            raise ErrorJuego("Acción de combate no válida.")

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
                bonus, evita = self._accion_jugador(accion)
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
                    self._terminar("derrota")
                    return

    def _resolver_victoria(self):
        enemigo = self.enemigo_actual
        oro = self.rng.randint(*enemigo.oro)
        self.jugador.oro += oro
        self.jugador.ganar_exp(enemigo.exp)
        enemigo.hp = 0
        self._registrar(
            f"Derrotas al {enemigo.nombre}: +{oro} oro, +{enemigo.exp} EXP."
        )
        self.fase = (
            "nivel" if self.sistema_niveles.puede_subir(self.jugador) else "transicion"
        )

    def subir_nivel(self, estadistica):
        self._exigir_fase("nivel")
        self.jugador.subir_nivel(estadistica)
        self._registrar(f"Nivel {self.jugador.nivel}: +1 {estadistica}.")
        if not self.sistema_niveles.puede_subir(self.jugador):
            self.fase = "transicion"

    def comprar(self, categoria, nombre):
        self._exigir_fase("tienda")
        if categoria not in objetos or nombre not in objetos[categoria]:
            raise ErrorJuego("Ese producto no existe.")
        datos = objetos[categoria][nombre]
        if self.jugador.oro < datos["precio"]:
            raise ErrorJuego("No tienes oro suficiente.")
        if categoria == "pociones":
            curacion = datos["salud"]
            if (
                not isinstance(curacion, int)
                or isinstance(curacion, bool)
                or curacion <= 0
            ):
                raise ErrorJuego("La poción debe tener una curación fija positiva.")
            self.jugador.oro -= datos["precio"]
            recuperada = self.jugador.curar(curacion)
            self._registrar(f"Compras {nombre} y recuperas {recuperada} de vida.")
        else:
            self.jugador.oro -= datos["precio"]
            self.jugador.arma = nombre
            self._registrar(f"Compras y equipas {nombre}.")

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
                "fuerza": self.jugador.fuerza,
                "destreza": self.jugador.destreza,
                "constitucion": self.jugador.constitucion,
                "salud_maxima": self.jugador.salud_maxima,
                "hp": max(0, self.jugador.hp),
                "nivel": self.jugador.nivel,
                "oro": self.jugador.oro,
                "exp": self.jugador.exp,
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
            "intencion": self.intencion,
            "turno_global": self.turno_global,
            "ultimo_actor": self.ultimo_actor,
            "acumuladores_velocidad": self.acumuladores_velocidad,
            "is_defending": self.is_defending,
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
            if fase not in {"combate", "nivel", "transicion", "tienda", "fin"}:
                raise ValueError
            if not 1 <= habitacion <= self.HABITACIONES_TOTALES:
                raise ValueError
            if not isinstance(jugador_datos, dict):
                raise ValueError
            arma = jugador_datos["arma"]
            if arma == "Espada y escudo":
                arma = "Espada y escudo de hierro"
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
            for atributo in ("hp", "nivel", "oro", "exp"):
                setattr(jugador, atributo, int(jugador_datos[atributo]))
            if min(jugador.fuerza, jugador.destreza, jugador.constitucion) < 1:
                raise ValueError
            if jugador.nivel < 1 or jugador.oro < 0 or jugador.exp < 0:
                raise ValueError
            if not 0 <= jugador.hp <= jugador.salud_maxima:
                raise ValueError

            if enemigo_datos and enemigo_datos.get("arma") == "Espada y escudo":
                enemigo_datos = {**enemigo_datos, "arma": "Espada y escudo de hierro"}
            enemigo = Enemigo(**enemigo_datos) if enemigo_datos else None
            if fase == "combate" and enemigo is None:
                raise ValueError
            if enemigo:
                if enemigo.arma not in objetos["armas"]:
                    raise ValueError
                if min(enemigo.fuerza, enemigo.destreza, enemigo.constitucion) < 1:
                    raise ValueError
                if not 0 <= enemigo.hp <= enemigo.salud_maxima:
                    raise ValueError
                # Recalcula la velocidad para reparar guardados creados cuando
                # la DEX racial incrementaba incorrectamente los turnos.
                enemigo.velocidad = calcular_velocidad_enemigo(
                    enemigo.raza,
                    enemigo.arquetipo,
                )

            energia = int(datos["energia"])
            turno_global = int(datos["turno_global"])
            ultimo_actor = datos.get("ultimo_actor")
            acumuladores_velocidad = datos.get(
                "acumuladores_velocidad",
                {"jugador": 0, "enemigo": 0},
            )
            is_defending = datos.get("is_defending", False)
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
        self.intencion = datos.get("intencion")
        self.turno_global = turno_global
        self.ultimo_actor = ultimo_actor
        self.acumuladores_velocidad = acumuladores_velocidad
        self.is_defending = is_defending
        if self.fase == "combate" and self.intencion not in {
            "rápido",
            "normal",
            "poderoso",
        }:
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
                "hp": max(0, j.hp),
                "salud_maxima": j.salud_maxima,
                "energia": self.energia,
                "energia_maxima": self.ENERGIA_MAXIMA,
                "nivel": j.nivel,
                "exp": j.exp,
                "oro": j.oro,
                "fuerza": j.fuerza,
                "destreza": j.destreza,
                "constitucion": j.constitucion,
                "dano_base": dano_base,
                "ataque_minimo": dano_base + ataque_arma[0],
                "ataque_maximo": dano_base + ataque_arma[1],
                "defensa": self._defensa_total_jugador(),
                "velocidad": j.velocidad,
                "evasion": j.evasion,
                "defendiendo": self.is_defending,
                "tecnica": objetos["armas"][j.arma]["tecnica"],
                "descripcion_tecnica": objetos["armas"][j.arma][
                    "descripcion_tecnica"
                ],
                "ataque_arma": ataque_arma,
            }
        if self.enemigo_actual and self.fase in {"combate", "nivel", "transicion"}:
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
                "intencion": self.intencion if self.fase == "combate" else None,
            }
        return datos
