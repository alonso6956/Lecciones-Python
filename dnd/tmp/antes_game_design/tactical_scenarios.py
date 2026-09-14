"""Escenarios de prueba: cada encuentro lleva su mapa, sin editor de bioma."""

from tactical_board import Tablero
from tactical_models import Encuentro


ESCENARIOS = {
    "patrulla_ruinas": {"nombre": "Patrulla · Ruinas", "mapa": "Ruinas del paso",
        "descripcion": "Tres enemigos entre muros y coberturas. Derrota a toda la patrulla.",
        "grupo": True, "celdas": [(4, 2, "muro"), (4, 3, "muro"), (5, 5, "muro"),
            (2, 2, "cobertura"), (7, 5, "cobertura"), (6, 1, "altura")]},
    "patrulla_bosque": {"nombre": "Patrulla · Sendero", "mapa": "Sendero del bosque",
        "descripcion": "La misma patrulla en un sendero con barro y obstáculos. Compara tu formación.",
        "grupo": True, "celdas": [(4, 1, "muro"), (5, 6, "muro"), (4, 4, "barro"),
            (5, 4, "barro"), (6, 4, "barro"), (2, 5, "cobertura"), (7, 2, "cobertura")]},
    "guardian_patio": {"nombre": "Guardián · Patio", "mapa": "Patio de piedra",
        "descripcion": "Encuentro de jefe: sangrado cercano y escudo al 50% de vida.",
        "grupo": False, "celdas": [(4, 2, "muro"), (5, 5, "muro"),
            (2, 2, "cobertura"), (3, 5, "altura"), (6, 3, "barro")]},
}


def crear_encuentro(escenario_id):
    if escenario_id not in ESCENARIOS:
        raise ValueError("Escenario desconocido")
    grupo = ESCENARIOS[escenario_id]["grupo"]
    return Encuentro(id="patrulla_hostil" if grupo else "guardian_verdugo", grupo=grupo)


def crear_tablero(escenario_id, aliados, enemigos):
    datos = ESCENARIOS[escenario_id]
    posiciones = {id: [1 + i % 2, 1 + i] for i, id in enumerate(aliados)}
    posiciones.update({id: [8, 3 if len(enemigos) == 1 else 1 + i * 2] for i, id in enumerate(enemigos)})
    return Tablero({"posiciones": posiciones,
                    "celdas": [{"x": x, "y": y, "tipo": t} for x, y, t in datos["celdas"]]}, aliados, enemigos)
