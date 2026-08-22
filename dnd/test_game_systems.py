import tempfile
import unittest
from pathlib import Path
from random import Random

from game_engine import MotorJuego
from persistence import ErrorGuardado, GestorGuardado


class RespawnTests(unittest.TestCase):
    def test_respawn_conserva_personaje_y_reinicia_expedicion(self):
        motor = MotorJuego(Random(1))
        motor.nueva_partida()
        motor.iniciar("Ada", "Dagas de hierro")
        jugador = motor.jugador
        jugador.fuerza = 4
        jugador.destreza = 5
        jugador.constitucion = 3
        jugador.nivel = 7
        jugador.oro = 123
        jugador.exp = 44
        jugador.arma = "Estoque de acero"
        jugador.inventario.append("Estoque de acero")
        jugador.salud_maxima = jugador.calcular_salud_maxima()
        jugador.hp = 0
        motor.numero_habitacion = 12

        motor._preparar_respawn()

        self.assertEqual(motor.fase, "muerte")
        self.assertEqual(jugador.hp, 0)
        self.assertEqual(motor.numero_habitacion, 12)

        motor.respawn()

        self.assertIs(motor.jugador, jugador)
        self.assertEqual(motor.numero_habitacion, 1)
        self.assertEqual(motor.fase, "combate")
        self.assertIsNone(motor.resultado)
        self.assertEqual(jugador.hp, jugador.salud_maxima)
        self.assertEqual(
            (jugador.fuerza, jugador.destreza, jugador.constitucion),
            (4, 5, 3),
        )
        self.assertEqual((jugador.nivel, jugador.oro, jugador.exp), (7, 123, 44))
        self.assertEqual(jugador.arma, "Estoque de acero")
        self.assertEqual(jugador.inventario, ["Dagas de hierro", "Estoque de acero"])
        self.assertIsNotNone(motor.enemigo_actual)

    def test_guardado_restaura_inventario_y_combate(self):
        original = MotorJuego(Random(3))
        original.nueva_partida()
        original.iniciar("Ada", "Dagas de hierro")
        original.jugador.inventario.append("Estoque de acero")
        original.jugador.arma = "Estoque de acero"

        restaurado = MotorJuego(Random(4))
        restaurado.importar_guardado(original.exportar_guardado())

        self.assertEqual(restaurado.fase, "combate")
        self.assertEqual(restaurado.jugador.arma, "Estoque de acero")
        self.assertEqual(
            restaurado.jugador.inventario,
            ["Dagas de hierro", "Estoque de acero"],
        )
        self.assertIsNotNone(restaurado.enemigo_actual)


class SlotsGuardadoTests(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.gestor = GestorGuardado(Path(self.temporal.name))

    def tearDown(self):
        self.temporal.cleanup()

    @staticmethod
    def estado(nombre, habitacion):
        return {
            "fase": "transicion",
            "numero_habitacion": habitacion,
            "jugador": {"nombre": nombre, "nivel": habitacion},
        }

    def test_slots_son_independientes_y_exponen_resumen(self):
        self.gestor.guardar(1, self.estado("Ada", 3))
        self.gestor.guardar(2, self.estado("Lin", 8))

        self.assertEqual(self.gestor.cargar(1)["jugador"]["nombre"], "Ada")
        self.assertEqual(self.gestor.cargar(2)["jugador"]["nombre"], "Lin")
        slots = self.gestor.listar_slots()
        self.assertEqual(slots[0]["resumen"]["habitacion"], 3)
        self.assertEqual(slots[1]["resumen"]["habitacion"], 8)
        self.assertFalse(slots[2]["ocupado"])

    def test_rechaza_slots_fuera_de_rango(self):
        with self.assertRaises(ErrorGuardado):
            self.gestor.guardar(4, self.estado("Ada", 1))


if __name__ == "__main__":
    unittest.main()
