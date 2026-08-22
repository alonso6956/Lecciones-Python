from combat_formulas import calcular_evasion, calcular_velocidad
from items import calcular_factor_arma


class Personaje:
    """Estadísticas y fórmulas propias del personaje, sin datos de equipo."""

    SALUD_BASE = 50
    DANO_BASE = 4
    DEFENSA_BASE = 2
    VELOCIDAD_BASE = 10
    ESCALADO_CONSTITUCION = 0.20

    def __init__(self, nombre, arma, stats):
        self.nombre = nombre
        self.arma = arma
        self.inventario = [arma]
        self.fuerza = stats["fuerza"]
        self.destreza = stats["destreza"]
        self.constitucion = stats.get("constitucion", stats.get("Constitución", 1))
        self.salud_maxima = self.calcular_salud_maxima()
        self.hp = self.salud_maxima
        self.nivel = 1
        self.oro = 0
        self.exp = 0

    @staticmethod
    def _bonus_porcentual(estadistica, porcentaje):
        """El primer punto es la base; cada punto posterior aporta el porcentaje."""
        return max(0, estadistica - 1) * porcentaje

    def calcular_salud_maxima(self):
        bonus = self._bonus_porcentual(
            self.constitucion,
            self.ESCALADO_CONSTITUCION,
        )
        return round(self.SALUD_BASE * (1 + bonus))

    def calcular_dano_base(self, arma=None):
        factor = calcular_factor_arma(
            arma or self.arma,
            self.fuerza,
            self.destreza,
        )
        return round(self.DANO_BASE * factor)

    def calcular_defensa_base(self, arma=None):
        """CON aporta 1 de defensa por cada 2 puntos, sin escalado ofensivo."""
        return self.DEFENSA_BASE + self.constitucion // 2

    @property
    def velocidad(self):
        return calcular_velocidad(self.VELOCIDAD_BASE, self.destreza)

    @property
    def evasion(self):
        return calcular_evasion(self.destreza)

    def curar(self, cantidad):
        salud_anterior = self.hp
        self.hp = min(self.salud_maxima, self.hp + cantidad)
        return self.hp - salud_anterior

    def subir_nivel(self, estadistica):
        if estadistica not in {"fuerza", "destreza", "constitucion"}:
            raise ValueError("La estadística elegida no es válida")

        salud_anterior = self.salud_maxima
        self.nivel += 1
        setattr(self, estadistica, getattr(self, estadistica) + 1)
        self.salud_maxima = self.calcular_salud_maxima()
        if estadistica == "constitucion":
            self.hp += self.salud_maxima - salud_anterior

    def ganar_exp(self, cantidad):
        self.exp += cantidad
