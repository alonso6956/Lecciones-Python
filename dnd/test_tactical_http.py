"""Aceptación a través del servidor real, en puerto efímero y sin guardar partidas."""

import json
import random
import threading
import unittest
from dataclasses import asdict, replace
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener
from unittest.mock import patch

import server
from game_engine import MotorJuego
from tactical_controller import PrototypeController
from tactical_models import preparacion_adaptada


class TacticalHTTPTests(unittest.TestCase):
    def setUp(self):
        self.patches = [patch.object(server, "motor", MotorJuego(random.Random(1234))),
                        patch.object(server, "prototipo", PrototypeController()),
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

    def test_ciclo_http_completo_derrota_reajuste_victoria(self):
        self.assertIn(b"tactical.html", self.request("/"))
        self.assertIn(b"tactical.js", self.request("/tactical.html"))
        self.assertIn(b"changeSelection", self.request("/tactical.js"))
        self.assertIn(b"party-grid", self.request("/tactical.css"))
        estado = self.request("/api/tactico/iniciar", {"seed": 1235})
        self.request("/api/tactico/reajustar", {}, expected=400)
        while estado["fase"] == "combate":
            estado = self.request("/api/tactico/avanzar", {})
        self.assertEqual(estado["resultado"]["resultado"], "derrota")
        self.assertEqual(estado["resultado"]["diagnostico"]["causa"], "sangrado")
        self.request("/api/tactico/reajustar", {})
        self.request("/api/tactico/preparar", {"selecciones": [asdict(s) for s in preparacion_adaptada()]})
        estado = self.request("/api/tactico/iniciar", {"seed": 1235})
        self.assertEqual(estado["eventos"], [])
        while estado["fase"] == "combate":
            estado = self.request("/api/tactico/avanzar", {})
        self.assertEqual(estado["resultado"]["resultado"], "victoria")
        self.assertEqual(self.request("/api/estado")["fase"], "menu")

    def test_api_rechaza_datos_invalidos(self):
        for data in ([], {"seed": "x"}, {"seed": True}, {"seed": -1}, {"seed": 2**32}):
            self.request("/api/tactico/iniciar", data, expected=400)
        for data in ({}, {"selecciones": [None] * 3}, {"selecciones": [{}] * 3}):
            self.request("/api/tactico/preparar", data, expected=400)
        self.request("/api/tactico/desconocido", {}, expected=404)
        self.assertEqual(self.request("/api/tactico/estado")["fase"], "preparacion")

    def test_regresion_combate_original_por_http(self):
        self.request("/api/nueva", {})
        estado = self.request("/api/iniciar", {"nombre": "Baseline", "arma": "Espada de hierro"})
        pasos = 0
        while estado["fase"] == "combate" and pasos < 300:
            estado = self.request("/api/accion", {"accion": "atacar"})
            pasos += 1
        self.assertEqual(estado["fase"], "transicion")
        self.assertEqual(pasos, 6)
        self.assertEqual(self.request("/api/tactico/estado")["fase"], "preparacion")


if __name__ == "__main__":
    unittest.main()
