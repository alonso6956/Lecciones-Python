"""Parada por grados y contrajuego de ataques poderosos."""

import unittest
from dataclasses import replace
from unittest.mock import patch

from character import Personaje
from combat_stats import estadisticas_combate
from defense_system import resolver_defensa
from enemies import crear_enemigo, elegir_enemigo, SPAWN_POR_HABITACION
from game_engine import MotorJuego
from initiative import calculateTurnOrder
from item_factory import item_factory
from test_game_design import SinAzar


class ParadaPorGradosTests(unittest.TestCase):
    def setUp(self):
        self.jugador = Personaje("Nivel 1", "espada_basica", dict(fuerza=1, destreza=1, constitucion=1))
        self.enemigo = crear_enemigo("Goblin", "Bárbaro")

    def parada(self, defensa, ataque, **opciones):
        base = item_factory.crear("espada_basica")
        with patch("defense_system.arma_de", side_effect=lambda modelo: replace(base, ataque=defensa if modelo is self.jugador else ataque)):
            return resolver_defensa(self.enemigo, self.jugador, 40, defendiendo=True, **opciones)

    def test_fronteras_y_medias_sin_azar(self):
        for defensor, grado, recibido, pierde in (
            ((9, 11), "completa", 20, True),
            ((9, 10), "parcial", 30, False),
            ((5, 7), "parcial", 30, False),
            ((5, 6), "debil", 36, False),
        ):
            with self.subTest(defensor=defensor):
                r = self.parada(defensor, (8, 12))
                self.assertEqual((r["parada"], r["dano"], r["pierde_accion"]), (grado, recibido, pierde))
                self.assertEqual(r["presion_ataque"], 10)

    def test_ejemplos_usuario_y_frontera_poderosa(self):
        for dano_defensor, poderoso, grado in ((7, False, "parcial"), (7, True, "parcial"), (10, False, "completa"), (10, True, "completa")):
            r = self.parada((dano_defensor, dano_defensor), (8, 8), poderoso=poderoso)
            self.assertEqual(r["parada"], grado)
            self.assertEqual(r["presion_ataque"], 10 if poderoso else 8)

    def test_rapido_no_admite_ningun_grado(self):
        r = self.parada((100, 100), (1, 1), rapido=True)
        self.assertEqual(r["dano"], 40)
        self.assertIsNone(r["parada"])
        self.assertFalse(r["pierde_accion"])

    def test_espada_inicial_vs_barbaro_es_parcial_o_debil(self):
        r = resolver_defensa(self.enemigo, self.jugador, 40, defendiendo=True)
        self.assertEqual((r["parada"], r["dano"]), ("parcial", 30))
        r = resolver_defensa(self.enemigo, self.jugador, 40, defendiendo=True, poderoso=True)
        self.assertEqual((r["parada"], r["dano"]), ("debil", 36))

    def test_escudo_no_compara_poder_y_sigue_siendo_fiable(self):
        self.jugador.fuerza = 10
        self.jugador.inventario.recolectar("escudo_hierro")
        self.jugador.inventario.equipar("escudo_hierro", self.jugador)
        r = resolver_defensa(self.enemigo, self.jugador, 40, defendiendo=True, poderoso=True)
        self.assertEqual(r["dano"], 16)
        self.assertTrue(r["bloqueo_activo"])
        self.assertTrue(r["pierde_accion"])


class PoderosoTests(unittest.TestCase):
    def motor(self):
        m = MotorJuego(rng=SinAzar())
        m.jugador = Personaje("Prueba", "espada_basica", dict(fuerza=1, destreza=1, constitucion=1))
        m.enemigo_actual = crear_enemigo("Goblin", "Bárbaro")
        return m

    def test_intencion_independiente_de_escalado_y_tirada(self):
        m = self.motor()
        for dano in (1, 10, 1000):
            with patch("game_engine.tirar_dano", return_value=dano), patch.object(m.rng, "random", return_value=.5):
                m._preparar_turno_enemigo()
            self.assertEqual((m.intencion, m.enemigo_dano), ("normal", dano))

    def test_poderoso_multiplica_dano_y_no_se_encadena(self):
        m = self.motor()
        with patch("game_engine.tirar_dano", return_value=8):
            m._preparar_turno_enemigo()
            self.assertEqual((m.intencion, m.enemigo_dano), ("poderoso", 12))
            m._accion_enemigo(0)
            self.assertEqual((m.intencion, m.enemigo_dano), ("normal", 8))
            m._accion_enemigo(0)
            self.assertEqual(m.intencion, "poderoso")

    def test_prioridad_baja_incluso_con_iniciativa_enemiga_mayor(self):
        for ultimo in (None, "jugador", "enemigo"):
            orden, _ = calculateTurnOrder(10, 100, ultimo_actor=ultimo, ataque_enemigo_poderoso=True)
            self.assertEqual(orden, ["jugador", "enemigo"])
        self.assertEqual(calculateTurnOrder(10, 100)[0], ["enemigo", "jugador"])

    def test_motor_transmite_presion_poderosa(self):
        m = self.motor()
        m.is_defending = True
        m._preparar_turno_enemigo()
        with patch.object(m, "_defensa_del_golpe", wraps=m._defensa_del_golpe) as resolver:
            m._accion_enemigo(0)
        self.assertTrue(resolver.call_args.kwargs["poderoso"])

    def test_presupuesto_barbaros_iniciales_y_enemigos_posteriores(self):
        for raza in ("Goblin", "Esqueleto"):
            datos = estadisticas_combate(crear_enemigo(raza, "Bárbaro"))
            promedio = (datos["ataque_minimo"] + datos["ataque_maximo"]) / 2
            self.assertTrue(6 <= promedio <= 10)
            self.assertTrue(10 <= promedio * 1.5 <= 15)
            self.assertTrue(5 <= 50 / promedio <= 8)
        self.assertEqual(crear_enemigo("Orco", "Bárbaro").calcular_dano_base(), 3)

    def test_primer_encuentro_basico_sin_eliminar_enemigos_posteriores(self):
        import random
        for seed in range(30):
            self.assertEqual(elegir_enemigo(1, random.Random(seed)).raza, "Goblin")
        self.assertEqual(SPAWN_POR_HABITACION[1], (2, 9, {"Goblin": 90, "Esqueleto": 10}))
        self.assertEqual(elegir_enemigo(50, random.Random(0)).arquetipo, "Jefe")


if __name__ == "__main__":
    unittest.main()
