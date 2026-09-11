"""Compras previas a la expedición y regresiones de guardado."""

import random
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from character import Personaje
from character_roster import CharacterRoster, deserializar_personaje
from game_engine import ErrorJuego, MotorJuego
from item_factory import item_factory
from persistence import ErrorGuardado
from shop import Shop


class ShopTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.roster = CharacterRoster(self.temp.name)
        self.a = Personaje("Uno", "espada_basica", {"fuerza": 10, "destreza": 10, "constitucion": 10})
        self.b = Personaje("Dos", "espada_basica", {"fuerza": 10, "destreza": 10, "constitucion": 10})
        for p in (self.a, self.b):
            p.oro = 200
            self.roster.save_to_disk(p)
        self.motor = MotorJuego(random.Random(17), self.roster)

    def test_compra_afecta_solo_personaje_elegido_y_persiste(self):
        antes_a = self.roster.obtener(self.a.id)
        vault = self.roster.vault.serializar()
        estado = self.motor.comprar("pociones", "Pocion mediana", self.b.id, 3)
        precio = item_factory.crear("pocion_mediana").precio
        self.assertEqual(estado["oro"], 200 - 3 * precio)
        self.assertEqual(self.roster.obtener(self.a.id), antes_a)
        self.assertEqual(self.roster.vault.serializar(), vault)
        self.assertEqual(self.motor.fase, "menu")
        self.assertIsNone(self.motor.jugador)
        nuevo = MotorJuego(roster=CharacterRoster(self.temp.name))
        nuevo.cargar_personaje(self.b.id)
        self.assertEqual(nuevo.jugador.inventario.cantidad("pocion_mediana"), 3)
        nuevo.jugador.hp -= 30
        nuevo.fase = "transicion"
        nuevo.usar_item("pocion_mediana")
        self.assertEqual(nuevo.jugador.inventario.cantidad("pocion_mediana"), 2)
        nuevo.siguiente_habitacion()
        guardado = deserializar_personaje(CharacterRoster(self.temp.name).obtener(self.b.id))
        self.assertEqual(guardado.inventario.cantidad("pocion_mediana"), 2)

    def test_todas_las_habitaciones_son_combates_incluso_con_oro(self):
        self.motor.cargar_personaje(self.a.id)
        self.motor.jugador.oro = 100000
        for habitacion in range(1, 51):
            self.motor.numero_habitacion = habitacion
            self.assertEqual(self.motor._elegir_habitacion(), "combate")
        self.motor.numero_habitacion = 1
        for _ in range(5):
            self.motor.fase = "transicion"
            self.motor.siguiente_habitacion()
            self.assertEqual(self.motor.fase, "combate")
            self.assertIsNone(self.motor.estado()["tienda"])

    def test_comprar_rechazado_en_cualquier_fase_fuera_del_menu(self):
        antes = self.roster.personajes
        for fase in ("combate", "transicion", "nivel", "tienda", "muerte", "fin", "inicio"):
            self.motor.fase = fase
            with self.assertRaises(ErrorJuego):
                self.motor.comprar("pociones", "Pocion mediana", self.a.id)
        self.assertEqual(self.roster.personajes, antes)

    def test_cantidad_producto_personaje_y_oro_validados_antes_de_guardar(self):
        antes = self.roster.personajes
        for cantidad in (True, 0, -1, 1.5, "2", 1000, 999):
            with self.assertRaises(ValueError):
                self.motor.comprar("pociones", "Pocion mediana", self.a.id, cantidad)
        for personaje_id in (None, "", "inexistente"):
            with self.assertRaises(ValueError):
                self.motor.comprar("pociones", "Pocion mediana", personaje_id)
        for categoria, nombre in (([], "x"), ("materiales", "Hierro"), ("armas", {}), ("armas", "inexistente")):
            with self.assertRaises(ValueError):
                self.motor.comprar(categoria, nombre, self.a.id)
        self.assertEqual(self.roster.personajes, antes)

    def test_fallo_de_disco_no_cobra_ni_entrega_producto(self):
        antes = self.roster.personajes
        with patch("persistence.os.replace", side_effect=OSError("Sin espacio")):
            with self.assertRaises(ErrorGuardado):
                self.motor.comprar("armas", "Maza de hierro", self.a.id)
        self.assertEqual(self.roster.personajes, antes)
        self.assertEqual(CharacterRoster(self.temp.name).personajes, antes)

    def test_inventario_lleno_no_cobra(self):
        self.a.inventario.capacidad = 1
        self.roster.save_to_disk(self.a)
        antes = self.roster.personajes
        with self.assertRaises(ValueError):
            self.motor.comprar("armas", "Maza de hierro", self.a.id)
        self.assertEqual(self.roster.personajes, antes)

    def test_compra_equipa_si_es_compatible_y_guarda_secundario_si_no(self):
        self.motor.comprar("armas", "Maza de hierro", self.a.id)
        personaje = deserializar_personaje(self.roster.obtener(self.a.id))
        self.assertEqual(personaje.inventario.arma_equipada.id, "maza_hierro")
        self.motor.comprar("secundarios", "Escudo de hierro", self.a.id)
        personaje = deserializar_personaje(self.roster.obtener(self.a.id))
        self.assertEqual(personaje.inventario.cantidad("escudo_hierro"), 1)
        self.assertIsNone(personaje.inventario.secundario_equipado)

    def test_victoria_final_guarda_antes_de_salir(self):
        self.motor.cargar_personaje(self.a.id)
        self.motor.numero_habitacion = 50
        self.motor.fase = "transicion"
        self.motor.jugador.oro += 100
        self.motor.siguiente_habitacion()
        self.assertEqual(self.motor.resultado, "victoria")
        self.motor.abandonar()
        self.assertEqual(Shop(CharacterRoster(self.temp.name)).estado(self.a.id)["oro"], 300)


if __name__ == "__main__":
    unittest.main()
