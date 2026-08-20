from items import calcular_factor_arma


MULTIPLICADOR_HABILIDAD = 1.50
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
    nombre_arma,
    fuerza,
    destreza,
    defensa_objetivo,
    constitucion_objetivo,
):
    """Calcula daño de habilidad escalado y amortiguado por el objetivo.

    Primero, el perfil del arma convierte STR/DEX en un factor de crecimiento.
    El potencial es (base + arma) por perfil por multiplicador de habilidad.
    Después, Defensa y CON forman la presión defensiva del objetivo y entran
    en la curva control / (control + presión), con rendimientos decrecientes.

    La mitigación queda entre 35% y 90%: el suelo evita que la habilidad quede
    obsoleta contra stats altas y el techo evita ignorar objetivos débiles.
    Como no depende de una clase concreta, sirve también para enemigos.
    """
    factor_escalado = calcular_factor_arma(nombre_arma, fuerza, destreza)
    dano_potencial = (
        (dano_base + dano_arma)
        * factor_escalado
        * MULTIPLICADOR_HABILIDAD
    )
    presion_defensiva = defensa_objetivo + constitucion_objetivo * 0.50
    mitigacion = FACTOR_CONTROL / (FACTOR_CONTROL + presion_defensiva)
    mitigacion = max(MITIGACION_MINIMA, min(MITIGACION_MAXIMA, mitigacion))
    return max(1, round(dano_potencial * mitigacion))
