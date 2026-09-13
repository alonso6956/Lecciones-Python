"""Regresiones del tablero con personajes y partidas temporales."""

import json
import tempfile
import threading
import unittest
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from character import Personaje
from character_roster import CharacterRoster
from tactical_board import Tablero, distancia
from tactical_combat import CombatResolver
from tactical_controller import PrototypeController
from tactical_models import BuildManager, Seleccion, Encuentro


class BoardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.roster = CharacterRoster(self.temp.name)
        self.heroes = []
        for i in range(6):
            p = Personaje(f"Heroe {i + 1}", "espada_basica", dict(fuerza=5, destreza=5, constitucion=5))
            self.roster.save_to_disk(p)
            self.heroes.append(p)
        self.controller = PrototypeController(encuentro=Encuentro(), roster=self.roster)
        self.controller.estado()

    def plan(self):
        plan = self.controller.tablero.plan()
        return plan

    def battle(self, plan=None):
        if plan is not None:
            self.controller.configurar_campo(plan)
        self.controller.iniciar(42)
        return self.controller.combate

    def test_six_unique_characters_keep_deployment_and_progress(self):
        original = self.roster.personajes
        plan = self.plan()
        plan["posiciones"][self.heroes[0].id] = [0, 7]
        self.controller.configurar_campo(plan)
        choices = [Seleccion(p.id, arma="espada_basica") for p in self.heroes]
        state = self.controller.preparar([asdict(s) for s in choices])
        self.assertEqual(len(state["party"]), 6)
        self.assertEqual(state["tablero"]["posiciones"][self.heroes[0].id], [0, 7])
        battle = self.battle()
        final = battle.ejecutar()
        self.assertIn(final["resultado"], ("victoria", "derrota"))
        self.assertEqual(len(battle.party), 6)
        self.assertEqual(self.roster.personajes, original)
        self.assertEqual(CharacterRoster(self.temp.name).personajes, original)

    def test_party_limits_duplicates_and_unknown_maneuvers(self):
        original = self.controller.estado()
        base = [asdict(Seleccion(p.id, arma="espada_basica")) for p in self.heroes]
        for choices in (base[:2], base + base[:1], [base[0]] * 3,
                        [{**s, "maniobra": "invalid"} for s in base[:3]]):
            with self.assertRaises(ValueError):
                self.controller.preparar(choices)
            self.assertEqual(self.controller.estado(), original)

    def test_empty_roster_shows_board_but_cannot_start(self):
        controller = PrototypeController(roster=CharacterRoster())
        state = controller.estado()
        self.assertFalse(state["tactico_disponible"])
        self.assertEqual(state["party"], [])
        self.assertEqual(len(state["tablero"]["posiciones"]), 3)
        with self.assertRaises(ValueError):
            controller.iniciar()

    def test_invalid_placement_leaves_plan_unchanged(self):
        original = self.controller.tablero.plan()
        hero = self.heroes[0].id
        for position in ([10, 1], [-1, 0], [True, 1], [1.2, 0], [3, 0], [2, 2], "A1"):
            plan = deepcopy(original)
            plan["posiciones"][hero] = position
            with self.subTest(position=position), self.assertRaises(ValueError):
                self.controller.configurar_campo(plan)
            self.assertEqual(self.controller.tablero.plan(), original)

    def test_walls_cannot_seal_arena_and_limits_are_validated(self):
        for cells in ([{"x": 4, "y": y, "tipo": "muro"} for y in range(8)],
                      [{"x": x, "y": 0, "tipo": "trampa_aliada"} for x in range(3, 7)],
                      [{"x": 0, "y": 0, "tipo": "muro"}],
                      [{"x": 4, "y": 2, "tipo": "invalid"}],
                      [{"x": 4, "y": 2, "tipo": "altura"}] * 2):
            plan = self.plan(); plan["celdas"] = cells
            with self.assertRaises(ValueError):
                self.controller.configurar_campo(plan)

    def test_path_routes_around_walls_and_accounts_for_mud(self):
        plan = self.plan()
        plan["celdas"] = [{"x": 4, "y": 1, "tipo": "muro"}, {"x": 2, "y": 1, "tipo": "barro"}]
        board = Tablero(plan, self.controller.tablero.aliados, self.controller.encuentro.id)
        path = board.ruta(self.heroes[0].id, (8, 1), 1, set())
        self.assertIsNotNone(path)
        self.assertNotIn((4, 1), path)
        previous = board.posiciones[self.heroes[0].id]
        for point in path:
            self.assertEqual(distancia(previous, point), 1)
            previous = point
        self.assertEqual(board.coste((2, 1)), 2)
        self.assertFalse(board.visible((3, 1), (5, 1)))

    def test_far_targets_require_movement_and_stay_in_bounds(self):
        battle = self.battle(self.plan())
        old = dict(battle.tablero.posiciones)
        battle.paso()
        self.assertTrue(any(e.tipo == "movimiento" for e in battle.log.eventos))
        self.assertNotEqual(battle.tablero.posiciones, old)
        for view in battle.vistas:
            positions = [tuple(view["tablero"]["posiciones"][a["id"]]) for a in view["party"] + [view["jefe"]] if a["hp"] > 0]
            self.assertEqual(len(positions), len(set(positions)))
            self.assertTrue(all(0 <= x < 10 and 0 <= y < 8 for x, y in positions))
        self.assertTrue(battle.vistas)

    def test_weapon_range_and_line_of_sight(self):
        battle = self.battle(self.plan())
        actor = battle.party[0]
        battle.tablero.posiciones[actor.id] = (5, 3)
        battle.tablero.posiciones[battle.jefe.id] = (7, 3)
        self.assertFalse(battle.tablero.en_alcance((5, 3), (7, 3), 1))
        self.assertTrue(battle.tablero.en_alcance((5, 3), (7, 3), 2))
        battle.tablero.celdas[(6, 3)] = "muro"
        self.assertFalse(battle.tablero.en_alcance((5, 3), (7, 3), 2))

    def test_elevation_cover_smoke_and_flanking(self):
        battle = self.battle(self.plan())
        board = battle.tablero
        a, b = battle.party[:2]
        board.posiciones[a.id], board.posiciones[b.id], board.posiciones[battle.jefe.id] = (4, 3), (6, 3), (5, 3)
        factor, causes = board.multiplicador(a.id, battle.jefe.id, {a.id, b.id})
        self.assertAlmostEqual(factor, 1.15)
        self.assertIn("flanqueo", causes)
        board.celdas[(4, 3)] = "altura"
        board.celdas[(5, 3)] = "cobertura"
        board.efectos[(5, 3)] = {"tipo": "humo", "vence": 2}
        factor, causes = board.multiplicador(a.id, battle.jefe.id, {a.id})
        self.assertAlmostEqual(factor, 1.15 * .8 * .75)
        self.assertEqual(set(causes), {"altura", "cobertura", "humo"})
        board.expirar(2)
        self.assertFalse(board.efectos)

    def test_trap_consumes_stops_and_respects_teams(self):
        battle = self.battle(self.plan())
        actor = battle.party[0]
        battle.tablero.posiciones[actor.id] = (3, 0)
        battle.tablero.posiciones[battle.jefe.id] = (7, 0)
        battle.tablero.celdas[(4, 0)] = "trampa_rival"
        hp = actor.hp
        self.assertFalse(battle._acercar(actor, battle.jefe, 1))
        self.assertEqual(actor.hp, hp - 12)
        self.assertEqual(battle.tablero.posiciones[actor.id], (4, 0))
        self.assertNotIn((4, 0), battle.tablero.celdas)
        self.assertIn("inmovilizado", actor.estados)
        actor.estados.clear()
        battle.tablero.celdas[(5, 0)] = "trampa_aliada"
        battle._acercar(actor, battle.jefe, 1)
        self.assertEqual(actor.hp, hp - 12)
        self.assertEqual(battle.tablero.terreno((5, 0)), "trampa_aliada")

    def test_maneuvers_change_field_once_and_use_action(self):
        for maneuver in ("humo", "cobertura", "trampa"):
            battle = CombatResolver(self.controller.selecciones, roster=self.roster.personajes, tablero=self.plan())
            actor = battle.party[0]
            actor.habilidades_tacticas = (maneuver,)
            battle.tablero.posiciones[actor.id] = (5, 3)
            before = battle.jefe.hp
            battle._accion_aliado(actor)
            self.assertEqual(battle.jefe.hp, before)
            self.assertIn(actor.id, battle.maniobras_usadas)
            self.assertFalse(battle._maniobra(actor))
            if maneuver == "humo":
                self.assertEqual(len(battle.tablero.efectos), 5)
            else:
                self.assertIn("trampa_aliada" if maneuver == "trampa" else "cobertura", battle.tablero.celdas.values())

    def test_boss_bleed_is_local(self):
        battle = self.battle(self.plan())
        near, far, other = battle.party
        battle.tablero.posiciones[battle.jefe.id] = (5, 3)
        battle.tablero.posiciones[near.id] = (4, 3)
        battle.tablero.posiciones[far.id] = (0, 0)
        battle.tablero.posiciones[other.id] = (0, 7)
        with patch.object(battle, "_golpe", return_value=1):
            battle._accion_jefe()
        self.assertIn("sangrado", near.estados)
        self.assertNotIn("sangrado", far.estados)
        self.assertNotIn("sangrado", other.estados)

    def test_same_seed_plan_and_characters_reproduce_combat(self):
        args = dict(selecciones=self.controller.selecciones, roster=self.roster.personajes, tablero=self.plan(), seed=123)
        a, b = CombatResolver(**args), CombatResolver(**args)
        self.assertEqual(a.ejecutar(), b.ejecutar())

    def test_locked_edits_and_retry_restore_plan(self):
        plan = self.plan()
        self.controller.configurar_campo(plan)
        canonical = self.controller.tablero.plan()
        battle = self.battle()
        with self.assertRaises(ValueError):
            self.controller.configurar_campo(plan)
        with self.assertRaises(ValueError):
            self.controller.preparar([asdict(s) for s in self.controller.selecciones])
        while self.controller.fase == "combate":
            self.controller.avanzar()
        state = self.controller.reajustar()
        self.assertEqual(self.controller.tablero.plan(), canonical)
        self.assertFalse(state["tablero"]["efectos"])
        self.controller.iniciar()
        self.assertFalse(self.controller.combate.maniobras_usadas)
        self.assertTrue(all(a.hp == a.hp_max for a in self.controller.combate.party))

    def test_http_board_six_party_and_locks(self):
        import config
        with patch("config.cargar_configuracion", return_value=replace(config.cargar_configuracion(), data_dir=Path(self.temp.name))):
            import server
        from game_engine import MotorJuego
        with patch.multiple(server, roster=self.roster, motor=MotorJuego(roster=self.roster), prototipo=self.controller):
            http = server.ServidorDungeon(("127.0.0.1", 0), server.ManejadorDungeon)
            worker = threading.Thread(target=http.serve_forever, daemon=True); worker.start()
            def request(action, body=None):
                req = Request(f"http://127.0.0.1:{http.server_port}/api/tactico/{action}", data=json.dumps(body).encode() if body is not None else None, headers={"Content-Type": "application/json"})
                try:
                    with urlopen(req) as response:
                        return response.status, json.load(response)
                except HTTPError as error:
                    return error.code, json.load(error)
            try:
                choices = [asdict(Seleccion(p.id, arma="espada_basica")) for p in self.heroes]
                status, state = request("preparar", {"selecciones": choices})
                self.assertEqual(status, 200)
                self.assertEqual(len(state["party"]), 6)
                plan = {k: state["tablero"][k] for k in ("posiciones", "celdas")}
                self.assertEqual(request("campo", {"tablero": plan})[0], 200)
                self.assertEqual(request("iniciar", {"seed": 32})[0], 200)
                self.assertEqual(request("campo", {"tablero": plan})[0], 400)
                status, state = request("avanzar", {})
                self.assertEqual(status, 200)
                self.assertTrue(state["reproduccion"])
            finally:
                http.shutdown(); http.server_close(); worker.join()


if __name__ == "__main__":
    unittest.main()
