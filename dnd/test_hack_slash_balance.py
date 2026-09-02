import unittest

from character import Personaje
from combat_formulas import calcular_bonus_hack_slash
from habilidades import habilidad_factory


class HackSlashBalanceTests(unittest.TestCase):
    def setUp(self):
        self.personaje = Personaje(
            "Tester",
            "espada_hierro",
            {"fuerza": 5, "destreza": 3, "constitucion": 3},
        )
        self.habilidad = habilidad_factory.crear("hack_slash")

    def test_combo_nivel_1_mas_fuerte_que_un_ataque_basico(self):
        dano_basico = self.personaje.calcular_dano_base()
        combo = sum(
            max(1, round(dano_basico * self.habilidad.multiplicador_dano(1)))
            for _ in range(3)
        )
        self.assertGreater(combo, dano_basico + 3)

    def test_combo_maximo_puede_superar_15_de_dano(self):
        dano_basico = self.personaje.calcular_dano_base()
        combo = sum(
            max(1, round(dano_basico * self.habilidad.multiplicador_dano(5)))
            for _ in range(3)
        )
        self.assertGreater(combo, 15)

    def test_bonus_hack_slash_se_activa_en_70_50_y_30_por_ciento(self):
        self.assertAlmostEqual(calcular_bonus_hack_slash(70, 100, 1), 0.05)
        self.assertAlmostEqual(calcular_bonus_hack_slash(50, 100, 1), 0.10)
        self.assertAlmostEqual(calcular_bonus_hack_slash(30, 100, 1), 0.20)
        self.assertAlmostEqual(calcular_bonus_hack_slash(100, 100, 1), 0.0)


if __name__ == "__main__":
    unittest.main()
