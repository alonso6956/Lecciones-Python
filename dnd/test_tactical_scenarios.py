"""Combate de grupos, mapas fijos y regresión del sangrado."""

import unittest
from copy import deepcopy
from dataclasses import asdict, replace
from unittest.mock import patch

from tactical_combat import CombatResolver
from tactical_controller import PrototypeController
from tactical_models import Encuentro, preparacion_ofensiva
from tactical_scenarios import ESCENARIOS


class ScenarioTests(unittest.TestCase):
    def test_three_enemies_act_and_no_boss_mechanics(self):
        controller = PrototypeController()
        controller.iniciar(42)
        battle = controller.combate
        battle.paso()
        self.assertEqual(len(battle.cerebros), 3)
        actors = {e.actor_id for e in battle.log.eventos if e.tipo == "decision_ia"}
        self.assertEqual(actors, set(controller.encuentro.ids_enemigos))
        result = battle.ejecutar()
        self.assertIsNone(result["final"]["jefe"])
        self.assertFalse({"escudo_activado", "tick_sangrado", "castigo_escudo"} & {e.tipo for e in battle.log.eventos})
        self.assertEqual(result["motivo"], "enemigos_derrotados")
        self.assertTrue(all(not a.vivo for a in battle.enemigos))
        for frame in battle.frames:
            actors = frame["party"] + frame["enemigos"]
            occupied = [tuple(frame["tablero"]["posiciones"][a["id"]]) for a in actors if a["hp"] > 0]
            self.assertEqual(len(occupied), len(set(occupied)))

    def test_death_retargets_and_victory_requires_all(self):
        battle = CombatResolver(preparacion_ofensiva(), Encuentro(grupo=True))
        battle._dano(battle.party[0], battle.enemigos[0], 10000, "prueba")
        self.assertIsNone(battle.resultado)
        with patch.object(battle, "_golpe", return_value=1):
            battle._accion_aliado(battle.party[0])
        action = [e for e in battle.log.eventos if e.tipo == "accion"][-1]
        self.assertNotEqual(action.objetivo_id, battle.enemigos[0].id)
        for enemy in battle.enemigos[1:]:
            battle._dano(battle.party[0], enemy, 10000, "prueba")
        self.assertEqual(battle.resultado, "victoria")

    def test_fixed_maps_reject_terrain_enemy_and_manual_traps(self):
        controller = PrototypeController()
        original = controller.estado()
        for change in ("terrain", "enemy", "trap"):
            plan = controller.tablero.plan()
            if change == "enemy":
                plan["posiciones"][controller.encuentro.ids_enemigos[0]] = [9, 1]
            else:
                plan["celdas"].append({"x": 3, "y": 0, "tipo": "trampa_aliada" if change == "trap" else "barro"})
            with self.assertRaises(ValueError):
                controller.configurar_campo(plan)
            self.assertEqual(controller.estado(), original)
        selections = [asdict(replace(s, maniobra="trampa")) for s in controller.selecciones]
        with self.assertRaises(ValueError):
            controller.preparar(selections)
        plan = controller.tablero.plan()
        plan["posiciones"][controller.selecciones[0].personaje_id] = [0, 7]
        controller.configurar_campo(plan)
        self.assertEqual(controller.tablero.posiciones[controller.selecciones[0].personaje_id], (0, 7))

    def test_presets_retry_and_determinism(self):
        for scenario in ESCENARIOS:
            with self.subTest(scenario=scenario):
                controller = PrototypeController()
                controller.seleccionar_escenario(scenario)
                plan = deepcopy(controller.tablero.plan())
                controller.iniciar(1234)
                with self.assertRaises(ValueError):
                    controller.seleccionar_escenario("patrulla_bosque")
                while controller.fase == "combate":
                    controller.avanzar()
                result = controller.combate.resumen()
                controller.reajustar()
                self.assertEqual(controller.tablero.plan(), plan)
                controller.iniciar(1234)
                self.assertEqual(result, controller.combate.ejecutar())

    def test_traps_require_capability_not_manual_selection(self):
        controller = PrototypeController()
        controller.iniciar()
        battle = controller.combate
        actor = battle.party[0]
        battle.tablero.posiciones[actor.id] = (5, 1)
        actor.seleccion = replace(actor.seleccion, maniobra="trampa")
        self.assertFalse(battle._maniobra(actor))
        actor.habilidades_tacticas = ("trampa",)
        self.assertTrue(battle._maniobra(actor))
        self.assertFalse(battle._maniobra(actor))

    def test_boss_miss_does_not_apply_or_refresh_bleed(self):
        for with_board in (False, True):
            controller = PrototypeController(encuentro=Encuentro())
            controller.estado()
            battle = CombatResolver(controller.selecciones, tablero=controller.tablero.plan() if with_board else None)
            battle.party[0].estados["sangrado"] = {"cargas": 1, "vence": 3}
            before = [deepcopy(a.estados) for a in battle.party]
            with patch.object(battle, "_golpe", return_value=0):
                battle._accion_jefe()
            self.assertEqual([a.estados for a in battle.party], before)
            self.assertFalse(any(e.tipo == "estado_aplicado" for e in battle.log.eventos))

    def test_boss_hit_still_applies_bleed(self):
        battle = CombatResolver(preparacion_ofensiva())
        with patch.object(battle, "_golpe", return_value=1):
            battle._accion_jefe()
        self.assertTrue(all(a.estados["sangrado"]["cargas"] == 1 for a in battle.party))


if __name__ == "__main__":
    unittest.main()
