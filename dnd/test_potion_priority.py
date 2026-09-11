"""Las pociones tienen prioridad sin otorgar acciones adicionales."""

import random
import unittest
from unittest.mock import patch

from game_engine import ErrorJuego, MotorJuego
from item_factory import item_factory


class PotionPriorityTests(unittest.TestCase):
    def setUp(self):
        self.motor = MotorJuego(random.Random(1234))
        self.motor.nueva_partida()
        self.motor.iniciar("Pociones")
        self.motor.jugador.inventario.recolectar("pocion_mediana", 2)
        self.motor.jugador.hp = 1
        self.vida_tras_pocion = 1 + item_factory.crear("pocion_mediana").valor

    def test_pocion_precede_ataque_rapido_que_seria_letal(self):
        m = self.motor
        m.intencion = "rápido"
        # En empate, haber actuado último también daría prioridad al enemigo.
        m.enemigo_actual.destreza = m.jugador.destreza
        m.ultimo_actor = "jugador"
        vida_al_atacar = []

        def atacar(_defensa):
            vida_al_atacar.append(m.jugador.hp)
            m.jugador.hp -= 10

        with patch.object(m, "_accion_enemigo", side_effect=atacar):
            m.usar_item("pocion_mediana")
        self.assertEqual(vida_al_atacar, [self.vida_tras_pocion])
        self.assertEqual(m.jugador.hp, self.vida_tras_pocion - 10)
        self.assertEqual(m.fase, "combate")
        self.assertEqual(m.jugador.inventario.cantidad("pocion_mediana"), 1)
        turno = next(e for e in m.eventos if e["tipo"] == "turno_iniciado")
        self.assertEqual(turno["datos"]["orden"], ["jugador", "enemigo"])

    def test_prioridad_conserva_acciones_extra_y_consume_solo_una_pocion(self):
        m = self.motor
        orden = []
        restos = {"jugador": 2, "enemigo": 4}
        with patch("game_engine.calculateTurnOrder", return_value=(
            ["enemigo", "enemigo", "jugador", "jugador"], restos,
        )), patch.object(m, "_accion_enemigo", side_effect=lambda _: orden.append(("enemigo", m.jugador.hp))), patch.object(
            m, "_accion_jugador", side_effect=lambda accion: (orden.append((accion, m.jugador.hp)) or (0, 0)),
        ):
            m.usar_item("pocion_mediana")
        self.assertEqual(orden, [("enemigo", self.vida_tras_pocion), ("enemigo", self.vida_tras_pocion), ("atacar", self.vida_tras_pocion)])
        self.assertEqual(m.jugador.inventario.cantidad("pocion_mediana"), 1)
        self.assertEqual(m.acumuladores_velocidad, restos)
        turno = next(e for e in m.eventos if e["tipo"] == "turno_iniciado")
        self.assertEqual(turno["datos"]["orden"], ["jugador", "enemigo", "enemigo", "jugador"])

    def test_pocion_invalida_no_inicia_turno(self):
        m = self.motor
        m.jugador.hp = m.jugador.salud_maxima
        with self.assertRaises(ErrorJuego):
            m.usar_item("pocion_mediana")
        self.assertEqual(m.turno_global, 0)
        self.assertEqual(m.jugador.inventario.cantidad("pocion_mediana"), 2)

    def test_prioridad_no_elimina_aturdimiento(self):
        m = self.motor
        m.aturdimiento_jugador = 1
        with patch("game_engine.calculateTurnOrder", return_value=(
            ["enemigo", "jugador"], {"jugador": 0, "enemigo": 0},
        )), patch.object(m, "_accion_enemigo"):
            m.usar_item("pocion_mediana")
        self.assertEqual(m.jugador.hp, 1)
        self.assertEqual(m.jugador.inventario.cantidad("pocion_mediana"), 2)
        self.assertEqual(m.aturdimiento_jugador, 0)


if __name__ == "__main__":
    unittest.main()
