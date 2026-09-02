import math


FACTOR_MITIGACION_ARMADURA = 22.0
EVASION_BASE = 0.05
EVASION_POR_DESTREZA = 0.03
VELOCIDAD_POR_DESTREZA = 1
UMBRAL_HACK_SLASH = 0.70
PESO_POR_PENALIZACION = 10
EVASION_PERDIDA_POR_PESO = 0.05
VELOCIDAD_PERDIDA_POR_PESO = 3


def calcular_evasion(destreza):
    """5% base + 3% por cada punto de DEX posterior al primero."""
    return min(1.0, EVASION_BASE + max(0, destreza - 1) * EVASION_POR_DESTREZA)


def calcular_velocidad(velocidad_base, destreza):
    """Cada punto de DEX posterior al primero aporta 1 de Velocidad."""
    return velocidad_base + max(0, destreza - 1) * VELOCIDAD_POR_DESTREZA


def calcular_penalizaciones_peso(peso_equipado, capacidad_peso=0):
    """Penaliza cada tramo iniciado de 10 puntos por encima de la capacidad."""
    sobrepeso = max(0, peso_equipado - capacidad_peso)
    tramos = math.ceil(sobrepeso / PESO_POR_PENALIZACION)
    return {
        "evasion": tramos * EVASION_PERDIDA_POR_PESO,
        "velocidad": tramos * VELOCIDAD_PERDIDA_POR_PESO,
    }


def calcular_mitigacion_armadura(armadura):
    """Devuelve la mitigación producida exclusivamente por la armadura."""
    armadura = max(0, armadura)
    return armadura / (armadura + FACTOR_MITIGACION_ARMADURA)


def aplicar_mitigacion_dano(dano_bruto, bloqueo_escudo=0, armadura=0):
    """Aplica bloqueo de escudo y después mitigación de armadura."""
    porcentaje_bloqueo = max(0.0, min(1.0, bloqueo_escudo))

    # Primera capa defensiva: el escudo solo modifica el daño bruto.
    dano_tras_escudo = dano_bruto * (1 - porcentaje_bloqueo)

    # Segunda capa defensiva: la armadura mitiga el resultado anterior.
    mitigacion_armadura = calcular_mitigacion_armadura(armadura)
    return dano_tras_escudo * (1 - mitigacion_armadura)


def calcular_bonus_hack_slash(salud_actual, salud_maxima, nivel_habilidad):
    """Bonus del tercer golpe según el porcentaje actual de vida del enemigo."""
    del nivel_habilidad
    if salud_maxima <= 0:
        return 0.0

    porcentaje_salud = max(0.0, min(1.0, salud_actual / salud_maxima))
    if porcentaje_salud > 0.70:
        return 0.0
    if porcentaje_salud > 0.50:
        return 0.05
    if porcentaje_salud > 0.30:
        return 0.10
    return 0.20


def calcular_dano_bloqueo_contraataque(
    dano_arma,
    constitucion,
    bloqueo_exitoso=False,
    porcentaje_dano_bloqueado=0,
):
    """Daño bruto: base con CON más el porcentaje completo que bloquea el escudo."""
    dano_bruto = dano_arma * (1 + max(0, constitucion) * 0.05)
    if bloqueo_exitoso:
        porcentaje = max(0.0, min(1.0, porcentaje_dano_bloqueado))
        # Se añade el 100% del valor de bloqueo: un escudo que bloquea 20%
        # aporta exactamente +20% al daño, no el 10% de ese porcentaje.
        dano_adicional_bloqueo = dano_bruto * porcentaje
        dano_bruto += dano_adicional_bloqueo
    return dano_bruto


def calcular_dano_habilidad(
    *,
    dano_base,
    dano_arma,
    habilidad,
    nivel_habilidad,
    valor_atributo,
    defensa_objetivo,
    constitucion_objetivo,
    bloqueo_escudo=0,
    bloqueo_exitoso=False,
    porcentaje_dano_bloqueado=0,
):
    """Calcula el daño bruto y aplica escudo y armadura en capas separadas."""
    if habilidad.id == "bloqueo_contraataque":
        dano_bruto = calcular_dano_bloqueo_contraataque(
            dano_arma,
            valor_atributo,
            bloqueo_exitoso,
            porcentaje_dano_bloqueado,
        )
    else:
        factor_escalado = 1 + max(0, valor_atributo - 1) * 0.20
        dano_bruto = (
            (dano_base + dano_arma)
            * factor_escalado
            * habilidad.multiplicador_dano(nivel_habilidad)
        )
    # Se conserva el argumento de constitución por compatibilidad, pero la nueva
    # fórmula depende únicamente de la armadura.
    _ = constitucion_objetivo
    bloqueo_aplicable = 0 if habilidad.inbloqueable else bloqueo_escudo
    dano_final = aplicar_mitigacion_dano(
        dano_bruto,
        bloqueo_escudo=bloqueo_aplicable,
        armadura=defensa_objetivo,
    )
    return max(1, round(dano_final))
