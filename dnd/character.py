from combat_formulas import (
    calcular_evasion,
    calcular_penalizaciones_peso,
    calcular_velocidad,
)
from habilidades import habilidad_factory
from inventario import Inventario
from items import calcular_factor_arma
from uuid import uuid4
from progression import CLASES, comprobar_hitos, habilidades_de_clase
from pasiva_factory import pasiva_factory


class Personaje:
    """Estadísticas y fórmulas propias del personaje, sin datos de equipo."""

    SALUD_BASE = 50
    DANO_BASE = 2
    DEFENSA_BASE = 10
    VELOCIDAD_BASE = 10
    ESCALADO_CONSTITUCION = 0.20
    ESCALADO_VIDA_NIVEL = 0.10  # 10% de SALUD_BASE: +5 de vida por nivel ganado.
    ENERGIA_BASE = 3
    NIVEL_MAXIMO = 30
    CAPACIDAD_PESO_BASE = 8
    CAPACIDAD_PESO_POR_CONSTITUCION = 4

    def __init__(self, nombre, arma, stats):
        self.id = uuid4().hex
        self.clase = None
        self.chispa = None
        self.nombre = nombre
        self.fuerza = stats["fuerza"]
        self.destreza = stats["destreza"]
        self.constitucion = stats.get("constitucion", stats.get("Constitución", 1))
        self.inventario = Inventario()
        arma_inicial = self.inventario.recolectar(arma)
        self.inventario.equipar(arma_inicial.id, self)
        self.habilidades = {}
        self.puntos_estadistica = 0
        self.puntos_habilidad = 0
        self.mitigar_dano_activo = False
        self.mitigar_dano_turnos = 0
        self.nivel = 1
        self.salud_maxima = self.calcular_salud_maxima()
        self.hp = self.salud_maxima
        self.oro = 0
        self.exp = 0
        self.crafting_exp = 0

    @property
    def crafting_tier(self):
        from crafting import crafting_data
        return sum(self.crafting_exp >= umbral for umbral in crafting_data()["experiencia_por_tier"])

    @property
    def arma(self):
        arma = self.inventario.arma_equipada
        return (arma.id if arma.id.startswith("craft_") else arma.nombre) if arma else None

    @property
    def pasiva_clase(self):
        pasivas = pasiva_factory.para_clase(self.clase)
        return pasivas[0] if pasivas else None

    @arma.setter
    def arma(self, identificador):
        self.inventario.equipar(identificador, self)

    @staticmethod
    def _bonus_porcentual(estadistica, porcentaje):
        """El primer punto es la base; cada punto posterior aporta el porcentaje."""
        return max(0, estadistica - 1) * porcentaje

    def calcular_salud_maxima(self):
        bonus = self._bonus_porcentual(
            self.estadistica_total("constitucion"),
            self.ESCALADO_CONSTITUCION,
        )
        vida_por_nivel = self.SALUD_BASE * self.ESCALADO_VIDA_NIVEL * (self.nivel - 1)
        return round(self.SALUD_BASE * (1 + bonus) + vida_por_nivel)

    @property
    def energia_maxima(self):
        return self.ENERGIA_BASE + self.nivel // 10

    def estadistica_total(self, estadistica):
        bonus = self.inventario.bonificaciones_atributos().get(estadistica, 0)
        return getattr(self, estadistica) + bonus

    @property
    def fuerza_total(self):
        return self.estadistica_total("fuerza")

    @property
    def destreza_total(self):
        return self.estadistica_total("destreza")

    @property
    def constitucion_total(self):
        return self.estadistica_total("constitucion")

    def calcular_dano_base(self, arma=None):
        factor = calcular_factor_arma(
            arma or self.arma,
            self.fuerza_total,
            self.destreza_total,
        )
        return round(self.DANO_BASE * factor)

    def calcular_defensa_base(self, arma=None):
        """CON aporta 1 de defensa por cada 2 puntos, sin escalado ofensivo."""
        return self.DEFENSA_BASE + self.constitucion_total // 2

    @property
    def velocidad(self):
        velocidad = calcular_velocidad(self.VELOCIDAD_BASE, self.destreza_total)
        velocidad = round(velocidad * self.inventario.arma_equipada.velocidad)
        return max(0, velocidad - self.penalizaciones_peso["velocidad"])

    @property
    def evasion(self):
        evasion = min(
            1.0,
            calcular_evasion(self.destreza_total)
            + self.bonus_pasivo_habilidad("evasion"),
        )
        return max(0.0, evasion - self.penalizaciones_peso["evasion"])

    @property
    def peso_equipado(self):
        return self.inventario.peso_equipo()

    @property
    def capacidad_peso(self):
        return (
            self.CAPACIDAD_PESO_BASE
            + max(0, self.constitucion_total - 1)
            * self.CAPACIDAD_PESO_POR_CONSTITUCION
        )

    @property
    def penalizaciones_peso(self):
        return calcular_penalizaciones_peso(
            self.peso_equipado,
            self.capacidad_peso,
        )

    def bonus_pasivo_habilidad(self, tipo_efecto):
        """Aplica los incrementos de las habilidades de clase aprendidas."""
        total = 0
        for habilidad in habilidad_factory.todas():
            nivel = self.nivel_habilidad(habilidad.id)
            if (
                nivel > 0
                and habilidad.tipo_efecto == tipo_efecto
                and self.puede_usar_habilidad(habilidad.id)
            ):
                total += nivel * habilidad.efecto_por_nivel
        return total

    def curar(self, cantidad):
        salud_anterior = self.hp
        self.hp = min(self.salud_maxima, self.hp + cantidad)
        return self.hp - salud_anterior

    def asignar_atributo(self, estadistica):
        if estadistica not in {"fuerza", "destreza", "constitucion"}:
            raise ValueError("La estadística elegida no es válida")
        if self.puntos_estadistica < 1:
            raise ValueError("No tienes puntos de estadística.")

        salud_anterior = self.salud_maxima
        setattr(self, estadistica, getattr(self, estadistica) + 1)
        self.puntos_estadistica -= 1
        self.salud_maxima = self.calcular_salud_maxima()
        if estadistica == "constitucion":
            self.hp += self.salud_maxima - salud_anterior

    def subir_nivel(self, estadistica=None):
        if self.nivel >= self.NIVEL_MAXIMO:
            raise ValueError("El personaje ya alcanzó el nivel máximo.")
        self.nivel += 1
        salud_anterior = self.salud_maxima
        self.salud_maxima = self.calcular_salud_maxima()
        self.hp += self.salud_maxima - salud_anterior
        self.puntos_estadistica += 1
        self.puntos_habilidad += 1
        if estadistica:
            self.asignar_atributo(estadistica)
        return comprobar_hitos(self)

    def elegir_clase(self, clase):
        if not isinstance(clase, str) or self.nivel < 10 or self.clase is not None or clase not in CLASES:
            raise ValueError("No puedes elegir esa clase ahora.")
        self.clase = clase
        # TODO: Integrar estadísticas y habilidades; por ahora solo es una etiqueta.

    def mejorar_habilidad(self, habilidad_id):
        if habilidad_id not in habilidades_de_clase(self.clase):
            raise ValueError("La habilidad no pertenece al árbol de tu clase.")
        habilidad = habilidad_factory.crear(habilidad_id)
        nivel = self.habilidades.get(habilidad_id, 0)
        if self.puntos_habilidad < 1:
            raise ValueError("No tienes puntos de habilidad.")
        if nivel >= habilidad.nivel_maximo:
            raise ValueError("La habilidad ya alcanzó su nivel máximo.")
        self.habilidades[habilidad_id] = nivel + 1
        self.puntos_habilidad -= 1
        return habilidad

    def nivel_habilidad(self, habilidad_id):
        return self.habilidades.get(habilidad_id, 0)

    def activar_mitigar_dano(self, turnos=3):
        if self.mitigar_dano_activo:
            raise ValueError("Mitigar daño ya está activa.")
        self.establecer_mitigar_dano(turnos)

    def establecer_mitigar_dano(self, turnos_restantes):
        turnos_restantes = int(turnos_restantes)
        if turnos_restantes < 0:
            raise ValueError("La duración de Mitigar daño no puede ser negativa.")
        self.mitigar_dano_turnos = turnos_restantes
        self.mitigar_dano_activo = turnos_restantes > 0

    def puede_usar_habilidad(self, habilidad_id):
        return (
            self.nivel_habilidad(habilidad_id) > 0
            and self.cumple_requisitos_habilidad(habilidad_id)
        )

    def cumple_requisitos_habilidad(self, habilidad_id):
        habilidad_factory.crear(habilidad_id)
        return habilidad_id in habilidades_de_clase(self.clase)

    def recalcular_por_equipo(self, salud_maxima_anterior=None):
        anterior = (
            self.salud_maxima
            if salud_maxima_anterior is None
            else salud_maxima_anterior
        )
        self.salud_maxima = self.calcular_salud_maxima()
        if self.salud_maxima > anterior:
            self.hp += self.salud_maxima - anterior
        self.hp = min(self.hp, self.salud_maxima)

    def ganar_exp(self, cantidad):
        self.exp += cantidad
