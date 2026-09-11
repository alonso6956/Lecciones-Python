"""Integración y atomicidad de crafteo, equipo procedural y vault compartido."""

from copy import deepcopy
from dataclasses import asdict
import random
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch, Mock

from character import Personaje
from character_roster import CharacterRoster, deserializar_personaje, serializar_personaje
from crafting import crafting_data, generar_arma, fabricar, botin_crafteo, previsualizar_arma, progreso_crafteo
from game_engine import MotorJuego
from item_container import SharedVault
from item_factory import item_factory
from persistence import ErrorGuardado
from tactical_models import BuildManager, Seleccion
from tactical_combat import CombatResolver
from weapon_effects import activar_afijo, ticks_afijos, armadura_tras_penetracion
from workshop import Workshop


class WorkshopTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.roster = CharacterRoster(self.temp.name)
        self.a = Personaje("Artesano", "espada_basica", {"fuerza": 10, "destreza": 10, "constitucion": 10})
        self.b = Personaje("Receptor", "espada_basica", {"fuerza": 10, "destreza": 10, "constitucion": 10})
        for p in (self.a, self.b):
            p.inventario.recolectar("material_hierro", 20)
            p.inventario.recolectar("glandula_venenosa", 2)
            self.roster.save_to_disk(p)
        self.taller = Workshop(self.roster)

    def transfer(self, accion, p, instance_id, cantidad=1):
        return self.taller.ejecutar(accion, p.id, instance_id=instance_id, cantidad=cantidad)

    def test_preview_cubre_cada_perfil_sin_crear_ni_consumir(self):
        antes = serializar_personaje(self.a)
        cache = deepcopy(item_factory._instancias)
        datos = crafting_data()
        for exp in datos["experiencia_por_tier"]:
            self.a.crafting_exp = exp
            for tipo in datos["tipos"]:
                for material in datos["materiales"]:
                    for componente in [None, *datos["afijos"]]:
                        with patch("crafting.uuid4", side_effect=AssertionError("Preview creó un UUID")):
                            preview = previsualizar_arma(self.a, tipo, material, componente)
                        for perfil in datos["perfiles"]:
                            arma = generar_arma(self.a, tipo, material, componente, rng=Mock(choice=Mock(return_value=perfil)))
                            for indice, clave in enumerate(("minimo", "maximo")):
                                self.assertLessEqual(preview["ataque"][clave][0], arma["ataque"][indice])
                                self.assertGreaterEqual(preview["ataque"][clave][1], arma["ataque"][indice])
                            for clave, limites in preview["rangos"].items():
                                self.assertLessEqual(limites[0], arma[clave])
                                self.assertGreaterEqual(limites[1], arma[clave])
                            for clave in ("durabilidad", "peso", "requisitos", "afijo"):
                                self.assertEqual(preview[clave], arma[clave])
        self.a.crafting_exp = antes["crafting_exp"]
        self.assertEqual(serializar_personaje(self.a), antes)
        self.assertEqual(item_factory._instancias, cache)

    def test_preview_materiales_componente_y_capacidad(self):
        preview = previsualizar_arma(self.a, "espada", "hierro", "glandula_venenosa")
        self.assertTrue(preview["puede_fabricar"])
        self.assertEqual([(r["disponible"], r["necesario"]) for r in preview["recursos"]], [(20, 3), (2, 1)])
        self.assertFalse(previsualizar_arma(self.a, "espada", "acero")["puede_fabricar"])
        self.assertFalse(previsualizar_arma(self.a, "espada", "hierro", "colmillo_bestia")["puede_fabricar"])
        self.a.inventario.capacidad = self.a.inventario.slots_ocupados
        self.assertFalse(previsualizar_arma(self.a, "espada", "hierro")["espacio_disponible"])
        self.a.inventario.extraer("material_hierro", 17)
        self.assertTrue(previsualizar_arma(self.a, "espada", "hierro")["puede_fabricar"])
        fabricar(self.a, "espada", "hierro")
        self.assertEqual(self.a.inventario.slots_ocupados, self.a.inventario.capacidad)

    def test_progreso_entre_tiers_y_tope(self):
        for exp, tier, porcentaje in [(0, 1, 0), (4, 1, 80), (5, 2, 0), (10, 2, 50),
                                      (15, 3, 0), (30, 4, 0), (40, 4, 50), (50, 5, 100), (90, 5, 100)]:
            p = progreso_crafteo(exp)
            self.assertEqual((p["tier"], p["porcentaje"]), (tier, porcentaje))
            self.assertEqual(p["siguiente_tier"], tier + 1 if tier < 5 else None)

    def test_deposito_materiales_masivo_persistente(self):
        self.a.inventario.recolectar("maza_hierro")
        self.roster.save_to_disk(self.a)
        estado = self.taller.ejecutar("depositar_materiales", self.a.id)
        self.assertEqual(estado["transferidos"], 22)
        self.assertTrue(all(i["categoria"] != "material" for i in estado["inventario"]))
        self.assertTrue(any(i["item_id"] == "maza_hierro" for i in estado["inventario"]))
        self.assertFalse(self.taller.previsualizar(self.a.id, "espada", "hierro")["puede_fabricar"])
        recargado = CharacterRoster(self.temp.name)
        self.assertEqual(recargado.vault.serializar()["items"]["material_hierro"], 20)
        self.assertEqual(recargado.vault.serializar()["items"]["glandula_venenosa"], 2)

    def test_deposito_todo_omite_equipo_y_bloqueados(self):
        self.a.inventario.recolectar("maza_hierro")
        self.roster.save_to_disk(self.a)
        with patch.object(item_factory, "permite_vault", side_effect=lambda item: item != "glandula_venenosa"):
            estado = self.taller.ejecutar("depositar_todo", self.a.id)
        self.assertEqual(estado["transferidos"], 21)
        self.assertTrue(any(i["equipado"] for i in estado["inventario"]))
        self.assertTrue(any(i["item_id"] == "glandula_venenosa" for i in estado["inventario"]))
        self.assertEqual(self.roster.vault.serializar()["items"]["maza_hierro"], 1)

    def test_deposito_masivo_rollback_por_capacidad_y_disco(self):
        self.roster.vault = SharedVault(capacidad=1)
        antes = deepcopy(self.roster.personajes)
        with self.assertRaisesRegex(ValueError, "No se movió"):
            self.taller.ejecutar("depositar_materiales", self.a.id)
        self.assertEqual(self.roster.personajes, antes)
        self.assertEqual(self.roster.vault.slots_ocupados, 0)
        self.roster.vault = SharedVault()
        with patch("os.replace", side_effect=OSError("disco")), self.assertRaises(ErrorGuardado):
            self.taller.ejecutar("depositar_materiales", self.a.id)
        self.assertEqual(self.roster.personajes, antes)
        self.assertEqual(self.roster.vault.slots_ocupados, 0)

    def test_deposito_masivo_fusiona_stacks_en_vault_lleno(self):
        self.roster.vault = SharedVault(capacidad=2)
        self.roster.vault.recolectar("material_hierro", 1)
        self.roster.vault.recolectar("glandula_venenosa", 1)
        estado = self.taller.ejecutar("depositar_materiales", self.a.id)
        self.assertEqual(estado["vault"]["ocupados"], 2)
        self.assertEqual(self.roster.vault.serializar()["items"]["material_hierro"], 21)
        with self.assertRaisesRegex(ValueError, "No hay objetos"):
            self.taller.ejecutar("depositar_materiales", self.a.id)

    def test_stack_parcial_merge_y_cambio_personaje(self):
        self.transfer("depositar", self.a, "material_hierro", 5)
        self.assertEqual(deserializar_personaje(self.roster.obtener(self.a.id)).inventario.cantidad("material_hierro"), 15)
        self.transfer("depositar", self.b, "material_hierro", 5)
        self.assertEqual(self.roster.vault.slots_ocupados, 1)
        self.transfer("retirar", self.b, "material_hierro", 10)
        self.assertEqual(deserializar_personaje(self.roster.obtener(self.b.id)).inventario.cantidad("material_hierro"), 25)
        self.assertEqual(self.roster.vault.slots_ocupados, 0)

    def test_arma_fabricada_conserva_identidad_nombre_afijo_al_reiniciar(self):
        estado = self.taller.ejecutar("fabricar", self.a.id, tipo="lanza", material="hierro", componente="glandula_venenosa")
        arma_id = estado["arma_creada"]["id"]
        self.taller.ejecutar("nombrar", self.a.id, item_id=arma_id, nombre="La Última Razón")
        esperado = self.roster.obtener(self.a.id)["custom"][arma_id]
        self.transfer("depositar", self.a, arma_id)
        item_factory._instancias.pop(arma_id)
        nuevo = CharacterRoster(self.temp.name)
        resultado = Workshop(nuevo).ejecutar("retirar", self.b.id, instance_id=arma_id)
        fila = next(e for e in resultado["inventario"] if e["instance_id"] == arma_id)
        self.assertEqual(fila["custom_data"], esperado)
        self.assertEqual(nuevo.vault.slots_ocupados, 0)
        self.assertNotIn(arma_id, nuevo.obtener(self.a.id)["custom"])
        Workshop(nuevo).ejecutar("equipar", self.b.id, item_id=arma_id)
        recargado = CharacterRoster(self.temp.name)
        motor = MotorJuego(roster=recargado)
        motor.cargar_personaje(self.b.id)
        self.assertEqual(motor.estado()["jugador"]["arma"], "La Última Razón")
        self.assertEqual(motor.jugador.inventario.arma_equipada.id, arma_id)

    def test_equipo_estatico_es_instancia_no_stack(self):
        self.a.inventario.recolectar("maza_hierro", 2)
        self.roster.save_to_disk(self.a)
        entradas = [e for e in self.taller.estado(self.a.id)["inventario"] if e["item_id"] == "maza_hierro"]
        self.assertEqual(len(entradas), 2)
        self.assertNotEqual(entradas[0]["instance_id"], entradas[1]["instance_id"])
        for entrada in entradas:
            self.transfer("depositar", self.a, entrada["instance_id"])
        self.assertEqual(self.roster.vault.slots_ocupados, 2)
        self.transfer("retirar", self.b, entradas[0]["instance_id"])
        self.assertIn(entradas[0]["instance_id"], self.roster.obtener(self.b.id)["instancias"])

    def test_cantidades_invalidas_no_mutan(self):
        antes = self.roster.personajes
        for cantidad in (0, -1, True, 1.5, "5", 21):
            with self.assertRaises(ValueError):
                self.transfer("depositar", self.a, "material_hierro", cantidad)
            self.assertEqual(self.roster.personajes, antes)
            self.assertEqual(self.roster.vault.slots_ocupados, 0)

    def test_equipado_y_bloqueado_rechazados(self):
        arma = next(e for e in self.taller.estado(self.a.id)["inventario"] if e["equipado"])
        with self.assertRaises(ValueError):
            self.transfer("depositar", self.a, arma["instance_id"])
        with patch.dict(crafting_data()["vault"], {"bloqueados": ["material_hierro"]}):
            with self.assertRaises(ValueError):
                self.transfer("depositar", self.a, "material_hierro")
        self.assertEqual(self.roster.vault.slots_ocupados, 0)

    def test_vault_lleno_no_muta_pero_permite_merge(self):
        self.roster.vault = SharedVault(capacidad=1)
        self.transfer("depositar", self.a, "material_hierro")
        with self.assertRaises(ValueError):
            self.transfer("depositar", self.a, "glandula_venenosa")
        self.transfer("depositar", self.a, "material_hierro")
        self.assertEqual(self.roster.vault.entradas()[0]["cantidad"], 2)

    def test_inventario_lleno_rechaza_retiro_sin_perdida(self):
        self.transfer("depositar", self.a, "glandula_venenosa")
        p = deserializar_personaje(self.roster.obtener(self.b.id))
        p.inventario.extraer("glandula_venenosa", 2)
        p.inventario.capacidad = p.inventario.slots_ocupados
        self.roster.save_to_disk(p)
        antes = self.roster.vault.serializar()
        with self.assertRaises(ValueError):
            self.transfer("retirar", self.b, "glandula_venenosa")
        self.assertEqual(self.roster.vault.serializar(), antes)

    def test_fallo_disco_revierte_ambos_contenedores_y_reabre(self):
        antes = self.roster.personajes
        with patch("persistence.os.replace", side_effect=OSError("disco")):
            with self.assertRaises(ErrorGuardado):
                self.transfer("depositar", self.a, "material_hierro", 5)
        self.assertEqual(self.roster.personajes, antes)
        self.assertEqual(self.roster.vault.slots_ocupados, 0)
        nuevo = CharacterRoster(self.temp.name)
        self.assertEqual(nuevo.personajes, antes)
        self.assertEqual(nuevo.vault.slots_ocupados, 0)

    def test_transferencias_concurrentes_no_duplican(self):
        self.transfer("depositar", self.a, "material_hierro", 5)
        def retirar():
            try:
                self.transfer("retirar", self.b, "material_hierro", 5)
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(lambda _: retirar(), range(2))), 1)

    def test_todas_las_categorias_se_transfieren_sin_perder_instancias(self):
        for item in item_factory.todos():
            if item.id != "espada_basica":
                self.a.inventario.recolectar(item.id)
        self.roster.save_to_disk(self.a)
        entradas = [e for e in self.taller.estado(self.a.id)["inventario"] if not e["equipado"]]
        self.assertTrue({"arma", "armadura", "secundario", "consumible", "material"}.issubset({e["categoria"] for e in entradas}))
        for entrada in entradas:
            self.transfer("depositar", self.a, entrada["instance_id"], entrada["cantidad"])
            self.transfer("retirar", self.b, entrada["instance_id"], entrada["cantidad"])
        ids = {e["instance_id"] for e in self.taller.estado(self.b.id)["inventario"]}
        self.assertTrue(all(e["instance_id"] in ids for e in entradas))
        self.assertEqual(self.roster.vault.slots_ocupados, 0)

    def test_vault_sobrevive_descartar_personaje(self):
        self.transfer("depositar", self.a, "material_hierro", 5)
        self.roster.descartar(self.a.id)
        nuevo = CharacterRoster(self.temp.name)
        self.assertEqual(nuevo.vault.entradas()[0]["cantidad"], 5)
        Workshop(nuevo).ejecutar("retirar", self.b.id, instance_id="material_hierro", cantidad=5)
        self.assertEqual(nuevo.vault.slots_ocupados, 0)

    def test_migracion_guardado_sin_vault_ni_instancias(self):
        anteriores = self.roster.personajes
        for p in anteriores:
            for campo in ("instancias", "custom", "capacidad_inventario", "crafting_exp"):
                p.pop(campo)
        self.roster.archivo.guardar(1, {"roster": anteriores})
        nuevo = CharacterRoster(self.temp.name)
        self.assertEqual(nuevo.vault.slots_ocupados, 0)
        p = deserializar_personaje(nuevo.obtener(self.a.id))
        self.assertEqual(p.crafting_tier, 1)
        self.assertEqual(p.inventario.cantidad("material_hierro"), 20)
        nuevo.save_to_disk(p)
        self.assertEqual(nuevo.personajes, CharacterRoster(self.temp.name).personajes)

    def test_politicas_bound_y_quest_locked(self):
        for politica in ("bound", "quest_locked", "vault_allowed"):
            with patch.dict(item_factory._datos["material_hierro"], {politica: politica != "vault_allowed"}):
                with self.assertRaises(ValueError):
                    self.transfer("depositar", self.a, "material_hierro")

    def test_renombrado_fallido_restaurado_incluso_en_cache(self):
        arma = self.taller.ejecutar("fabricar", self.a.id, tipo="espada", material="hierro")["arma_creada"]
        with patch("persistence.os.replace", side_effect=OSError("disco")):
            with self.assertRaises(ErrorGuardado):
                self.taller.ejecutar("nombrar", self.a.id, item_id=arma["id"], nombre="No confirmado")
        self.assertEqual(item_factory.crear(arma["id"]).nombre, arma["nombre"])
        self.assertEqual(self.roster.obtener(self.a.id)["custom"][arma["id"]]["nombre"], arma["nombre"])

    def test_crafteo_consume_recursos_y_sube_tier_sin_elegirlo(self):
        for _ in range(5):
            self.taller.ejecutar("fabricar", self.a.id, tipo="daga", material="hierro")
        p = deserializar_personaje(self.roster.obtener(self.a.id))
        self.assertEqual(p.crafting_tier, 2)
        self.assertEqual(p.inventario.cantidad("material_hierro"), 5)
        antes = self.roster.personajes
        with self.assertRaises(ValueError):
            self.taller.ejecutar("fabricar", self.a.id, tipo="daga", material="hierro")
        self.assertEqual(self.roster.personajes, antes)

    def test_fallo_crafteo_no_consume(self):
        antes = self.roster.personajes
        with patch("persistence.os.replace", side_effect=OSError("disco")):
            with self.assertRaises(ErrorGuardado):
                self.taller.ejecutar("fabricar", self.a.id, tipo="daga", material="hierro", componente="glandula_venenosa")
        self.assertEqual(self.roster.personajes, antes)

    def test_generador_conserva_presupuesto_y_limita_variacion(self):
        datos = crafting_data()
        for tier, xp in enumerate(datos["experiencia_por_tier"], 1):
            self.a.crafting_exp = xp
            for tipo, plantilla in datos["tipos"].items():
                for material, metal in datos["materiales"].items():
                    for perfil in datos["perfiles"]:
                        rng = Mock(); rng.choice.return_value = perfil
                        arma = generar_arma(self.a, tipo, material, rng=rng)
                        presupuesto = datos["tiers"][str(tier)] * (0.97 if metal.get("bonus_sobrenatural") else 1)
                        self.assertAlmostEqual(sum(arma["distribucion"]), presupuesto)
                        for real, base, cambio in zip(arma["distribucion"], plantilla["distribucion"], metal["cambios"]):
                            referencia = (base + cambio) * presupuesto / 100
                            self.assertLessEqual(abs(real / referencia - 1), 0.100001)
        arma = generar_arma(self.a, "espada", "hierro", "glandula_venenosa")
        self.assertAlmostEqual(sum(arma["distribucion"]), arma["presupuesto"] * 0.9)

    def test_nombre_no_cambia_stats_ni_colisiona_con_catalogo(self):
        arma = self.taller.ejecutar("fabricar", self.a.id, tipo="espada", material="hierro")["arma_creada"]
        self.taller.ejecutar("nombrar", self.a.id, item_id=arma["id"], nombre="Espada de hierro")
        guardada = self.roster.obtener(self.a.id)["custom"][arma["id"]]
        self.assertEqual({k:v for k,v in arma.items() if k != "nombre"}, {k:v for k,v in guardada.items() if k != "nombre"})
        self.assertEqual(item_factory.crear("Espada de hierro").id, "espada_hierro")

    def test_botin_materiales_y_componentes(self):
        rng = Mock(); rng.random.return_value = 0; rng.choice.side_effect = ["hierro", "glandula_venenosa"]; rng.randint.return_value = 3
        self.assertEqual(botin_crafteo(rng), [("material_hierro", 3), ("glandula_venenosa", 1)])

    def test_arma_procedural_funciona_en_ambos_modos_y_aplica_afijo(self):
        arma = fabricar(self.a, "espada", "hierro", "glandula_venenosa", random.Random(7))
        self.a.inventario.equipar(arma["id"], self.a)
        self.roster.save_to_disk(self.a)
        c = Personaje("Tercero", "espada_basica", {"fuerza": 10, "destreza": 10, "constitucion": 10})
        self.roster.save_to_disk(c)
        selecciones = [Seleccion(p["id"], arma=p["arma_equipada"]) for p in self.roster.personajes]
        combate = CombatResolver(selecciones, roster=self.roster.personajes)
        self.assertEqual(combate.party[0].modelo.inventario.arma_equipada.id, arma["id"])
        motor = MotorJuego(roster=self.roster); motor.cargar_personaje(self.a.id)
        self.assertEqual(motor.estado()["jugador"]["ataque_minimo"], combate.party[0].estado()["ataque_minimo"])
        rng = Mock(); rng.random.return_value = 0
        self.assertEqual(activar_afijo(self.a, motor.enemigo_actual, rng), "veneno")
        hp = motor.enemigo_actual.hp
        self.assertEqual(list(ticks_afijos(motor.enemigo_actual)), [("veneno", 2)])
        self.assertEqual(motor.enemigo_actual.hp, hp-2)
        self.assertEqual(armadura_tras_penetracion(self.a, 20), max(0, 20-arma["penetracion"]))
        combate.ejecutar()


if __name__ == "__main__":
    unittest.main()
