"""Estadísticas de combate compartidas por Dungeon y el modo táctico."""

from combat_formulas import calcular_mitigacion_armadura
from item import Arma
from item_factory import item_factory
from items import obtener_dano_arma
from derived_stats import atributo, arma_de, umbral_salud


def defensa_total(modelo):
    if hasattr(modelo, "inventario"):
        return (modelo.calcular_defensa_base() + modelo.inventario.armadura_equipo()
                + round(modelo.bonus_pasivo_habilidad("defensa")))
    return modelo.defensa_total


def armas_ataque(modelo):
    """Cada mano genera un golpe; sus propiedades nunca se suman globalmente."""
    principal = arma_de(modelo)
    golpes = [(principal, 1.0)]
    inventario = getattr(modelo, "inventario", None)
    secundaria = inventario.secundario_equipado if inventario else None
    if isinstance(secundaria, Arma) and principal.compatible_dual and secundaria.compatible_dual:
        golpes.append((secundaria, .5))
    return golpes


def dano_con_arma(modelo, arma, valor):
    return (modelo.calcular_dano_base() + valor) * arma.factor_escalado(
        atributo(modelo, "fuerza"), atributo(modelo, "destreza"))


def tirar_dano(modelo, rng, arma=None):
    arma = arma or arma_de(modelo)
    return dano_con_arma(modelo, arma, rng.randint(*arma.ataque))


def estadisticas_combate(modelo):
    jugador = hasattr(modelo, "inventario")
    arma = item_factory.crear(modelo.arma)
    base = modelo.calcular_dano_base()
    defensa = defensa_total(modelo)
    secundario = (modelo.inventario.secundario_equipado if jugador else
                  item_factory.crear(modelo.secundario) if modelo.secundario else None)
    golpes = armas_ataque(modelo)
    datos = {
        "fuerza": modelo.fuerza_total if jugador else modelo.fuerza,
        "destreza": modelo.destreza_total if jugador else modelo.destreza,
        "constitucion": modelo.constitucion_total if jugador else modelo.constitucion,
        "salud_maxima": modelo.salud_maxima,
        "dano_base": base, "ataque_arma": list(arma.ataque),
        "ataque_minimo": round(sum(dano_con_arma(modelo, a, a.ataque[0]) * f for a, f in golpes), 1),
        "ataque_maximo": round(sum(dano_con_arma(modelo, a, a.ataque[1]) * f for a, f in golpes), 1),
        "golpes_basicos": len(golpes),
        "iniciativa": modelo.iniciativa, "movimiento": modelo.movimiento,
        "precision": modelo.precision, "impacto": modelo.impacto,
        "estabilidad": modelo.estabilidad, "resistencia_fisica": modelo.resistencia_fisica,
        "regeneracion": modelo.regeneracion, "penetracion": modelo.penetracion,
        "umbral_salud": umbral_salud(modelo.hp, modelo.salud_maxima),
        "vida_efectiva": round(modelo.salud_maxima / (1 - calcular_mitigacion_armadura(defensa)), 1),
        "armadura": defensa, "mitigacion_armadura": calcular_mitigacion_armadura(defensa),
        "velocidad": modelo.velocidad, "evasion": modelo.evasion,
        "arma": arma.nombre, "arma_id": arma.id, "secundario": secundario.nombre if secundario else None,
        "critico_arma": arma.critico, "penetracion_arma": arma.penetracion,
        "alcance_arma": arma.alcance, "velocidad_arma": arma.velocidad,
        "durabilidad_arma": arma.durabilidad,
        "probabilidad_bloqueo": getattr(secundario, "probabilidad_bloqueo", 0),
        "porcentaje_dano_bloqueado": getattr(secundario, "porcentaje_dano_bloqueado", 0),
    }
    if jugador:
        datos.update(energia_maxima=modelo.energia_maxima,
                     carga_categoria=modelo.penalizaciones_peso["categoria"],
                     carga_relativa=modelo.penalizaciones_peso["relativa"],
                     modificador_movimiento_carga=modelo.penalizaciones_peso["movimiento"],
                     peso_equipado=modelo.peso_equipado, capacidad_peso=modelo.capacidad_peso,
                     penalizacion_evasion_peso=modelo.penalizaciones_peso["evasion"],
                     penalizacion_velocidad_peso=modelo.penalizaciones_peso["velocidad"],
                     armadura_equipo=modelo.inventario.armadura_equipo(),
                     mitigacion_armadura_equipo=calcular_mitigacion_armadura(modelo.inventario.armadura_equipo()))
    return datos
