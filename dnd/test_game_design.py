"""Regresiones de las reglas completas de Game Design, sin partidas del usuario."""

import json
import math
import random
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from character import Personaje
from character_roster import CharacterRoster, serializar_personaje, deserializar_personaje
from combat_formulas import aplicar_mitigacion_dano, calcular_mitigacion_armadura, calcular_penalizaciones_peso
from combat_stats import armas_ataque, estadisticas_combate, tirar_dano
from crafting import _disenar_arma, fabricar, previsualizar_arma, crafting_data
from derived_stats import salud_por_nivel, umbral_salud, probabilidad_estado
from enemies import crear_enemigo
from equipment_balance import CALIDADES, ARMADURA_TIER, DANO_TIER, MULTIPLICADOR_ARMA, repartir_armadura, valor_calidad
from game_engine import MotorJuego
from initiative import calculateTurnOrder
from inventario import Inventario
from item_factory import item_factory
from tactical_combat import CombatResolver
from tactical_models import preparacion_ofensiva
from tactical_scenarios import crear_encuentro, crear_tablero
from weapon_effects import activar_afijo, armadura_tras_penetracion
from workshop import Workshop


class SinAzar:
    def random(self):
        return .99

    def randint(self, minimo, maximo):
        return maximo


def personaje(**stats):
    return Personaje("Prueba", "espada_basica", {**dict(fuerza=20, destreza=20, constitucion=10), **stats})


def instancia(base="dagas_hierro", **campos):
    datos = asdict(item_factory.crear(base))
    datos.update(id="craft_" + uuid4().hex, **campos)
    item_factory.registrar_instancia(datos)
    return datos


class EstadisticasTests(unittest.TestCase):
    def test_salud_por_nivel_independiente_de_constitucion(self):
        p = personaje(constitucion=1)
        p.nivel = 10
        self.assertEqual(p.calcular_salud_maxima(), 95)
        p.constitucion = 100
        self.assertEqual(p.calcular_salud_maxima(), 95)
        self.assertEqual(salud_por_nivel(20, 20, .10), 182)

    def test_hp_limites_curacion_y_no_resucitar_por_regeneracion(self):
        p = personaje()
        p.hp = -99
        self.assertEqual(p.hp, 0)
        self.assertEqual(p.regenerar(), 0)
        p.hp = 10000
        self.assertEqual(p.hp, p.salud_maxima)
        p.hp -= 3
        self.assertEqual(p.curar(10), 3)
        self.assertEqual(p.curar(-20), 0)

    def test_derivados(self):
        p = personaje(fuerza=10, destreza=11, constitucion=11)
        self.assertEqual((p.capacidad_peso, p.iniciativa, p.impacto, p.estabilidad, p.resistencia_fisica, p.regeneracion), (26, 30, 28, 30, 20, 3))
        self.assertEqual(p.precision, 70)
        self.assertEqual(p.penetracion, 15)
        self.assertEqual(p.calcular_defensa_base(), 0)

    def test_con_no_cura_al_asignar_punto(self):
        p = personaje()
        p.hp = 20
        p.puntos_estadistica = 1
        p.asignar_atributo("constitucion")
        self.assertEqual((p.hp, p.salud_maxima), (20, 50))

    def test_energia_cada_cincuenta(self):
        p = personaje()
        for nivel, energia in [(1, 3), (10, 3), (49, 3), (50, 4), (100, 5)]:
            p.nivel = nivel
            self.assertEqual(p.energia_maxima, energia)

    def test_mitigacion_cap_y_bloqueo(self):
        self.assertAlmostEqual(calcular_mitigacion_armadura(100), .5)
        self.assertAlmostEqual(calcular_mitigacion_armadura(1000), .6)
        self.assertEqual(calcular_mitigacion_armadura(-4), 0)
        self.assertEqual(aplicar_mitigacion_dano(100, .20, 100), 40)

    def test_carga_fronteras_continuas(self):
        for peso, categoria in [(50, "ligera"), (50.01, "normal"), (75, "normal"), (75.01, "pesada"), (100, "pesada"), (100.01, "sobrecargado")]:
            self.assertEqual(calcular_penalizaciones_peso(peso, 100)["categoria"], categoria)
        p = personaje(fuerza=1)
        p.inventario.recolectar("peto_hierro")
        p.inventario.equipar("peto_hierro", p)
        p.inventario.recolectar("escudo_hierro")
        p.inventario.equipar("escudo_hierro", p)
        self.assertEqual(p.penalizaciones_peso["categoria"], "sobrecargado")
        self.assertEqual(p.evasion, 0)

    def test_iniciativa_nunca_multiplica_acciones(self):
        for velocidades in [(10, 10), (1000, 1), (1, 1000)]:
            cola, restos = calculateTurnOrder(*velocidades, acumuladores={"jugador": 999, "enemigo": 999})
            self.assertCountEqual(cola, ["jugador", "enemigo"])
            self.assertEqual(restos, {"jugador": 0, "enemigo": 0})

    def test_movimiento_independiente_del_arma(self):
        p = personaje(destreza=21)
        self.assertEqual(p.movimiento, 6)  # 5 base + 1 carga ligera.
        rapido = instancia(velocidad=5, peso=0)
        p.inventario.recolectar(rapido["id"])
        anterior = p.iniciativa
        p.inventario.equipar(rapido["id"], p)
        self.assertEqual(p.iniciativa, anterior)
        self.assertEqual(p.movimiento, 6)

    def test_escalado_aplica_al_dano_completo(self):
        p = personaje(fuerza=10)
        self.assertAlmostEqual(tirar_dano(p, SinAzar()), (2 + 5) * 1.225)

    def test_umbrales_y_resistencias(self):
        self.assertEqual([umbral_salud(h, 100) for h in (76, 75, 40, 20, 0)], ["alta", "media", "baja", "critica", "derrotado"])
        self.assertAlmostEqual(probabilidad_estado(.4, 50, 50), .4)
        self.assertEqual(probabilidad_estado(.4, 0, 0), 0)
        self.assertEqual(probabilidad_estado(.4, 10, 0, inmune=True), 0)


class EquipoYGuardadoTests(unittest.TestCase):
    def test_doble_daga_exige_dos_copias_y_restaura(self):
        p = personaje()
        p.inventario.recolectar("dagas_hierro")
        p.inventario.equipar("dagas_hierro", p)
        with self.assertRaises(ValueError):
            p.inventario.equipar("dagas_hierro", p, "mano_secundaria")
        self.assertIsNone(p.inventario.secundario_equipado)
        p.inventario.recolectar("dagas_hierro")
        p.inventario.equipar("dagas_hierro", p, "mano_secundaria")
        q = deserializar_personaje(serializar_personaje(p))
        self.assertEqual(len(armas_ataque(q)), 2)

    def test_dos_manos_y_dual_validan_carga(self):
        p = personaje()
        p.inventario.recolectar("escudo_hierro")
        p.inventario.equipar("escudo_hierro", p)
        p.inventario.recolectar("maza_hierro")
        p.inventario.equipar("maza_hierro", p)
        self.assertIsNone(p.inventario.secundario_equipado)
        with self.assertRaises(ValueError):
            p.inventario.equipar("escudo_hierro", p)
        datos = p.inventario.serializar()
        datos["equipamiento"]["mano_secundaria"] = "escudo_hierro"
        with self.assertRaises(ValueError):
            Inventario.deserializar(datos)

    def test_guardado_anterior_conserva_objeto_incompatible(self):
        p = personaje()
        p.inventario.recolectar("dagas_hierro")
        datos = serializar_personaje(p)
        datos.pop("version_equipamiento")
        datos["equipamiento"]["mano_secundaria"] = "dagas_hierro"
        q = deserializar_personaje(datos)
        self.assertIsNone(q.inventario.secundario_equipado)
        self.assertEqual(q.inventario.cantidad("dagas_hierro"), 1)

    def test_legacy_tier_cinco_conserva_valores(self):
        datos = instancia(tier=5, ataque=[100, 200])
        p = personaje()
        p.inventario.recolectar(datos["id"])
        q = deserializar_personaje(serializar_personaje(p))
        self.assertEqual(item_factory.crear(datos["id"]).ataque, (100, 200))
        self.assertEqual(q.inventario.cantidad(datos["id"]), 1)

    def test_penetracion_es_por_arma(self):
        p = personaje(fuerza=10)
        a = item_factory.crear(instancia(penetracion=10)["id"])
        b = item_factory.crear(instancia(penetracion=30)["id"])
        self.assertEqual(armadura_tras_penetracion(p, 100, a), 75)
        self.assertEqual(armadura_tras_penetracion(p, 100, b), 55)

    def test_bonos_de_escudo_compartidos_con_enemigos(self):
        datos = instancia("escudo_hierro", defensa=20, bonificaciones={"estabilidad": 10})
        enemigo = crear_enemigo("Goblin", "Guerrero")
        enemigo.secundario = datos["id"]
        self.assertEqual(enemigo.defensa_total, 20)
        self.assertEqual(enemigo.estabilidad, 22)


class FabricacionTests(unittest.TestCase):
    def test_endpoint_preview_recibe_varios_componentes(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        import importlib
        with tempfile.TemporaryDirectory() as carpeta:
            with patch("config.cargar_configuracion", return_value=SimpleNamespace(data_dir=Path(carpeta))):
                servidor = importlib.import_module("server")
            roster = CharacterRoster()
            p = personaje()
            p.crafting_exp = 5
            roster.save_to_disk(p)
            with patch.object(servidor, "roster", roster):
                manejador = servidor.ManejadorDungeon.__new__(servidor.ManejadorDungeon)
                respuestas = []
                manejador._json = lambda datos, codigo=200: respuestas.append((codigo, datos))
                manejador.path = f"/api/taller/previsualizar?personaje_id={p.id}&tipo=daga&material=hierro&componente=colmillo_bestia&componente=glandula_venenosa"
                manejador._get()
                self.assertEqual(respuestas[0][0], 200)
                self.assertEqual(len(respuestas[0][1]["afijos"]), 2)

    def test_calidad_y_reparto_no_crean_armadura(self):
        self.assertEqual(valor_calidad((11, 20), "buena"), 15.95)
        for presupuesto in range(5, 121):
            self.assertEqual(sum(repartir_armadura(presupuesto).values()), presupuesto)

    def test_todas_las_variantes_respetan_caps_y_preview(self):
        for tier in range(1, 5):
            p = personaje()
            p.crafting_exp = crafting_data()["experiencia_por_tier"][tier - 1]
            for material in crafting_data()["materiales"]:
                for tipo in crafting_data()["tipos"]:
                    preview = previsualizar_arma(p, tipo, material)
                    for perfil in crafting_data()["perfiles"]:
                        for calidad in CALIDADES:
                            a = _disenar_arma(tier, tipo, material, None, perfil, calidad)
                            if "ataque" in a:
                                self.assertGreaterEqual(a["ataque"][0], 1)
                                self.assertLess(a["ataque"][0], a["ataque"][1])
                                self.assertLessEqual(a["ataque"][1], math.floor(DANO_TIER[tier][1] * MULTIPLICADOR_ARMA[tipo]))
                                self.assertLessEqual(preview["ataque"]["minimo"][0], a["ataque"][0])
                                self.assertGreaterEqual(preview["ataque"]["minimo"][1], a["ataque"][0])
                                self.assertLessEqual(preview["ataque"]["maximo"][0], a["ataque"][1])
                                self.assertGreaterEqual(preview["ataque"]["maximo"][1], a["ataque"][1])
                            if "slot" in a:
                                self.assertLessEqual(a["defensa"], repartir_armadura(ARMADURA_TIER[tier][1])[a["slot"]])
                            a["id"] = "craft_" + uuid4().hex
                            item_factory.registrar_instancia(a)

    def test_afijos_limites_recursos_y_rechazo_atomico(self):
        p = personaje()
        p.oro = 1000
        p.inventario.recolectar("material_hierro", 20)
        p.inventario.recolectar("colmillo_bestia", 1)
        p.inventario.recolectar("glandula_venenosa", 1)
        antes = serializar_personaje(p)
        with self.assertRaises(ValueError):
            fabricar(p, "daga", "hierro", ["colmillo_bestia", "glandula_venenosa"])
        self.assertEqual(serializar_personaje(p), antes)
        p.crafting_exp = 5
        a = fabricar(p, "daga", "hierro", ["colmillo_bestia", "glandula_venenosa"], random.Random(2))
        self.assertEqual(len(a["afijos"]), 2)
        self.assertEqual(p.inventario.cantidad("material_hierro"), 14)
        self.assertEqual(p.inventario.cantidad("colmillo_bestia"), 0)
        self.assertEqual(p.inventario.cantidad("glandula_venenosa"), 0)

    def test_rechaza_dano_que_supera_tier(self):
        a = _disenar_arma(1, "daga", "hierro", None, "equilibrado")
        a.update(id="craft_" + uuid4().hex, ataque=[50, 100])
        with self.assertRaises(ValueError):
            item_factory.registrar_instancia(a)

    def test_arma_fabricada_conserva_rango_y_tira_danos_distintos(self):
        p = personaje()
        p.oro = 1000
        p.inventario.recolectar("material_hierro", 10)
        a = fabricar(p, "espada", "hierro", rng=random.Random(7))
        p.inventario.equipar(a["id"], p)
        restaurado = deserializar_personaje(serializar_personaje(p))
        self.assertEqual(list(restaurado.inventario.arma_equipada.ataque), a["ataque"])

        class Extremo:
            def __init__(self, maximo):
                self.maximo = maximo

            def randint(self, minimo, maximo):
                return maximo if self.maximo else minimo

        self.assertLess(tirar_dano(restaurado, Extremo(False)), tirar_dano(restaurado, Extremo(True)))

    def test_taller_guardado_y_boveda(self):
        with tempfile.TemporaryDirectory() as carpeta:
            roster = CharacterRoster(carpeta)
            p = personaje()
            p.oro = 1000
            roster.vault.recolectar("material_hierro", 10)
            roster.save_to_disk(p, roster.vault)
            resultado = Workshop(roster).ejecutar("fabricar", p.id, tipo="daga", material="hierro")
            a = resultado["objeto_creado"]
            nuevo = CharacterRoster(carpeta)
            q = deserializar_personaje(nuevo.obtener(p.id))
            self.assertEqual(nuevo.vault.cantidad("material_hierro"), 7)
            self.assertEqual(q.inventario.cantidad(a["id"]), 1)
            self.assertEqual(item_factory.crear(a["id"]).calidad, a["calidad"])


class IntegracionCombateTests(unittest.TestCase):
    def preparar_dual(self):
        p = personaje(fuerza=1, destreza=1)
        a = instancia(ataque=[10, 10], penetracion=0)
        b = instancia(ataque=[20, 20], penetracion=100,
                      afijo={"id": "fuego", "probabilidad": 1, "dano": 3, "turnos": 1})
        for datos, slot in [(a, "mano_principal"), (b, "mano_secundaria")]:
            p.inventario.recolectar(datos["id"])
            p.inventario.equipar(datos["id"], p, slot)
        return p

    def test_dungeon_dual_dano_y_afijo_independientes(self):
        p = self.preparar_dual()
        m = MotorJuego(rng=SinAzar())
        m.jugador = p
        m.enemigo_actual = crear_enemigo("Guardián", "Jefe")
        m.enemigo_actual.calcular_defensa_base = lambda: 100
        hp = m.enemigo_actual.hp
        m._ataque_basico()
        # Principal (2+10) / 2 = 6; secundaria (2+20)*.5 = 11, penetra toda la armadura.
        self.assertEqual(hp - m.enemigo_actual.hp, 17)
        self.assertIn("fuego", m.enemigo_actual.efectos_arma)
        self.assertEqual(len([e for e in m.eventos if e["tipo"] == "dano"]), 2)

    def test_respuesta_enemiga_con_daga_secundaria_no_falla(self):
        m = MotorJuego(rng=random.Random(10))
        m.jugador = self.preparar_dual()
        m.enemigo_actual = crear_enemigo("Goblin", "Guerrero")
        m._preparar_turno_enemigo()
        m._accion_enemigo(0)
        self.assertGreaterEqual(m.jugador.hp, 0)

    def test_tactico_dual_aplica_afijo_de_secundaria(self):
        combate = CombatResolver(preparacion_ofensiva(), seed=0)
        actor = combate.party[0]
        actor.modelo = self.preparar_dual()
        combate.rng = SinAzar()
        combate.jefe.modelo.calcular_defensa_base = lambda: 100
        hp = combate.jefe.hp
        combate._accion_aliado(actor)
        self.assertEqual(hp - combate.jefe.hp, 17)
        self.assertEqual(combate.jefe.modelo.efectos_arma["fuego"]["actor_id"], actor.id)

    def test_regeneracion_por_turno_dungeon(self):
        m = MotorJuego(rng=random.Random(0))
        m.jugador = personaje(constitucion=11)
        m.jugador.hp = 20
        m.enemigo_actual = crear_enemigo("Goblin", "Guerrero")
        m.fase = "combate"
        m._preparar_turno_enemigo()
        m.actuar("defender")
        regeneraciones = [e for e in m.eventos if e["datos"].get("fuente") == "regeneracion"]
        self.assertEqual(len(regeneraciones), 1)
        self.assertEqual(regeneraciones[0]["datos"]["cantidad"], 3)

    def test_escenarios_completan_y_estados_serializan(self):
        for escenario in ("patrulla_ruinas", "guardian_patio"):
            selecciones = preparacion_ofensiva()
            encuentro = crear_encuentro(escenario)
            tablero = crear_tablero(escenario, [s.personaje_id for s in selecciones], encuentro.ids_enemigos)
            r = CombatResolver(selecciones, encuentro, seed=1234, tablero=tablero.plan()).ejecutar()
            self.assertIn(r["resultado"], {"victoria", "derrota"})
            json.dumps(r, allow_nan=False)
            self.assertLessEqual(r["rondas"], encuentro.limite_rondas)


if __name__ == "__main__":
    unittest.main()
