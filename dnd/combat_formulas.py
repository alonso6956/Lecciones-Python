FACTOR_CONTROL = 20.0
MITIGACION_MINIMA = 0.35
MITIGACION_MAXIMA = 0.90
EVASION_BASE = 0.05
EVASION_POR_DESTREZA = 0.03
VELOCIDAD_POR_DESTREZA = 1


def calcular_evasion(destreza):
    """5% base + 3% por cada punto de DEX posterior al primero."""
    return min(1.0, EVASION_BASE + max(0, destreza - 1) * EVASION_POR_DESTREZA)


def calcular_velocidad(velocidad_base, destreza):
    """Cada punto de DEX posterior al primero aporta 1 de Velocidad."""
    return velocidad_base + max(0, destreza - 1) * VELOCIDAD_POR_DESTREZA


def calcular_dano_habilidad(
    *,
    dano_base,
    dano_arma,
    habilidad,
    nivel_habilidad,
    valor_atributo,
    defensa_objetivo,
    constitucion_objetivo,
):
    """Calcula una habilidad desde su atributo y nivel, no desde el arma."""
    factor_escalado = 1 + max(0, valor_atributo - 1) * 0.20
    dano_potencial = (
        (dano_base + dano_arma)
        * factor_escalado
        * habilidad.multiplicador_dano(nivel_habilidad)
    )
    presion_defensiva = defensa_objetivo + constitucion_objetivo * 0.50
    mitigacion = FACTOR_CONTROL / (FACTOR_CONTROL + presion_defensiva)
    mitigacion = max(MITIGACION_MINIMA, min(MITIGACION_MAXIMA, mitigacion))
    return max(1, round(dano_potencial * mitigacion))
