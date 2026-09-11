"""Paridad de estadísticas y golpes entre Dungeon y combate táctico."""

import random
import unittest
from dataclasses import replace
from unittest.mock import Mock, patch

from character import Personaje
from character_roster import serializar_personaje
from combat_stats import estadisticas_combate, tirar_dano
from combat_formulas import aplicar_mitigacion_dano
from enemies import crear_enemigo
from game_engine import MotorJuego
from item_factory import item_factory
from tactical_models import Actor, BuildManager, Encuentro, Seleccion, preparacion_ofensiva
from tactical_combat import CombatResolver


class CombatStatsTests(unittest.TestCase):
    def test_roster_mismos_valores_que_estado_dungeon(self):
        personajes = []
        for n, arma in enumerate(("dagas_hierro", "espada_hierro", "maza_hierro")):
            p = Personaje(str(n), arma, {"fuerza": 20, "destreza": 20, "constitucion": 20})
            p.nivel = 20
            for item in item_factory.todos():
                if hasattr(item, "slot") and item.cumple_requisitos(p):
                    p.inventario.recolectar(item.id)
                    p.inventario.equipar(item.id, p)
            p.recalcular_por_equipo()
            personajes.append(p)
        roster = [serializar_personaje(p) for p in personajes]
        selecciones = [Seleccion(p.id, arma=p.inventario.arma_equipada.id) for p in personajes]
        for build in ("ofensiva", "adaptacion"):
            party = BuildManager.crear_party([replace(s, build=build) for s in selecciones], roster)
            for p, actor in zip(personajes, party):
                motor = MotorJuego(random.Random(7))
                motor.jugador = p
                dungeon = motor.estado()["jugador"]
                tactico = actor.estado()
                for key in estadisticas_combate(p):
                    self.assertEqual(tactico[key], dungeon[key], key)
                self.assertEqual(actor.defensa, motor._defensa_total_jugador())
                self.assertEqual(actor.velocidad, p.velocidad)
                self.assertFalse(actor.habilidades_tacticas)
        self.assertEqual(roster, [serializar_personaje(p) for p in personajes])

    def test_jefe_es_el_del_dungeon(self):
        enemigo = crear_enemigo("Guardián", "Jefe")
        actor = Encuentro().crear_jefe()
        self.assertEqual(estadisticas_combate(enemigo), estadisticas_combate(actor.modelo))
        self.assertEqual(actor.hp_max, 114)
        self.assertEqual(actor.velocidad, 14)
        self.assertEqual(actor.defensa, 8)

    def test_tiradas_reales_sin_multiplicador_ni_promedio(self):
        actor = BuildManager.crear_party(preparacion_ofensiva())[0]
        motor = MotorJuego(random.Random(91))
        motor.jugador = actor.modelo
        rng = random.Random(91)
        valores = [tirar_dano(actor.modelo, rng) for _ in range(40)]
        self.assertEqual(valores, [motor._dano_total_jugador() for _ in range(40)])
        self.assertGreater(len(set(valores)), 1)
        stats = actor.estado()
        self.assertTrue(all(stats["ataque_minimo"] <= v <= stats["ataque_maximo"] for v in valores))

    def test_golpes_en_ambas_direcciones_mitigan_y_redondean_como_dungeon(self):
        combate = CombatResolver(preparacion_ofensiva())
        for atacante, objetivo in ((combate.party[0], combate.jefe), (combate.jefe, combate.party[0])):
            combate.rng = Mock()
            combate.rng.randint.return_value = item_factory.crear(atacante.modelo.arma).ataque[0]
            combate.rng.random.return_value = 0.99
            bruto = atacante.modelo.calcular_dano_base() + combate.rng.randint.return_value
            esperado = max(1, round(aplicar_mitigacion_dano(bruto, armadura=objetivo.defensa)))
            self.assertEqual(combate._golpe(atacante, objetivo), esperado)
            combate.rng.random.return_value = 0
            self.assertEqual(combate._golpe(atacante, objetivo), 0)

    def test_bloqueo_equipo_y_bonus_defensa_aplican(self):
        combate = CombatResolver(preparacion_ofensiva())
        actor = combate.party[0]
        actor.modelo.fuerza = 30
        actor.modelo.inventario.recolectar("espada_hierro")
        actor.modelo.inventario.equipar("espada_hierro", actor.modelo)
        actor.modelo.inventario.recolectar("escudo_hierro")
        actor.modelo.inventario.equipar("escudo_hierro", actor.modelo)
        combate.rng = Mock()
        combate.rng.randint.return_value = 5
        combate.rng.random.side_effect = [0.99, 0]
        with patch.object(actor.modelo, "bonus_pasivo_habilidad", side_effect=lambda tipo: 3 if tipo == "defensa" else 0):
            defensa = actor.modelo.calcular_defensa_base() + actor.modelo.inventario.armadura_equipo() + 3
            self.assertEqual(actor.defensa, defensa)
            escudo = actor.modelo.inventario.secundario_equipado
            esperado = max(1, round(aplicar_mitigacion_dano(
                combate.jefe.modelo.calcular_dano_base() + 5,
                bloqueo_escudo=escudo.porcentaje_dano_bloqueado, armadura=defensa)))
            self.assertEqual(combate._golpe(combate.jefe, actor), esperado)


if __name__ == "__main__":
    unittest.main()
