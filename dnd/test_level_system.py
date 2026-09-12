import math
import unittest

from level_system import SistemaNiveles


def formula_runescape(nivel):
    if nivel <= 1:
        return 0
    total = 0
    for n in range(1, nivel):
        total += math.floor(n + 300 * (2 ** (n / 7)))
    return total // 4


class LevelSystemTests(unittest.TestCase):
    def test_formula_runescape_progresiva(self):
        sistema = SistemaNiveles()

        self.assertEqual(sistema.experiencia_necesaria(1), 0)
        for nivel in range(2, 11):
            with self.subTest(nivel=nivel):
                self.assertEqual(sistema.experiencia_necesaria(nivel), formula_runescape(nivel))

    def test_sube_de_nivel_con_xp_progresiva(self):
        sistema = SistemaNiveles()
        personaje = type("P", (), {"nivel": 1, "exp": 0})()

        objetivo = sistema.experiencia_necesaria(2)
        personaje.exp = objetivo
        self.assertTrue(sistema.puede_subir(personaje))

        personaje.exp = objetivo - 1
        self.assertFalse(sistema.puede_subir(personaje))


if __name__ == "__main__":
    unittest.main()
