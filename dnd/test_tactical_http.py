"""Aceptación a través del servidor real, en puerto efímero y sin guardar partidas."""

import json
import random
import threading
import unittest
from tempfile import TemporaryDirectory
from dataclasses import asdict, replace
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener
from unittest.mock import patch

import server
from game_engine import MotorJuego
from character_roster import CharacterRoster
from tactical_controller import PrototypeController
from tactical_models import preparacion_adaptada


class TacticalHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.roster = CharacterRoster(self.temp.name)
        self.motor = MotorJuego(random.Random(1234), self.roster)
        self.patches = [patch.object(server, "motor", self.motor),
                        patch.object(server, "roster", self.roster),
                        patch.object(server, "prototipo", PrototypeController(roster=self.roster)),
                        patch.object(server, "configuracion", replace(server.configuracion, request_logging=False))]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.http = server.ServidorDungeon(("127.0.0.1", 0), server.ManejadorDungeon)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:" + str(self.http.server_port)
        self.opener = build_opener(ProxyHandler({}))

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(timeout=5)

    def request(self, path, data=None, expected=200):
        body = None if data is None else json.dumps(data).encode()
        req = Request(self.base + path, data=body, headers={"Content-Type": "application/json"})
        try:
            response = self.opener.open(req, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            self.assertEqual(response.status, expected)
            content = response.read()
            return json.loads(content) if path.startswith("/api/") else content

    def test_preview_y_deposito_masivo_http(self):
        from character import Personaje
        p = Personaje("Forjador", "espada_basica", {"fuerza": 10, "destreza": 10, "constitucion": 10})
        p.inventario.recolectar("material_hierro", 6)
        self.roster.save_to_disk(p)
        url = f"/api/taller/previsualizar?personaje_id={p.id}&tipo=espada&material=hierro"
        self.assertTrue(self.request(url)["puede_fabricar"])
        self.request(url.replace("hierro", "invalido"), expected=400)
        self.request("/api/taller/previsualizar", expected=400)
        estado = self.request("/api/taller/estado?personaje_id=" + p.id)
        self.assertEqual(estado["progreso"]["porcentaje"], 0)
        self.assertTrue(all("detalles" in i and "transferible" in i for i in estado["inventario"]))
        self.assertIn(b"workshop-rpg.css", self.request("/workshop.html"))
        self.assertIn(b".inventory-grid", self.request("/workshop-rpg.css"))
        self.request("/api/taller/depositar_materiales", {"personaje_id": p.id})
        self.assertFalse(self.request(url)["puede_fabricar"])
        self.request("/api/taller/retirar", {"personaje_id": p.id, "instance_id": "material_hierro", "cantidad": 6})
        self.assertTrue(self.request(url)["puede_fabricar"])
        self.motor.cargar_personaje(p.id)
        self.request("/api/taller/depositar_todo", {"personaje_id": p.id}, expected=400)

    def test_ciclo_http_roster_y_reintento(self):
        self.assertIn(b"tacticalButton", self.request("/"))
        self.assertIn(b"tactical.js", self.request("/tactical.html"))
        self.assertIn(b"changeSelection", self.request("/tactical.js"))
        self.assertIn(b"party-grid", self.request("/tactical.css"))
        self.request("/api/tactico/iniciar", {"seed": 1235}, expected=400)
        for nombre in ("Uno", "Dos", "Tres"):
            self.request("/api/nueva", {})
            self.request("/api/iniciar", {"nombre": nombre})
            self.request("/api/reiniciar", {})
        roster_antes = self.roster.personajes
        self.assertTrue(self.request("/api/estado")["tactico_disponible"])
        estado = self.request("/api/tactico/iniciar", {"seed": 1235})
        inicial = estado["combate"]
        self.assertEqual([a["nombre"] for a in inicial["party"]], ["Uno", "Dos", "Tres"])
        self.request("/api/tactico/reajustar", {}, expected=400)
        while estado["fase"] == "combate":
            estado = self.request("/api/tactico/avanzar", {})
        self.assertEqual(estado["resultado"]["resultado"], "derrota")
        self.request("/api/tactico/reajustar", {})
        estado = self.request("/api/tactico/iniciar", {"seed": 1235})
        self.assertEqual(estado["eventos"], [])
        self.assertEqual(estado["combate"], inicial)
        while estado["fase"] == "combate":
            estado = self.request("/api/tactico/avanzar", {})
        self.assertEqual(self.roster.personajes, roster_antes)
        self.assertEqual(self.request("/api/estado")["fase"], "menu")

    def test_descartar_confirmado_actualiza_roster_y_bloqueo_tactico(self):
        for nombre in ("Uno", "Dos", "Tres"):
            self.request("/api/nueva", {})
            estado = self.request("/api/iniciar", {"nombre": nombre})
            personaje_id = estado["jugador"]["id"]
            self.request("/api/descartar", {"id": personaje_id, "confirmado": True}, expected=400)
            self.request("/api/reiniciar", {})
        self.assertTrue(self.request("/api/tactico/estado")["tactico_disponible"])
        self.request("/api/descartar", {"id": personaje_id}, expected=400)
        self.request("/api/descartar", {"id": "no-existe", "confirmado": True}, expected=400)
        self.request("/api/tactico/iniciar", {})
        self.request("/api/descartar", {"id": personaje_id, "confirmado": True}, expected=400)
        while server.prototipo.fase == "combate":
            self.request("/api/tactico/avanzar", {})
        estado = self.request("/api/descartar", {"id": personaje_id, "confirmado": True})
        self.assertEqual([p["nombre"] for p in estado["roster"]], ["Uno", "Dos"])
        self.assertFalse(estado["tactico_disponible"])
        tactico = self.request("/api/tactico/estado")
        self.assertEqual(tactico["selecciones"], [])
        self.assertIsNone(tactico["combate"])
        self.assertEqual(len(CharacterRoster(self.temp.name).personajes), 2)
        self.request("/api/cargar", {"id": personaje_id}, expected=400)

    def test_api_rechaza_datos_invalidos(self):
        for data in ([], {"seed": "x"}, {"seed": True}, {"seed": -1}, {"seed": 2**32}):
            self.request("/api/tactico/iniciar", data, expected=400)
        for data in ({}, {"selecciones": [None] * 3}, {"selecciones": [{}] * 3}):
            self.request("/api/tactico/preparar", data, expected=400)
        self.request("/api/tactico/desconocido", {}, expected=404)
        self.assertEqual(self.request("/api/tactico/estado")["fase"], "preparacion")

    def test_taller_http_fabrica_transfiere_y_equipa_con_otro_personaje(self):
        from character_roster import deserializar_personaje
        ids = []
        for nombre in ("Herrero", "Viajero", "Tercero"):
            self.request("/api/nueva", {})
            estado = self.request("/api/iniciar", {"nombre": nombre})
            ids.append(estado["jugador"]["id"])
            self.request("/api/reiniciar", {})
        jugador = deserializar_personaje(self.roster.obtener(ids[0]))
        jugador.inventario.recolectar("material_acero", 3)
        self.roster.save_to_disk(jugador)
        self.assertIn(b"workshop.js", self.request("/workshop.html"))
        self.assertTrue(self.request("/api/taller/estado")["disponible"])
        estado = self.request("/api/taller/fabricar", {"personaje_id": ids[0], "tipo": "lanza", "material": "acero"})
        arma = estado["arma_creada"]
        self.request("/api/taller/nombrar", {"personaje_id": ids[0], "item_id": arma["id"], "nombre": "Aurora"})
        self.request("/api/taller/depositar", {"personaje_id": ids[0], "instance_id": arma["id"]})
        self.request("/api/taller/retirar", {"personaje_id": ids[1], "instance_id": arma["id"]})
        self.request("/api/taller/equipar", {"personaje_id": ids[1], "item_id": arma["id"]})
        tactico = self.request("/api/tactico/estado")
        heroe = next(p for p in tactico["party"] if p["id"] == ids[1])
        self.assertEqual(heroe["arma"], "Aurora")
        estado = self.request("/api/cargar", {"id": ids[1]})
        self.assertEqual(estado["jugador"]["arma"], "Aurora")
        self.assertFalse(self.request("/api/taller/estado")["disponible"])
        self.request("/api/taller/depositar", {"personaje_id": ids[1], "instance_id": arma["id"]}, expected=400)
        self.request("/api/reiniciar", {})
        self.request("/api/tactico/iniciar", {})
        self.request("/api/taller/fabricar", {"personaje_id": ids[0], "tipo": "lanza", "material": "acero"}, expected=400)

    def test_taller_http_rechaza_payloads_sin_mutar(self):
        self.request("/api/nueva", {})
        estado = self.request("/api/iniciar", {"nombre": "Validación"})
        personaje_id = estado["jugador"]["id"]
        self.request("/api/reiniciar", {})
        antes = self.roster.personajes
        for payload in ({}, {"personaje_id": personaje_id, "tipo": [], "material": "hierro"},
                        {"personaje_id": personaje_id, "tipo": "espada", "material": "inexistente"}):
            self.request("/api/taller/fabricar", payload, expected=400)
        self.request("/api/taller/retirar", {"personaje_id": personaje_id, "instance_id": "material_hierro", "cantidad": True}, expected=400)
        self.request("/api/taller/estado?personaje_id=inexistente", expected=400)
        self.assertEqual(self.roster.personajes, antes)

    def test_tienda_http_personaje_cantidad_y_bloqueo_tactico(self):
        from character_roster import deserializar_personaje
        ids = []
        for nombre in ("Comprador", "Aliado", "Tercero"):
            self.request("/api/nueva", {})
            estado = self.request("/api/iniciar", {"nombre": nombre})
            ids.append(estado["jugador"]["id"])
            self.request("/api/reiniciar", {})
        p = deserializar_personaje(self.roster.obtener(ids[0]))
        p.oro = 100
        self.roster.save_to_disk(p)
        self.assertIn(b"shop.html", self.request("/"))
        self.assertIn(b"shop.js", self.request("/shop.html"))
        self.request("/api/tienda/comprar", {"categoria": "pociones", "nombre": "Pocion mediana"}, expected=400)
        compra = {"personaje_id": ids[0], "categoria": "pociones", "nombre": "Pocion mediana", "cantidad": 2}
        estado = self.request("/api/tienda/comprar", compra)
        self.assertEqual(estado["oro"], 60)
        self.assertEqual(self.roster.obtener(ids[1])["oro"], 0)
        self.request("/api/tactico/iniciar", {})
        self.assertFalse(self.request("/api/tienda/estado")["disponible"])
        for ruta in ("/api/comprar", "/api/tienda/comprar"):
            self.request(ruta, compra, expected=400)
        self.assertEqual(self.roster.obtener(ids[0])["oro"], 60)

    def test_regresion_combate_original_por_http(self):
        pagina = self.request("/")
        self.assertIn(b"characterButton", pagina)
        self.assertNotIn(b'id="skillsButton"', pagina)
        self.assertIn(b"combat-inventory.js?v=23", pagina)
        self.assertIn(b"character-panel.js?v=23", pagina)
        self.assertIn(b"seleccionarPestanaPersonaje", self.request("/character-panel.js"))
        self.assertIn(b".character-tabs", self.request("/character-panel.css"))
        self.assertIn(b"management-layout", self.request("/combat-inventory.css"))
        self.assertIn(b"ejecutarGestion", self.request("/combat-inventory.js"))
        self.request("/api/nueva", {})
        estado = self.request("/api/iniciar", {"nombre": "Baseline", "arma": "Espada de hierro"})
        self.assertEqual(estado["jugador"]["chispa_nivel_desbloqueo"], 30)
        pasos = 0
        while estado["fase"] == "combate" and pasos < 300:
            estado = self.request("/api/accion", {"accion": "atacar"})
            pasos += 1
        self.assertIn(estado["fase"], ("transicion", "nivel", "menu"))
        self.assertGreater(pasos, 0)
        self.assertEqual(len(self.roster.personajes), 1)
        self.assertEqual(self.roster.personajes[0]["arma_equipada"], "espada_basica")
        self.assertEqual(self.request("/api/tactico/estado")["fase"], "preparacion")

    def test_comprar_desde_menu_guarda_y_dungeon_no_permite_compras(self):
        self.request("/api/nueva", {})
        estado = self.request("/api/iniciar", {"nombre": "Tienda"})
        id_personaje = estado["jugador"]["id"]
        archivo = self.roster.archivo.directorio / "roster.json"
        inicial = archivo.read_bytes()
        self.request("/api/guardar", {"slot": 1}, expected=400)
        self.request("/api/cargar", {"slot": 1}, expected=400)
        self.motor.jugador.oro = 100
        self.motor.fase = "transicion"
        self.request("/api/continuar", {})
        self.request("/api/reiniciar", {})
        tienda = self.request("/api/tienda/estado?personaje_id=" + id_personaje)
        self.assertTrue(tienda["disponible"])
        self.assertEqual(tienda["oro"], 100)
        tienda = self.request("/api/comprar", {"personaje_id": id_personaje, "categoria": "armas", "nombre": "Maza de hierro"})
        self.assertEqual(tienda["oro"], 50)
        checkpoint = archivo.read_bytes()
        self.assertNotEqual(checkpoint, inicial)
        self.request("/api/cargar", {"id": id_personaje})
        self.assertFalse(self.request("/api/tienda/estado")["disponible"])
        for endpoint in ("/api/comprar", "/api/tienda/comprar"):
            self.request(endpoint, {"personaje_id": id_personaje, "categoria": "pociones", "nombre": "Pocion mediana"}, expected=400)
        self.motor.jugador.oro += 500
        self.request("/api/reiniciar", {})
        self.assertEqual(archivo.read_bytes(), checkpoint)
        estado = self.request("/api/cargar", {"id": id_personaje})
        self.assertEqual(estado["habitacion"], 1)
        self.assertEqual(estado["jugador"]["oro"], 50)
        self.assertEqual(estado["jugador"]["arma"], "Maza de hierro")
        self.assertEqual(estado["jugador"]["hp"], estado["jugador"]["salud_maxima"])

    def test_muerte_http_conserva_recompensas_posteriores_a_tienda(self):
        self.request("/api/nueva", {})
        estado = self.request("/api/iniciar", {"nombre": "Persistente"})
        personaje_id = estado["jugador"]["id"]
        self.motor.jugador.exp = 10
        self.motor.jugador.oro = 15
        self.motor.fase = "transicion"
        self.request("/api/continuar", {})
        self.motor.jugador.ganar_exp(12)
        self.motor.jugador.oro += 17
        self.motor._iniciar_combate()
        self.motor.jugador.hp = 0
        estado = self.request("/api/accion", {"accion": "atacar"})
        self.assertEqual(estado["fase"], "menu")
        self.assertEqual(estado["roster"][0]["exp"], 22)
        self.assertEqual(estado["roster"][0]["oro"], 32)
        disco = CharacterRoster(self.temp.name).obtener(personaje_id)
        self.assertEqual(disco["exp"], 22)
        self.assertEqual(disco["oro"], 32)
        estado = self.request("/api/cargar", {"id": personaje_id})
        self.assertEqual(estado["jugador"]["exp"], 22)
        self.assertEqual(estado["jugador"]["oro"], 32)
        self.assertEqual(estado["habitacion"], 1)


if __name__ == "__main__":
    unittest.main()
