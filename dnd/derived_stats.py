"""Derivados definidos en Game Design; independientes del resolutor de combate."""

import math


def atributo(modelo, nombre):
    total = getattr(modelo, "estadistica_total", None)
    return total(nombre) if total else getattr(modelo, nombre)


def bonus(modelo, nombre):
    inventario = getattr(modelo, "inventario", None)
    equipo = inventario.bonificaciones_atributos() if inventario else {}
    if not inventario and getattr(modelo, "secundario", None):
        from item_factory import item_factory
        equipo = getattr(item_factory.crear(modelo.secundario), "bonificaciones", {})
        from defense_system import durabilidad_escudo
        if durabilidad_escudo(modelo) <= 0:
            equipo = {}
    return equipo.get(nombre, 0) + getattr(modelo, "modificadores", {}).get(nombre, 0)


def arma_de(modelo):
    from item_factory import item_factory
    inventario = getattr(modelo, "inventario", None)
    return inventario.arma_equipada if inventario else item_factory.crear(modelo.arma)


def salud_por_nivel(nivel, plano=0, porcentual=0):
    return max(1, round((50 + 5 * (nivel - 1) + plano) * (1 + porcentual)))


def umbral_salud(actual, maxima):
    if actual <= 0:
        return "derrotado"
    porcentaje = actual / maxima
    return "alta" if porcentaje > .75 else "media" if porcentaje > .40 else "baja" if porcentaje > .20 else "critica"


def probabilidad_estado(base, potencia, resistencia, inmune=False):
    if inmune or base <= 0 or potencia <= 0:
        return 0.0
    return max(.05, min(.95, base * 2 * potencia / (potencia + max(0, resistencia))))


class EstadisticasDerivadas:
    @property
    def iniciativa(self):
        return max(0, 10 + 2 * (atributo(self, "destreza") - 1) + bonus(self, "iniciativa"))

    @property
    def movimiento(self):
        base = min(6, 3 + (atributo(self, "destreza") - 1) // 10)
        penalizaciones = getattr(self, "penalizaciones_peso", {})
        return max(0, int(base + bonus(self, "movimiento") + penalizaciones.get("movimiento", 0)))

    @property
    def precision(self):
        return max(0, 50 + 2 * (atributo(self, "destreza") - 1) + arma_de(self).precision + bonus(self, "precision"))

    @property
    def impacto(self):
        return max(0, 10 + 2 * (atributo(self, "fuerza") - 1) + arma_de(self).impacto + bonus(self, "impacto"))

    @property
    def estabilidad(self):
        return max(0, 10 + 2 * (atributo(self, "constitucion") - 1) + bonus(self, "estabilidad"))

    @property
    def resistencia_fisica(self):
        return max(0, 2 * (atributo(self, "constitucion") - 1) + bonus(self, "resistencia_fisica"))

    def penetracion_con(self, arma):
        return max(0, 5 * math.sqrt(max(0, atributo(self, "fuerza") - 1)) + arma.penetracion + bonus(self, "penetracion"))

    @property
    def penetracion(self):
        return self.penetracion_con(arma_de(self))

    @property
    def regeneracion(self):
        base = 1 + max(0, atributo(self, "constitucion") - 1) // 5 + bonus(self, "regeneracion")
        return max(0, base * (1 + bonus(self, "regeneracion_pct")))

    def regenerar(self):
        if self.hp <= 0:
            return 0
        anterior = self.hp
        self.hp = min(self.salud_maxima, self.hp + self.regeneracion)
        return self.hp - anterior
