"""Tablas de Crafteo.md. Los objetos anteriores conservan su versión y valores."""

import math

CALIDADES = {"defectuosa": .10, "comun": .30, "buena": .55, "excelente": .80, "maestra": 1.0}
NOMBRES_CALIDAD = {"defectuosa": "Defectuosa", "comun": "Común", "buena": "Buena", "excelente": "Excelente", "maestra": "Maestra", "legacy": "Anterior"}
ARMADURA_TIER = {1: (5, 17), 2: (18, 40), 3: (41, 80), 4: (81, 120)}
DANO_TIER = {1: (5, 10), 2: (11, 20), 3: (21, 35), 4: (36, 55)}
COEFICIENTES_SLOT = {"pecho": .40, "piernas": .25, "casco": .20, "brazos": .15}
MULTIPLICADOR_ARMA = {"daga": .70, "espada": 1., "lanza": .95, "maza": 1.10}
REQUISITOS = {
    "daga": [{"destreza": n} for n in (2, 5, 9, 14)],
    "espada": [{"fuerza": n} for n in (2, 5, 9, 14)],
    "maza": [{"fuerza": n} for n in (3, 6, 10, 15)],
    "lanza": [dict(fuerza=f, destreza=d) for f, d in ((2, 2), (5, 4), (9, 7), (14, 10))],
}


def valor_calidad(rango, calidad):
    minimo, maximo = rango
    return minimo + (maximo - minimo) * CALIDADES[calidad]


def repartir_armadura(presupuesto):
    """Mayores restos: el redondeo de cuatro piezas nunca crea poder adicional."""
    total = max(0, round(presupuesto))
    piezas = {s: math.floor(total * c) for s, c in COEFICIENTES_SLOT.items()}
    orden = sorted(piezas, key=lambda s: (-(total * COEFICIENTES_SLOT[s] - piezas[s]), s))
    for slot in orden[:total - sum(piezas.values())]:
        piezas[slot] += 1
    return piezas


def componentes_validos(componente, tier, catalogo):
    seleccion = [] if componente is None else [componente] if isinstance(componente, str) else componente
    if not isinstance(seleccion, list) or any(not isinstance(c, str) or c not in catalogo for c in seleccion):
        raise ValueError("Componentes de fabricación inválidos.")
    if len(set(seleccion)) != len(seleccion) or len(seleccion) > tier:
        raise ValueError(f"El Tier {tier} permite hasta {tier} afijos distintos.")
    return seleccion


def validar_equipo_nuevo(item):
    if item.version_diseno < 2:
        return
    from item import Arma, Armadura
    if item.version_diseno != 2 or item.tier not in DANO_TIER or item.calidad not in CALIDADES:
        raise ValueError("Versión, Tier o Calidad de equipo inválidos.")
    if isinstance(item, Arma):
        if item.tipo_arma not in MULTIPLICADOR_ARMA:
            raise ValueError("Familia de arma sin balance definido.")
        limite = DANO_TIER[item.tier][1] * MULTIPLICADOR_ARMA[item.tipo_arma]
        if item.ataque[1] > math.floor(limite):
            raise ValueError("El daño supera el límite del Tier y familia.")
        if len(item.afijos) > item.tier or len({a['id'] for a in item.afijos}) != len(item.afijos):
            raise ValueError("Cantidad de afijos inválida.")
        if item.requisitos != REQUISITOS[item.tipo_arma][item.tier - 1]:
            raise ValueError("Requisitos incompatibles con el Tier y familia.")
    elif isinstance(item, Armadura):
        if item.defensa > repartir_armadura(ARMADURA_TIER[item.tier][1])[item.slot]:
            raise ValueError("La pieza supera su presupuesto de Armadura.")
