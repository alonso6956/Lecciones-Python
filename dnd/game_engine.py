import random

from character import Personaje
from enemies import enemigos
from items import calcular_defensa, objetos
from level_system import SistemaNiveles


class ErrorJuego(ValueError):
    pass


class MotorJuego:
    HABITACIONES_TOTALES = 50
    ENERGIA_MAXIMA = 3
    ATURDIMIENTO_MAXIMO = 0.80

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.sistema_niveles = SistemaNiveles(exp_por_nivel=30, nivel_maximo=10)
        self.reiniciar()

    def reiniciar(self):
        self.jugador = None
        self.fase = "inicio"
        self.resultado = None
        self.numero_habitacion = 0
        self.habitacion_anterior = None
        self.enemigo_anterior = None
        self.enemigo_actual = None
        self.enemigo_hp = 0
        self.energia = self.ENERGIA_MAXIMA
        self.enemigo_dano = 0
        self.intencion = None
        self.registro = ["Elige un nombre y un arma para comenzar."]

    def iniciar(self, nombre, arma):
        nombre = str(nombre).strip()
        if not nombre:
            raise ErrorJuego("Debes escribir un nombre.")
        if arma not in objetos["armas"] or objetos["armas"][arma]["tier"] != 1:
            raise ErrorJuego("El arma inicial no es válida.")
        stats = {
            "fuerza": 1,
            "destreza": 1,
            "Constitución": 1,
            "Inteligencia": 1,
            "Carisma": 1,
        }
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
            self.enemigo_anterior = None
            self.enemigo_actual = None
            self.fase = "tienda"
            self._registrar("Un mercader te ofrece sus productos.")

    def _elegir_enemigo(self):
        fuertes = {"Orco", "Troll"}
        candidatos = list(enemigos)
        if self.enemigo_anterior in fuertes:
            candidatos = [nombre for nombre in candidatos if nombre not in fuertes]
        pesos = [enemigos[nombre]["peso"] for nombre in candidatos]
        return self.rng.choices(candidatos, weights=pesos, k=1)[0]

    def _iniciar_combate(self):
        self.enemigo_actual = self._elegir_enemigo()
        self.enemigo_anterior = self.enemigo_actual
        self.enemigo_hp = enemigos[self.enemigo_actual]["hp"]
        self.energia = self.ENERGIA_MAXIMA
        self.fase = "combate"
        self._registrar(f"Aparece un {self.enemigo_actual}.")
        self._preparar_turno()

    def _preparar_turno(self):
        ataque = enemigos[self.enemigo_actual]["ataque"]
        self.enemigo_dano = self.rng.randint(*ataque)
        minimo, maximo = ataque
        tercio = (maximo - minimo) / 3
        if self.enemigo_dano <= minimo + tercio:
            self.intencion = "rápido"
        elif self.enemigo_dano >= maximo - tercio:
            self.intencion = "poderoso"
        else:
            self.intencion = "normal"

    def actuar(self, accion):
        self._exigir_fase("combate")
        if accion not in {"atacar", "defender", "tecnica"}:
            raise ErrorJuego("Acción de combate no válida.")
        arma = objetos["armas"][self.jugador.arma]
        minimo, maximo = arma["ataque"]
        dano = 0
        defensa_base = calcular_defensa(
            self.jugador.arma,
            self.jugador.fuerza,
            self.jugador.destreza,
            self.jugador.constitucion,
        )
        defensa_extra = 0
        evita_ataque = False

        if accion == "atacar":
            dano = self.rng.randint(minimo, maximo) + self.jugador.fuerza
            self._registrar(f"Atacas y causas {dano} de daño.")
        elif accion == "defender":
            self.energia = min(self.ENERGIA_MAXIMA, self.energia + 1)
            defensa_extra = defensa_base
            self._registrar(
                f"Defiendes con {defensa_base * 2} de defensa y recuperas energía."
            )
        else:
            if self.energia < 2:
                raise ErrorJuego("No tienes energía suficiente.")
            self.energia -= 2
            tipo = arma["tipo_tecnica"]
            if tipo == "constitucion":
                dano = self.rng.randint(minimo, maximo) + self.jugador.constitucion
                defensa_extra = self.jugador.constitucion + 2
            elif tipo == "destreza":
                dano = self.rng.randint(minimo, maximo) + self.jugador.destreza * 2
                probabilidad = min(0.75, 0.20 + self.jugador.destreza * 0.05)
                evita_ataque = self.rng.random() < probabilidad
            else:
                dano = self.rng.randint(minimo, maximo) + self.jugador.fuerza * 2
                probabilidad = min(
                    self.ATURDIMIENTO_MAXIMO,
                    arma["tier"] * 0.10 + self.jugador.fuerza * 0.05,
                )
                evita_ataque = self.rng.random() < probabilidad
            self._registrar(f"Usas {arma['tecnica']} y causas {dano} de daño.")

        self.enemigo_hp -= dano
        if self.enemigo_hp <= 0:
            self._resolver_victoria()
            return
        if evita_ataque:
            self._registrar(f"El {self.enemigo_actual} pierde su ataque.")
        else:
            defensa = defensa_base + defensa_extra
            recibido = max(1, self.enemigo_dano - defensa)
            self.jugador.hp -= recibido
            self._registrar(
                f"El {self.enemigo_actual} ataca y causa {recibido} de daño."
            )
        if self.jugador.hp <= 0:
            self._terminar("derrota")
        else:
            self._preparar_turno()

    def _resolver_victoria(self):
        stats = enemigos[self.enemigo_actual]
        oro = self.rng.randint(*stats["oro"])
        self.jugador.oro += oro
        self.jugador.ganar_exp(stats["exp"])
        self.enemigo_hp = 0
        self._registrar(
            f"Derrotas al {self.enemigo_actual}: +{oro} oro, +{stats['exp']} EXP."
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
        self.jugador.oro -= datos["precio"]
        if categoria == "pociones":
            recuperada = self.jugador.curar(self.rng.randint(*datos["salud"]))
            self._registrar(f"Compras {nombre} y recuperas {recuperada} de vida.")
        elif categoria == "armas":
            self.jugador.arma = nombre
            self._registrar(f"Compras y equipas {nombre}.")

    def _terminar(self, resultado):
        self.fase = "fin"
        self.resultado = resultado
        mensaje = "Encontraste la salida." if resultado == "victoria" else "Has muerto."
        self._registrar(mensaje)

    def estado(self):
        armas_iniciales = [
            {"nombre": nombre, **datos}
            for nombre, datos in objetos["armas"].items()
            if datos["tier"] == 1
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
            defensa = calcular_defensa(
                j.arma,
                j.fuerza,
                j.destreza,
                j.constitucion,
            )
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
                "defensa": defensa,
                "tecnica": objetos["armas"][j.arma]["tecnica"],
            }
        if self.enemigo_actual and self.fase in {"combate", "nivel", "transicion"}:
            stats = enemigos[self.enemigo_actual]
            datos["enemigo"] = {
                "nombre": self.enemigo_actual,
                "hp": max(0, self.enemigo_hp),
                "hp_maxima": stats["hp"],
                "intencion": self.intencion if self.fase == "combate" else None,
            }
        return datos
