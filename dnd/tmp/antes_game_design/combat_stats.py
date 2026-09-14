"""Estadísticas de combate compartidas por Dungeon y el modo táctico."""

from combat_formulas import calcular_mitigacion_armadura
from item import Arma
from item_factory import item_factory
from items import obtener_dano_arma


def defensa_total(modelo):
    if hasattr(modelo, "inventario"):
        return (modelo.calcular_defensa_base() + modelo.inventario.armadura_equipo()
                + round(modelo.bonus_pasivo_habilidad("defensa")))
    return modelo.defensa_total


def tirar_dano(modelo, rng):
    dano = modelo.calcular_dano_base() + obtener_dano_arma(modelo.arma, rng)
    inventario = getattr(modelo, "inventario", None)
    secundaria = inventario.secundario_equipado if inventario else None
    if isinstance(secundaria, Arma) and secundaria.tipo_arma == "daga":
        dano += obtener_dano_arma(secundaria.id, rng) * 0.5
    return dano


def estadisticas_combate(modelo):
    jugador = hasattr(modelo, "inventario")
    arma = item_factory.crear(modelo.arma)
    base = modelo.calcular_dano_base()
    defensa = defensa_total(modelo)
    secundario = (modelo.inventario.secundario_equipado if jugador else
                  item_factory.crear(modelo.secundario) if modelo.secundario else None)
    dano_secundario = (secundario.ataque if isinstance(secundario, Arma) and secundario.tipo_arma == "daga"
                       else (0, 0))
    datos = {
        "fuerza": modelo.fuerza_total if jugador else modelo.fuerza,
        "destreza": modelo.destreza_total if jugador else modelo.destreza,
        "constitucion": modelo.constitucion_total if jugador else modelo.constitucion,
        "salud_maxima": modelo.salud_maxima,
        "dano_base": base, "ataque_arma": list(arma.ataque),
        "ataque_minimo": round(base + arma.ataque[0] + dano_secundario[0] * 0.5, 1),
        "ataque_maximo": round(base + arma.ataque[1] + dano_secundario[1] * 0.5, 1),
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
                     peso_equipado=modelo.peso_equipado, capacidad_peso=modelo.capacidad_peso,
                     penalizacion_evasion_peso=modelo.penalizaciones_peso["evasion"],
                     penalizacion_velocidad_peso=modelo.penalizaciones_peso["velocidad"],
                     armadura_equipo=modelo.inventario.armadura_equipo(),
                     mitigacion_armadura_equipo=calcular_mitigacion_armadura(modelo.inventario.armadura_equipo()))
    return datos
