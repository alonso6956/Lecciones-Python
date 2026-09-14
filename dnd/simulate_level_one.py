"""Duelo inicial reproducible, sin guardar ni modificar personajes del usuario."""

import argparse
import json
import random
from collections import Counter

from character import Personaje
from enemies import crear_enemigo, ARQUETIPOS_COMUNES
from game_engine import MotorJuego
from defense_system import resolver_defensa


def simular(n=200):
    resultados = []
    for raza in ("Goblin", "Esqueleto"):
        for arquetipo in ARQUETIPOS_COMUNES:
            for politica in ("atacar", "parada_completa"):
                victorias = turnos = 0
                intenciones = Counter()
                for seed in range(n):
                    motor = MotorJuego(rng=random.Random(seed))
                    motor.jugador = Personaje("Simulación", "espada_basica", dict(fuerza=1, destreza=1, constitucion=1))
                    motor.enemigo_actual = crear_enemigo(raza, arquetipo)
                    motor.fase = "combate"
                    motor._resolver_victoria = lambda: setattr(motor, "fase", "victoria")
                    motor._preparar_respawn = lambda: setattr(motor, "fase", "muerte")
                    motor._preparar_turno_enemigo()
                    for _ in range(100):
                        if motor.fase != "combate" or motor.jugador.hp <= 0:
                            break
                        intenciones[motor.intencion] += 1
                        accion = "atacar"
                        if politica == "parada_completa" and not motor.enemigo_actual.acciones_perdidas:
                            # Solo evalúa parada de arma: no toca un escudo ni tira azar.
                            defensa = resolver_defensa(motor.enemigo_actual, motor.jugador, 1,
                                defendiendo=True, rapido=motor.intencion == "rápido",
                                ataque={"poderoso": motor.intencion == "poderoso"})
                            if defensa["pierde_accion"]:
                                accion = "defender"
                        motor.actuar(accion)
                    victorias += motor.fase == "victoria"
                    turnos += motor.turno_global
                resultados.append(dict(raza=raza, arquetipo=arquetipo, politica=politica,
                    combates=n, victorias=victorias, porcentaje_victoria=round(victorias / n * 100, 1),
                    turnos_medios=round(turnos / n, 2), intenciones=dict(intenciones)))
    return resultados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=200)
    args = parser.parse_args()
    if args.n < 1:
        parser.error("--n debe ser positivo")
    print(json.dumps(simular(args.n), ensure_ascii=True, indent=2))
