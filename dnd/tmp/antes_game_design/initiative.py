"""Cálculos puros de iniciativa y orden de actuación."""


def getActionPoints(velocidad, velocidad_rival, acumulador=0):
    """Devuelve acciones y remanente de iniciativa para el siguiente ciclo.

    Se suman los puntos de ventaja en cada ciclo y cada 6 puntos acumulados
    generan una acción extra. Así, +2 Velocidad sigue dando una acción cada
    tres ciclos, mientras ventajas grandes actúan desde el primer ciclo en vez
    de quedar retenidas hasta un burst artificial en el turno global 3.
    """
    if acumulador < 0:
        raise ValueError("El acumulador de velocidad no puede ser negativo.")
    ventaja = max(0, velocidad - velocidad_rival)
    acciones_extra, remanente = divmod(acumulador + ventaja, 6)
    return 1 + acciones_extra, remanente


def jugador_rompe_prioridad_rapida(velocidad_jugador, velocidad_enemigo):
    """Solo una Velocidad estrictamente mayor rompe la prioridad rápida."""
    return velocidad_jugador > velocidad_enemigo


def calculateTurnOrder(
    velocidad_jugador,
    velocidad_enemigo,
    ataque_enemigo_rapido=False,
    ultimo_actor=None,
    acumuladores=None,
):
    """Construye una cola sin remanentes entre ciclos de iniciativa.

    Un ataque rápido conserva prioridad salvo en empates ya iniciados: cuando
    las velocidades coinciden, ``ultimo_actor`` fuerza alternancia estricta y
    evita que una cola termine y la siguiente empiece con el mismo actor.
    """
    acumuladores = acumuladores or {"jugador": 0, "enemigo": 0}
    acciones_jugador, resto_jugador = getActionPoints(
        velocidad_jugador,
        velocidad_enemigo,
        acumuladores.get("jugador", 0),
    )
    acciones_enemigo, resto_enemigo = getActionPoints(
        velocidad_enemigo,
        velocidad_jugador,
        acumuladores.get("enemigo", 0),
    )
    puntos = {
        "jugador": acciones_jugador,
        "enemigo": acciones_enemigo,
    }
    nuevos_acumuladores = {
        "jugador": resto_jugador,
        "enemigo": resto_enemigo,
    }

    # Con velocidades idénticas no existen puntos extra. La primera posición
    # se asigna al opuesto del último actor para impedir E,E entre dos colas.
    if velocidad_jugador == velocidad_enemigo:
        if ultimo_actor == "jugador":
            return ["enemigo", "jugador"], nuevos_acumuladores
        if ultimo_actor == "enemigo":
            return ["jugador", "enemigo"], nuevos_acumuladores
        primero = "enemigo" if ataque_enemigo_rapido else "jugador"
        segundo = "jugador" if primero == "enemigo" else "enemigo"
        return [primero, segundo], nuevos_acumuladores

    if ataque_enemigo_rapido and not jugador_rompe_prioridad_rapida(
        velocidad_jugador,
        velocidad_enemigo,
    ):
        prioridad = ["enemigo", "jugador"]
    else:
        prioridad = sorted(
            puntos,
            key=lambda entidad: (
                velocidad_jugador if entidad == "jugador" else velocidad_enemigo
            ),
            reverse=True,
        )
    cola = [
        entidad
        for entidad in prioridad
        for _ in range(puntos[entidad])
    ]
    return cola, nuevos_acumuladores
