"""Fabricación, venta y persistencia; todos los guardados son temporales."""

import json
import random
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from character import Personaje
from character_roster import CharacterRoster, deserializar_personaje
from crafting import crafting_data, fabricar, generar_arma, previsualizar_arma
from economy import coste_fabricacion, precio_venta, valor_fabricacion
from item import Arma, Armadura, Secundario
from item_factory import item_factory
from shop import Shop
from workshop import Workshop


class CraftingEconomyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.roster = CharacterRoster(self.temp.name)
        self.p = Personaje("Forjadora", "espada_basica", dict(fuerza=5, destreza=5, constitucion=5))
        self.p.oro = 1000
        self.roster.save_to_disk(self.p)
        self.workshop = Workshop(self.roster)
        self.shop = Shop(self.roster)

    def saved(self):
        return deserializar_personaje(self.roster.obtener(self.p.id))

    def snapshot(self):
        return self.roster.personajes, self.roster.vault.serializar()

    def supply(self, local=0, vault=3):
        if local:
            self.p.inventario.recolectar("material_hierro", local)
        if vault:
            self.roster.vault.recolectar("material_hierro", vault)
        self.roster.save_to_disk(self.p)

    def craft(self, tipo="espada", **extra):
        return self.workshop.ejecutar("fabricar", self.p.id, tipo=tipo, material="hierro", **extra)["objeto_creado"]

    def test_mixed_sources_component_and_reload(self):
        self.supply(local=1, vault=5)
        self.roster.vault.recolectar("glandula_venenosa")
        self.roster.save_to_disk(self.p)
        before = self.snapshot()
        preview = self.workshop.previsualizar(self.p.id, "espada", "hierro", "glandula_venenosa")
        self.assertEqual((preview["recursos"][0]["inventario"], preview["recursos"][0]["vault"]), (1, 5))
        self.assertEqual(self.snapshot(), before)
        arma = self.craft(componente="glandula_venenosa")
        self.assertEqual(self.saved().oro, 925)
        self.assertEqual(self.saved().crafting_exp, 1)
        self.assertEqual(self.saved().inventario.cantidad("material_hierro"), 0)
        self.assertEqual(self.roster.vault.cantidad("material_hierro"), 3)
        self.assertEqual(self.roster.vault.cantidad("glandula_venenosa"), 0)
        loaded = CharacterRoster(self.temp.name)
        self.assertEqual(loaded.personajes, self.roster.personajes)
        self.assertEqual(loaded.vault.serializar(), self.roster.vault.serializar())
        self.assertEqual(self.saved().inventario._custom[arma["id"]]["precio"], 50)

    def test_vault_only_and_inventory_first(self):
        for local, vault, remaining in [(0, 3, 0), (3, 3, 3), (6, 3, 3)]:
            with self.subTest(local=local):
                p = deepcopy(self.p)
                from item_container import SharedVault
                v = SharedVault()
                if local:
                    p.inventario.recolectar("material_hierro", local)
                v.recolectar("material_hierro", vault)
                fabricar(p, "espada", "hierro", vault=v)
                self.assertEqual(v.cantidad("material_hierro"), remaining)
                self.assertEqual(p.inventario.cantidad("material_hierro"), max(0, local - 3))

    def test_capacity_counts_only_freed_inventory_stacks(self):
        self.p.inventario.capacidad = 1
        self.supply(vault=3)
        self.assertFalse(self.workshop.previsualizar(self.p.id, "espada", "hierro")["espacio_disponible"])
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.craft()
        self.assertEqual(self.snapshot(), before)
        self.p.inventario.capacidad = 2
        self.supply(local=1, vault=0)
        self.assertTrue(self.workshop.previsualizar(self.p.id, "espada", "hierro")["puede_fabricar"])
        self.craft()
        self.assertEqual(self.saved().inventario.slots_ocupados, 2)

    def test_no_resources_or_gold_never_mutates(self):
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.craft()
        self.assertEqual(self.snapshot(), before)
        self.p.oro = 74
        self.supply()
        before = self.snapshot()
        self.assertFalse(self.workshop.previsualizar(self.p.id, "espada", "hierro")["puede_fabricar"])
        with self.assertRaises(ValueError):
            self.craft()
        self.assertEqual(self.snapshot(), before)

    def test_craft_disk_failure_keeps_gold_inventory_vault_and_xp(self):
        self.supply(local=1)
        before = self.snapshot()
        with patch.object(self.roster.archivo, "guardar", side_effect=OSError("disk")):
            with self.assertRaises(OSError):
                self.craft()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(CharacterRoster(self.temp.name).personajes, before[0])

    def test_all_recipes_tiers_materials_profiles_and_prices(self):
        from dataclasses import asdict
        data = crafting_data()
        for exp in data["experiencia_por_tier"]:
            self.p.crafting_exp = exp
            for tipo, recipe in data["tipos"].items():
                for material in data["materiales"]:
                    preview = previsualizar_arma(self.p, tipo, material)
                    for profile in data["perfiles"]:
                        with self.subTest(tier=self.p.crafting_tier, tipo=tipo, material=material, profile=profile):
                            rng = unittest.mock.Mock()
                            rng.choice.return_value = profile
                            result = generar_arma(self.p, tipo, material, rng=rng)
                            item = item_factory.registrar_instancia(result)
                            for key, bounds in preview["rangos"].items():
                                self.assertLessEqual(bounds[0], result[key])
                                self.assertGreaterEqual(bounds[1], result[key])
                            self.assertGreater(preview["coste_oro"], result["precio"])
                            self.assertGreater(result["precio"], precio_venta(item))
                            self.assertEqual(preview["precio_venta"], precio_venta(item))
                            self.assertEqual(asdict(item_factory.crear(item.id)), asdict(item))
                            if isinstance(item, Armadura):
                                self.assertGreater(item.defensa, item_factory.crear(recipe["base"]).defensa)
                            if isinstance(item, Secundario):
                                self.assertGreater(item.probabilidad_bloqueo, .15)

    def test_offensive_components_not_consumed_for_armor(self):
        self.supply()
        self.roster.vault.recolectar("glandula_venenosa")
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.craft("casco", componente="glandula_venenosa")
        self.assertEqual(self.snapshot(), before)

    def test_protections_equip_rename_transfer_reload_and_tactical(self):
        from tactical_models import ARMAS, BuildManager, Seleccion
        self.supply(vault=60)
        crafted = [self.craft(t) for t in ("casco", "peto", "brazales", "grebas", "escudo")]
        for item in crafted:
            self.workshop.ejecutar("equipar", self.p.id, item_id=item["id"])
        self.assertGreater(self.saved().inventario.armadura_equipo(), 17)
        self.assertIsInstance(self.saved().inventario.secundario_equipado, Secundario)
        other = []
        for name in ("B", "C"):
            p = Personaje(name, "espada_basica", dict(fuerza=5, destreza=5, constitucion=5))
            self.roster.save_to_disk(p)
            other.append(p)
        party = BuildManager.crear_party([Seleccion(p.id, arma="espada_basica") for p in [self.p, *other]], self.roster.personajes)
        self.assertEqual(party[0].modelo.inventario.armadura_equipo(), self.saved().inventario.armadura_equipo())
        self.assertFalse(any(i["id"] in ARMAS for i in crafted))
        casco = crafted[0]
        self.workshop.ejecutar("desequipar", self.p.id, slot="casco")
        self.workshop.ejecutar("nombrar", self.p.id, item_id=casco["id"], nombre="El guardián")
        self.workshop.ejecutar("depositar", self.p.id, instance_id=casco["id"])
        self.workshop.ejecutar("retirar", other[0].id, instance_id=casco["id"])
        loaded = CharacterRoster(self.temp.name)
        restored = deserializar_personaje(loaded.obtener(other[0].id))
        self.assertEqual(restored.inventario._custom[casco["id"]]["nombre"], "El guardián")
        self.assertEqual(restored.inventario._custom[casco["id"]]["precio"], casco["precio"])
        Shop(loaded).vender(other[0].id, casco["id"])
        self.assertEqual(loaded.obtener(other[0].id)["oro"], casco["precio"] // 2)

    def test_craft_sale_loses_gold_and_cannot_be_replayed(self):
        self.supply()
        arma = self.craft()
        self.shop.vender(self.p.id, arma["id"])
        self.assertEqual(self.saved().oro, 950)
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.shop.vender(self.p.id, arma["id"])
        self.assertEqual(self.snapshot(), before)

    def test_sale_duplicate_equipped_item_and_free_starter(self):
        self.p.inventario.recolectar("casco_hierro", 2)
        self.p.inventario.equipar("casco_hierro", self.p)
        self.p.inventario.recolectar("espada_hierro")
        self.p.inventario.equipar("espada_hierro", self.p)
        self.roster.save_to_disk(self.p)
        entries = self.shop.estado(self.p.id)["ventas"]
        helmets = [e for e in entries if e["item_id"] == "casco_hierro"]
        equipped = next(e for e in helmets if e["equipado"])
        spare = next(e for e in helmets if not e["equipado"])
        with self.assertRaises(ValueError):
            self.shop.vender(self.p.id, equipped["instance_id"])
        free = next(e for e in entries if e["item_id"] == "espada_basica")
        self.assertFalse(free["vendible"])
        with self.assertRaises(ValueError):
            self.shop.vender(self.p.id, free["instance_id"])
        self.shop.vender(self.p.id, spare["instance_id"])
        self.assertEqual(self.saved().inventario.cantidad("casco_hierro"), 1)
        self.assertEqual(self.saved().inventario.item_en_slot("casco").id, "casco_hierro")

    def test_sale_stack_invalid_amount_and_disk_failure(self):
        self.p.inventario.recolectar("pocion_mediana", 3)
        self.roster.save_to_disk(self.p)
        before = self.snapshot()
        for quantity in (0, -1, True, 1.5, "1", 4, 1000):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                self.shop.vender(self.p.id, "pocion_mediana", quantity)
            self.assertEqual(self.snapshot(), before)
        with patch.object(self.roster.archivo, "guardar", side_effect=OSError("disk")):
            with self.assertRaises(OSError):
                self.shop.vender(self.p.id, "pocion_mediana")
        self.assertEqual(self.snapshot(), before)
        self.shop.vender(self.p.id, "pocion_mediana", 2)
        self.assertEqual(self.saved().inventario.cantidad("pocion_mediana"), 1)
        self.assertEqual(self.saved().oro, 1000 + 2 * precio_venta(item_factory.crear("pocion_mediana")))

    def test_concurrent_crafts_share_one_pool(self):
        self.supply()
        second = Personaje("Otro", "espada_basica", dict(fuerza=5, destreza=5, constitucion=5))
        second.oro = 1000
        self.roster.save_to_disk(second)
        def craft(pid):
            try:
                Workshop(self.roster).ejecutar("fabricar", pid, tipo="espada", material="hierro")
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(craft, [self.p.id, second.id]))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(self.roster.vault.cantidad("material_hierro"), 0)
        self.assertEqual(sum(p["oro"] for p in self.roster.personajes), 1925)

    def test_legacy_weapon_remains_loadable(self):
        legacy = generar_arma(self.p, "espada", "hierro", rng=random.Random(1))
        legacy["precio"] = 0
        item_factory.registrar_instancia(legacy)
        self.p.inventario.recolectar(legacy["id"])
        self.roster.save_to_disk(self.p)
        restored = deserializar_personaje(CharacterRoster(self.temp.name).obtener(self.p.id))
        self.assertEqual(restored.inventario.cantidad(legacy["id"]), 1)

    def test_page_scripts(self):
        import shutil
        import subprocess
        from pathlib import Path
        if not shutil.which("node"):
            self.skipTest("Node.js is required for page script checks")
        self.supply()
        self.p.inventario.recolectar("pocion_mediana", 2)
        self.roster.save_to_disk(self.p)
        for name in ("Dos", "Tres"):
            self.roster.save_to_disk(Personaje(name, "espada_basica", dict(fuerza=5, destreza=5, constitucion=5)))
        from game_engine import MotorJuego
        from tactical_controller import PrototypeController
        import re
        version = re.search(r'UI_VERSION = "([^"]+)"', Path("server.py").read_text(encoding="utf-8"))[1]
        fixture = {"workshop": {**self.workshop.estado(self.p.id), "disponible": True},
                   "main": {**MotorJuego(roster=self.roster).estado(), "ui_version": version,
                            "slots": self.roster.listar_slots(), "guardado_disponible": True,
                            "tactico_disponible": self.roster.tactico_disponible, "slot_activo": None},
                   "tactical": PrototypeController(roster=self.roster).estado(),
                   "shop": {**self.shop.estado(self.p.id), "disponible": True},
                   "empty": {**Workshop(CharacterRoster()).estado(), "disponible": True},
                   "previews": {t: self.workshop.previsualizar(self.p.id, t, "hierro") for t in crafting_data()["tipos"]}}
        from tactical_models import Seleccion
        from dataclasses import asdict
        for name in ("Cuatro", "Cinco", "Seis"):
            self.roster.save_to_disk(Personaje(name, "espada_basica", dict(fuerza=5, destreza=5, constitucion=5)))
        tactical = PrototypeController(roster=self.roster)
        fixture["tacticalSix"] = tactical.preparar([asdict(Seleccion(p["id"], arma=p["arma_equipada"])) for p in self.roster.personajes])
        tactical.iniciar(42)
        fixture["tacticalFrame"] = tactical.avanzar()
        path = Path(self.temp.name) / "pages.json"
        path.write_text(json.dumps(fixture), encoding="utf-8")
        result = subprocess.run(["node", "test_workshop_pages.cjs", str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_http_craft_sale_blocking_and_separate_pages(self):
        import config
        from pathlib import Path
        with patch("config.cargar_configuracion", return_value=replace(config.cargar_configuracion(), data_dir=Path(self.temp.name))):
            import server
        self.supply(vault=20)
        from game_engine import MotorJuego
        from tactical_controller import PrototypeController
        with patch.multiple(server, roster=self.roster, motor=MotorJuego(roster=self.roster), prototipo=PrototypeController(roster=self.roster)):
            httpd = server.ServidorDungeon(("127.0.0.1", 0), server.ManejadorDungeon)
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                def request(path, data=None):
                    req = Request(f"http://127.0.0.1:{httpd.server_port}{path}", data=json.dumps(data).encode() if data is not None else None, headers={"Content-Type": "application/json"})
                    try:
                        with urlopen(req) as response:
                            return response.status, response.read().decode()
                    except HTTPError as error:
                        return error.code, error.read().decode()
                for page in ("workshop", "vault", "shop"):
                    status, text = request(f"/{page}.html")
                    self.assertEqual(status, 200)
                    if page == "vault":
                        self.assertNotIn('id="craftFields"', text)
                    if page == "workshop":
                        self.assertNotIn('id="vaultPanel"', text)
                status, text = request("/api/taller/fabricar", {"personaje_id": self.p.id, "tipo": "escudo", "material": "hierro"})
                self.assertEqual(status, 200, text)
                item = json.loads(text)["objeto_creado"]
                sale = {"personaje_id": self.p.id, "instance_id": item["id"]}
                before = self.snapshot()
                self.assertEqual(request("/api/tienda/vender", {**sale, "precio": 99999})[0], 400)
                server.motor.fase = "combate"
                self.assertEqual(request("/api/tienda/vender", sale)[0], 400)
                server.motor.fase = "menu"
                server.prototipo.fase = "combate"
                self.assertEqual(request("/api/tienda/vender", sale)[0], 400)
                self.assertEqual(self.snapshot(), before)
                server.prototipo.fase = "preparacion"
                self.assertEqual(request("/api/tienda/vender", sale)[0], 200)
            finally:
                httpd.shutdown()
                httpd.server_close()
                thread.join()


if __name__ == "__main__":
    unittest.main()
