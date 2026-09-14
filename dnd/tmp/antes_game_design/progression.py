"""Hitos compartidos; las clases aún solo aportan una etiqueta."""

CLASES = {
    "guerrero": {"nombre": "Guerrero", "habilidades": [], "pasivas": []},
    "picaro": {"nombre": "Pícaro", "habilidades": [], "pasivas": []},
    "guardian": {"nombre": "Guardián", "habilidades": [], "pasivas": []},
}
CHISPA_INICIAL = "chispa_latente"
NIVEL_DESBLOQUEO_CHISPA = 30


def habilidades_de_clase(clase):
    # TODO: Integrar los árboles de habilidades activas/pasivas de cada clase.
    return CLASES.get(clase, {}).get("habilidades", [])


def comprobar_hitos(personaje):
    eventos = []
    if personaje.nivel >= 10 and personaje.clase is None:
        eventos.append("elegir_clase")
    if personaje.nivel >= NIVEL_DESBLOQUEO_CHISPA and personaje.chispa is None:
        personaje.chispa = CHISPA_INICIAL
        eventos.append("infestacion_chispa")
        # TODO: Integrar Entes, modificadores de estadísticas y habilidades de chispa.
    return eventos
