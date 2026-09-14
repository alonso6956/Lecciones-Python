"""Regresiones de defensa activa, desgaste por instancia y reparación transaccional."""

import json
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch

from character_roster import CharacterRoster, serializar_personaje, deserializar_personaje
from combat_formulas import aplicar_mitigacion_dano
from defense_system import resolver_defensa, durabilidad_escudo, identidad_equipada
from equipment_repair import cotizar_reparacion, reparar
from game_engine import MotorJuego
from habilidades import habilidad_factory
from inventario import Inventario
from item_container import SharedVault
from item_factory import item_factory
from tactical_combat import CombatResolver
from tactical_models import preparacion_ofensiva
from test_game_design import personaje, instancia, SinAzar
from enemies import crear_enemigo
from workshop import Workshop


def con_escudo():
    p = personaje()
    p.inventario.recolectar("escudo_hierro")
    p.inventario.equipar("escudo_hierro", p)
    return p


class DefensaTests(unittest.TestCase):
    def setUp(self):
        self.atacante = personaje()
        self.defensor = con_escudo()

    def test_pasiva_antes_armadura(self):
        r = resolver_defensa(self.atacante, self.defensor, 100)
        self.assertEqual((r["dano"], r["absorbido"], durabilidad_escudo(self.defensor)), (90, 10, 90))
        self.assertEqual(aplicar_mitigacion_dano(r["dano"], armadura=100), 45)
        self.assertFalse(r["pierde_accion"])

    def test_bloqueo_fiable_y_no_acumula_pasiva(self):
        r = resolver_defensa(self.atacante, self.defensor, 50, defendiendo=True, rng=SinAzar())
        self.assertEqual((r["dano"], r["absorbido"]), (20, 30))
        self.assertTrue(r["pierde_accion"])

    def test_rapido_solo_pasiva(self):
        r = resolver_defensa(self.atacante, self.defensor, 100, defendiendo=True, rapido=True)
        self.assertEqual(r["dano"], 90)
        self.assertFalse(r["pierde_accion"])
        self.assertFalse(r["bloqueo_activo"])

    def test_desbordamiento_y_roto_no_desaparece(self):
        inv = self.defensor.inventario
        clave = identidad_equipada(inv, "mano_secundaria")
        inv.establecer_durabilidad(clave, 5)
        r = resolver_defensa(self.atacante, self.defensor, 100, defendiendo=True)
        self.assertEqual((r["absorbido"], r["dano"]), (5, 95))
        self.assertEqual(inv.cantidad("escudo_hierro"), 1)
        r = resolver_defensa(self.atacante, self.defensor, 100, defendiendo=True)
        self.assertEqual(r["dano"], 100)
        self.assertFalse(r["pierde_accion"])

    def test_parada_compara_arma_y_rapido_la_ignora(self):
        defensor = personaje()
        grande = instancia("espada_hierro", ataque=[20, 20])
        pequena = instancia("espada_hierro", ataque=[10, 10])
        defensor.inventario.recolectar(grande["id"])
        defensor.inventario.equipar(grande["id"], defensor)
        for dano_arma, esperado, pierde in ((20, 20, True), (21, 30, False), (40, 36, False)):
            arma = instancia("espada_hierro", ataque=[dano_arma, dano_arma])
            r = resolver_defensa(self.atacante, defensor, 40, defendiendo=True, arma=item_factory.crear(arma["id"]))
            self.assertEqual((r["dano"], r["pierde_accion"]), (esperado, pierde))
        r = resolver_defensa(self.atacante, defensor, 40, defendiendo=True, rapido=True)
        self.assertEqual(r["dano"], 40)
        self.assertIsNone(r["parada"])

    def test_excepciones_no_consumen_escudo_inbloqueable(self):
        for bandera in ("inbloqueable",):
            r = resolver_defensa(self.atacante, self.defensor, 100, defendiendo=True, ataque={bandera: True})
            self.assertEqual(r["dano"], 100)
            self.assertFalse(r["pierde_accion"])
        self.assertEqual(durabilidad_escudo(self.defensor), 100)
        r = resolver_defensa(self.atacante, self.defensor, 100, defendiendo=True, ataque={"imparable": True})
        self.assertEqual(r["dano"], 90)
        self.assertFalse(r["pierde_accion"])

    def test_ruptura_resistida_y_exitosa(self):
        for azar, dano, rompe in ((.99, 40, False), (0, 90, True)):
            defensor = con_escudo()
            rng = type("Azar", (), {"random": lambda _: azar})()
            r = resolver_defensa(self.atacante, defensor, 100, defendiendo=True, ataque={"rompe_guardia": True}, rng=rng)
            self.assertEqual((r["dano"], r["ruptura"]), (dano, rompe))

    def test_copias_y_personajes_no_comparten_desgaste(self):
        inv = self.defensor.inventario
        inv.recolectar("escudo_hierro")
        resolver_defensa(self.atacante, self.defensor, 100)
        valores = [e["durabilidad_actual"] for e in inv.entradas() if e["item_id"] == "escudo_hierro"]
        self.assertEqual(valores, [90, 100])
        self.assertEqual(durabilidad_escudo(con_escudo()), 100)
        self.assertEqual(item_factory.crear("escudo_hierro").durabilidad, 100)

    def test_enemigo_pierde_exactamente_siguiente_accion(self):
        motor = MotorJuego(rng=SinAzar())
        motor.jugador = self.defensor
        motor.enemigo_actual = crear_enemigo("Goblin", "Guerrero")
        motor.enemigo_dano = 10
        motor.enemigo_habilidad = None
        motor.intencion = "normal"
        motor.is_defending = True
        with patch.object(motor, "_preparar_turno_enemigo"):
            motor._accion_enemigo(0)
            hp = motor.jugador.hp
            self.assertEqual(motor.enemigo_actual.acciones_perdidas, 1)
            motor._accion_enemigo(0)
            self.assertEqual(motor.jugador.hp, hp)
            self.assertEqual(motor.enemigo_actual.acciones_perdidas, 0)
            motor.is_defending = False
            motor._accion_enemigo(0)
            self.assertLess(motor.jugador.hp, hp)

    def test_motor_rapido_no_genera_contraataque(self):
        motor = MotorJuego(rng=SinAzar())
        motor.jugador = self.defensor
        motor.enemigo_actual = crear_enemigo("Goblin", "Guerrero")
        motor.enemigo_dano = 10
        motor.enemigo_habilidad = None
        motor.intencion = "rápido"
        motor.is_defending = True
        with patch.object(motor, "_preparar_turno_enemigo"):
            motor._accion_enemigo(0)
        self.assertEqual(durabilidad_escudo(motor.jugador), 99)
        self.assertFalse(motor.contraataque_disponible)
        self.assertEqual(motor.enemigo_actual.acciones_perdidas, 0)

    def test_tactico_pasiva_y_rapido(self):
        combate = CombatResolver(preparacion_ofensiva())
        actor, objetivo = combate.party[:2]
        objetivo.modelo = self.defensor
        objetivo.estados["defendiendo"] = {"vence": 5}
        combate.rng = SinAzar()
        with patch("tactical_combat.tirar_dano", return_value=10):
            combate._golpe(actor, objetivo, rapido=True)
        self.assertEqual(durabilidad_escudo(self.defensor), 99)
        self.assertNotIn("accion_perdida", actor.estados)

    def test_habilidades_y_combos_absorben_antes_de_armadura(self):
        for habilidad_id in ("golpe_aplastante", "hack_slash", "corte_certero"):
            with self.subTest(habilidad=habilidad_id):
                motor = MotorJuego(rng=SinAzar())
                motor.jugador = personaje()
                motor.jugador.habilidades[habilidad_id] = 1
                motor.jugador.puede_usar_habilidad = lambda _: True
                motor.enemigo_actual = crear_enemigo("Goblin", "Guerrero")
                motor.enemigo_actual.secundario = "escudo_hierro"
                motor.enemigo_actual.hp = 10000
                motor.enemigo_actual.salud_maxima = 10000
                motor.enemigo_actual.calcular_defensa_base = lambda: 100
                if habilidad_id == "hack_slash":
                    motor._resolver_ataques_multiples(habilidad_factory.crear(habilidad_id), 1)
                else:
                    motor._accion_jugador("habilidad", habilidad_id)
                desgastado = 100 - durabilidad_escudo(motor.enemigo_actual)
                if habilidad_id == "corte_certero":
                    self.assertEqual(desgastado, 0)
                else:
                    self.assertGreater(desgastado, 0)
                    absorciones = [e["datos"]["absorbido"] for e in motor.eventos if e["tipo"] == "bloqueo"]
                    self.assertAlmostEqual(sum(absorciones), desgastado)

    def test_absorcion_total_no_filtra_dano_minimo(self):
        datos = instancia("escudo_hierro", absorcion_pasiva=1)
        motor = MotorJuego(rng=SinAzar())
        motor.jugador = personaje()
        motor.enemigo_actual = crear_enemigo("Goblin", "Guerrero")
        motor.enemigo_actual.secundario = datos["id"]
        hp = motor.enemigo_actual.hp
        motor._ataque_basico()
        self.assertEqual(motor.enemigo_actual.hp, hp)
        self.assertLess(durabilidad_escudo(motor.enemigo_actual), 100)

    def test_habilidad_distribuye_bruto_sin_doble_mitigacion(self):
        motor = MotorJuego(rng=SinAzar())
        motor.jugador = personaje()
        motor.jugador.habilidades["golpe_aplastante"] = 1
        motor.jugador.puede_usar_habilidad = lambda _: True
        motor.enemigo_actual = crear_enemigo("Goblin", "Guerrero")
        motor.enemigo_actual.secundario = "escudo_hierro"
        motor.enemigo_actual.hp = 500
        with patch("game_engine.calcular_dano_habilidad", return_value=100), patch("game_engine.armadura_tras_penetracion", return_value=100):
            motor._accion_jugador("habilidad", "golpe_aplastante")
        self.assertEqual(durabilidad_escudo(motor.enemigo_actual), 90)
        self.assertEqual(motor.enemigo_actual.hp, 455)

    def test_escudo_roto_pierde_armadura_y_bonos(self):
        datos = instancia("escudo_hierro", defensa=20, bonificaciones={"estabilidad": 10})
        p = personaje()
        p.inventario.recolectar(datos["id"])
        p.inventario.equipar(datos["id"], p)
        estabilidad = p.estabilidad
        p.inventario.establecer_durabilidad(datos["id"], 0)
        self.assertEqual(p.inventario.armadura_equipo(), 0)
        self.assertEqual(p.estabilidad, estabilidad - 10)

    def test_arma_rota_no_proporciona_afijos_ni_ataque(self):
        p = personaje()
        inv = p.inventario
        original = inv.arma_equipada
        clave = identidad_equipada(inv, "mano_principal")
        inv.establecer_durabilidad(clave, 0)
        self.assertEqual(inv.arma_equipada.ataque, (0, 0))
        self.assertEqual(inv.arma_equipada.afijos, ())
        p.oro = 1000
        inv.recolectar("material_hierro", 5)
        reparar(p, clave)
        self.assertEqual(inv.arma_equipada, original)


class ReparacionTests(unittest.TestCase):
    def setUp(self):
        self.p = con_escudo()
        self.inv = self.p.inventario
        self.clave = identidad_equipada(self.inv, "mano_secundaria")
        self.inv.establecer_durabilidad(self.clave, 0)

    def test_roundtrip_y_legacy(self):
        datos = serializar_personaje(self.p)
        self.assertEqual(durabilidad_escudo(deserializar_personaje(json.loads(json.dumps(datos)))), 0)
        datos.pop("durabilidades")
        self.assertEqual(durabilidad_escudo(deserializar_personaje(datos)), 100)

    def test_vault_conserva_integridad_e_identidad(self):
        vault = SharedVault()
        self.inv.desequipar("mano_secundaria")
        vault.insertar(self.inv.extraer(self.clave))
        vault = SharedVault(vault.serializar())
        self.inv.insertar(vault.extraer(self.clave))
        self.assertEqual(self.inv.estado_durabilidad(self.clave)["durabilidad_actual"], 0)

    def test_durabilidad_invalida_rechazada(self):
        for valor in (-1, 101, float("nan"), float("inf"), True):
            datos = self.inv.serializar()
            datos["durabilidades"][self.clave] = valor
            with self.assertRaises(ValueError):
                Inventario.deserializar(datos)

    def test_reparar_consume_y_no_cambia_propiedades(self):
        self.p.oro = 1000
        vault = SharedVault()
        vault.recolectar("material_hierro", 2)
        antes = deepcopy(item_factory.crear("escudo_hierro"))
        coste = cotizar_reparacion(self.inv, self.clave)
        reparar(self.p, self.clave, vault)
        self.assertEqual(durabilidad_escudo(self.p), 100)
        self.assertEqual(self.p.oro, 1000 - coste["coste_oro"])
        self.assertEqual(vault.cantidad("material_hierro"), 1)
        self.assertEqual(item_factory.crear("escudo_hierro"), antes)
        with self.assertRaises(ValueError):
            reparar(self.p, self.clave, vault)

    def test_sin_recursos_no_muta(self):
        self.p.oro = 1000
        antes = serializar_personaje(self.p)
        with self.assertRaises(ValueError):
            reparar(self.p, self.clave)
        self.assertEqual(serializar_personaje(self.p), antes)

    def test_taller_persistencia_y_fallo_disco(self):
        with tempfile.TemporaryDirectory() as carpeta:
            roster = CharacterRoster(carpeta)
            self.p.oro = 1000
            roster.vault.recolectar("material_hierro", 2)
            roster.save_to_disk(self.p, roster.vault)
            antes = deepcopy(roster.obtener(self.p.id))
            with patch.object(roster, "save_to_disk", side_effect=OSError("disco")):
                with self.assertRaises(OSError):
                    Workshop(roster).ejecutar("reparar", self.p.id, instance_id=self.clave)
            self.assertEqual(roster.obtener(self.p.id), antes)
            self.assertEqual(roster.vault.cantidad("material_hierro"), 2)
            Workshop(roster).ejecutar("reparar", self.p.id, instance_id=self.clave)
            self.assertEqual(durabilidad_escudo(deserializar_personaje(roster.obtener(self.p.id))), 100)

    def test_endpoint_reparar_prohibido_durante_ambos_combates(self):
        from types import SimpleNamespace
        from pathlib import Path
        import importlib
        with tempfile.TemporaryDirectory() as carpeta:
            with patch("config.cargar_configuracion", return_value=SimpleNamespace(data_dir=Path(carpeta))):
                servidor = importlib.import_module("server")
            for dungeon, tactico in (("combate", "preparacion"), ("menu", "combate")):
                with patch.object(servidor.motor, "fase", dungeon), patch.object(servidor.prototipo, "fase", tactico), patch.object(Workshop, "ejecutar") as ejecutar:
                    manejador = servidor.ManejadorDungeon.__new__(servidor.ManejadorDungeon)
                    manejador.path = "/api/taller/reparar"
                    manejador._estado = lambda: {}
                    manejador._leer_json = lambda: {"personaje_id": self.p.id, "instance_id": self.clave}
                    respuestas = []
                    manejador._json = lambda datos, codigo=200: respuestas.append((codigo, datos))
                    manejador._post()
                    self.assertEqual(respuestas[0][0], 400)
                    ejecutar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
