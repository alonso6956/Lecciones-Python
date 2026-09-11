"""Regresiones de checkpoints, progresión y aislamiento entre ambos modos."""

from copy import deepcopy
from dataclasses import asdict, replace
import json
import random
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from character import Personaje
from character_roster import CharacterRoster, deserializar_personaje, serializar_personaje
from game_engine import ErrorJuego, MotorJuego
from habilidades import habilidad_factory
from item import Arma
from item_factory import item_factory
from persistence import GestorGuardado, ErrorGuardado
from progression import CLASES
from tactical_ai import AIController
from tactical_controller import PrototypeController
from tactical_models import BuildManager


class RosterTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.roster = CharacterRoster(self.temp.name)
        self.motor = MotorJuego(random.Random(20), self.roster)
        self.motor.nueva_partida()
        self.motor.iniciar("Aventurero")
        self.id = self.motor.jugador.id
        self.ruta = self.roster.archivo.directorio / "roster.json"

    def test_vida_por_nivel_es_aditiva_y_no_se_acumula_al_recalcular(self):
        for constitucion in (1, 5):
            jugador = Personaje("Vida", "espada_basica", {"fuerza": 1, "destreza": 1, "constitucion": constitucion})
            base = jugador.salud_maxima
            jugador.hp -= 20
            for nivel in range(2, 31):
                jugador.subir_nivel()
                self.assertEqual(jugador.salud_maxima, base + 5 * (nivel - 1))
                self.assertEqual(jugador.hp, jugador.salud_maxima - 20)
                jugador.recalcular_por_equipo()
                self.assertEqual(jugador.salud_maxima, base + 5 * (nivel - 1))
                self.assertEqual(jugador.hp, jugador.salud_maxima - 20)
                self.assertEqual(jugador.energia_maxima, 3 + nivel // 10)

    def test_subir_nivel_con_constitucion_suma_ambos_incrementos_una_vez(self):
        jugador = self.motor.jugador
        jugador.hp = 25
        jugador.subir_nivel("constitucion")
        self.assertEqual(jugador.salud_maxima, 65)
        self.assertEqual(jugador.hp, 40)
        jugador.subir_nivel("fuerza")
        self.assertEqual(jugador.salud_maxima, 70)
        self.assertEqual(jugador.hp, 45)

    def test_hitos_energia_se_aplican_en_combate_y_al_recargar(self):
        for nivel in (10, 20, 30):
            with self.subTest(nivel=nivel):
                m = self.motor
                m.cargar_personaje(self.id)
                m.jugador.nivel = nivel - 1
                m.jugador.exp = (nivel - 1) * 30
                m.jugador.salud_maxima = m.jugador.calcular_salud_maxima()
                m.jugador.hp = m.jugador.salud_maxima
                m.enemigo_actual.exp = 0
                m.energia = 1
                m._resolver_victoria()
                self.assertEqual(m.jugador.nivel, nivel)
                self.assertEqual(m.energia, 2)
                self.assertEqual(m.estado()["jugador"]["energia_maxima"], 3 + nivel // 10)
                for _ in range(10):
                    m._accion_jugador("defender")
                self.assertEqual(m.energia, m.energia_maxima)
                self.roster.save_to_disk(m.jugador)
                cargado = MotorJuego(roster=CharacterRoster(self.temp.name))
                cargado.cargar_personaje(self.id)
                self.assertEqual(cargado.jugador.salud_maxima, 50 + 5 * (nivel - 1))
                self.assertEqual(cargado.energia, 3 + nivel // 10)
                self.assertEqual(cargado.jugador.hp, cargado.jugador.salud_maxima)

    def test_creacion_nombre_id_equipo_y_reinicio_servidor(self):
        datos = CharacterRoster(self.temp.name).obtener(self.id)
        self.assertEqual(datos["nivel"], 1)
        self.assertIsNone(datos["clase"])
        self.assertIsNone(datos["chispa"])
        self.assertEqual(datos["inventario"], [{"id": "espada_basica", "cantidad": 1}])
        self.assertEqual(datos["arma_equipada"], "espada_basica")
        self.assertEqual(datos["habilidades"], {})
        self.motor.abandonar()
        self.motor.nueva_partida()
        self.motor.iniciar("Aventurero", "Maza de hierro")
        self.assertNotEqual(self.id, self.motor.jugador.id)
        self.assertEqual(len(self.roster.personajes), 2)
        self.assertEqual(self.motor.jugador.arma, "Espada básica")

    def test_avanzar_habitacion_guarda_checkpoint(self):
        anterior = self.ruta.read_bytes()
        self.motor.jugador.oro = 150
        self.motor.jugador.exp = 80
        self.motor.fase = "transicion"
        self.motor.siguiente_habitacion()
        self.assertNotEqual(self.ruta.read_bytes(), anterior)
        self.assertEqual(self.roster.obtener(self.id)["oro"], 150)

    def test_tienda_guarda_solo_personaje_y_carga_limpia(self):
        m = self.motor
        m.jugador.oro = 200
        m.jugador.subir_nivel("constitucion")
        m.jugador.exp = 30
        m.fase = "transicion"
        m.siguiente_habitacion()
        m.abandonar()
        m.comprar("armas", "Maza de hierro", self.id)
        m.comprar("pociones", "Pocion mediana", self.id)
        m.cargar_personaje(self.id)
        m.fase = "transicion"
        m.jugador.hp = 2
        m.is_defending = True
        m.aturdimiento_jugador = 2
        m.jugador.establecer_mitigar_dano(3)
        m.siguiente_habitacion()
        contenido = json.loads(self.ruta.read_text(encoding="utf-8"))
        texto = json.dumps(contenido)
        for prohibido in ("hp", "numero_habitacion", "habitacion", "fase", "cooldowns_habilidades", "mitigar_dano_activo", "enemigo"):
            self.assertNotIn('"' + prohibido + '"', texto)
        checkpoint = deepcopy(m.exportar_guardado())
        m.jugador.oro += 999
        m.abandonar()
        m.cargar_personaje(self.id)
        self.assertEqual(m.exportar_guardado(), checkpoint)
        self.assertEqual(m.numero_habitacion, 1)
        self.assertEqual(m.jugador.hp, m.jugador.salud_maxima)
        self.assertFalse(m.is_defending)
        self.assertFalse(m.jugador.mitigar_dano_activo)
        self.assertEqual(m.aturdimiento_jugador, 0)
        self.assertTrue(all(v == 0 for v in m.cooldowns_habilidades.values()))

    def test_muerte_guarda_exp_oro_y_niveles_incluso_sin_tienda(self):
        m = self.motor
        anterior = self.ruta.read_bytes()
        m.enemigo_actual.exp = 30
        m.enemigo_actual.oro = (25, 25)
        m._resolver_victoria()
        m.subir_nivel("constitucion")
        esperado = m.exportar_guardado()
        # Comienza otro combate y cae antes de alcanzar su primera tienda.
        m._iniciar_combate()
        m.jugador.hp = 0
        m.actuar("atacar")
        self.assertEqual(m.fase, "menu")
        self.assertEqual(m.numero_habitacion, 1)
        self.assertNotEqual(self.ruta.read_bytes(), anterior)
        m = MotorJuego(roster=CharacterRoster(self.temp.name))
        m.cargar_personaje(self.id)
        self.assertEqual(m.exportar_guardado(), esperado)
        self.assertEqual(m.jugador.nivel, 2)
        self.assertEqual(m.jugador.exp, 30)
        self.assertEqual(m.jugador.oro, 25)
        self.assertEqual(m.jugador.hp, m.jugador.salud_maxima)
        self.assertEqual(m.numero_habitacion, 1)
        # Morir otra vez sin ganar recompensas no vuelve a sumar EXP ni oro.
        m.jugador.hp = 0
        m.actuar("atacar")
        m.cargar_personaje(self.id)
        self.assertEqual(m.exportar_guardado(), esperado)

    def test_muerte_con_fallo_de_disco_permita_reintentar_sin_perder_progreso(self):
        m = self.motor
        m.jugador.exp = 20
        m.jugador.oro = 47
        m.jugador.hp = 0
        anterior = self.ruta.read_bytes()
        with patch.object(self.roster.archivo, "guardar", side_effect=ErrorGuardado("Sin espacio")):
            with self.assertRaises(ErrorGuardado):
                m.actuar("atacar")
        self.assertEqual(m.fase, "muerte")
        self.assertEqual(m.jugador.exp, 20)
        self.assertEqual(m.jugador.oro, 47)
        self.assertEqual(self.ruta.read_bytes(), anterior)
        m.respawn()
        self.assertEqual(m.fase, "menu")
        self.assertEqual(CharacterRoster(self.temp.name).obtener(self.id)["oro"], 47)
        self.assertEqual(CharacterRoster(self.temp.name).obtener(self.id)["exp"], 20)

    def test_guardado_fallido_mantiene_transicion_y_checkpoint(self):
        self.motor.fase = "transicion"
        self.motor.jugador.oro = 333
        antes = self.roster.personajes
        with patch.object(self.roster.archivo, "guardar", side_effect=ErrorGuardado("Sin espacio")):
            with self.assertRaises(ErrorGuardado):
                self.motor.siguiente_habitacion()
        self.assertEqual(self.motor.fase, "transicion")
        self.assertEqual(self.roster.personajes, antes)

    def test_descartar_ultimo_personaje_persiste_roster_vacio(self):
        self.roster.descartar(self.id)
        self.assertEqual(CharacterRoster(self.temp.name).personajes, [])
        with self.assertRaises(ErrorGuardado):
            self.roster.obtener(self.id)
        with self.assertRaises(ErrorGuardado):
            self.roster.descartar(self.id)

    def test_descartar_con_fallo_de_disco_conserva_personaje(self):
        antes = self.roster.personajes
        disco = self.ruta.read_bytes()
        with patch.object(self.roster.archivo, "guardar", side_effect=ErrorGuardado("Sin espacio")):
            with self.assertRaises(ErrorGuardado):
                self.roster.descartar(self.id)
        self.assertEqual(self.roster.personajes, antes)
        self.assertEqual(self.ruta.read_bytes(), disco)

    def test_checksum_corrupto_recupera_respaldo(self):
        self.motor.fase = "transicion"
        self.motor.jugador.oro = 300
        self.motor.siguiente_habitacion()
        self.ruta.write_text("archivo truncado", encoding="utf-8")
        recuperado = CharacterRoster(self.temp.name)
        self.assertEqual(recuperado.obtener(self.id)["oro"], 0)

    def test_hitos_10_30_saltos_y_clase_solo_etiqueta(self):
        m = self.motor
        m.jugador.nivel = 9
        m.jugador.exp = 900
        m.enemigo_actual.exp = 0
        m._resolver_victoria()
        self.assertEqual(m.jugador.nivel, 10)
        self.assertTrue(m.estado()["jugador"]["clase_pendiente"])
        antes = m.jugador.calcular_dano_base(), m.jugador.salud_maxima, m.jugador.velocidad
        m.elegir_clase("guerrero")
        self.assertEqual(antes, (m.jugador.calcular_dano_base(), m.jugador.salud_maxima, m.jugador.velocidad))
        with self.assertRaises(ValueError):
            m.elegir_clase("picaro")
        while m.fase == "nivel":
            m.subir_nivel("fuerza")
        self.assertEqual(m.jugador.nivel, 30)
        self.assertEqual(m.jugador.chispa, "chispa_latente")
        self.assertEqual(sum(e["tipo"] == "infestacion_chispa" for e in m.eventos), 1)
        m.fase = "transicion"
        m.siguiente_habitacion()
        m.cargar_personaje(self.id)
        self.assertEqual(m.jugador.clase, "guerrero")
        self.assertFalse(any(e["tipo"] == "infestacion_chispa" for e in m.eventos))

    def test_elegir_clase_despues_de_asignar_stat_no_bloquea(self):
        m = self.motor
        m.jugador.nivel = 9
        m.jugador.exp = 270
        m.enemigo_actual.exp = 0
        m._resolver_victoria()
        m.subir_nivel("constitucion")
        self.assertEqual(m.fase, "nivel")
        m.elegir_clase("guardian")
        self.assertEqual(m.fase, "transicion")

    def test_habilidades_no_se_conceden_por_equipo(self):
        jugador = self.motor.jugador
        jugador.puntos_habilidad = 10
        for arma in (i for i in item_factory.todos() if isinstance(i, Arma)):
            self.assertFalse(hasattr(arma, "pasiva_id"))
        for habilidad in habilidad_factory.todas():
            self.assertFalse(hasattr(habilidad, "tipo_arma_requerida"))
            with self.assertRaises(ValueError):
                jugador.mejorar_habilidad(habilidad.id)
        # El futuro árbol se consulta por clase y funciona con cualquier arma.
        jugador.nivel = 10
        jugador.elegir_clase("guerrero")
        with patch.dict(CLASES["guerrero"], habilidades=["hack_slash"]):
            jugador.mejorar_habilidad("hack_slash")
            self.assertTrue(jugador.puede_usar_habilidad("hack_slash"))
            jugador.inventario.recolectar("dagas_hierro")
            jugador.inventario.equipar("dagas_hierro", jugador)
            self.assertTrue(jugador.puede_usar_habilidad("hack_slash"))

    def test_tactico_usa_stats_inventario_y_copias_del_roster(self):
        tactico = PrototypeController(roster=self.roster)
        with self.assertRaises(ValueError):
            tactico.iniciar()
        for nombre in ("Dos", "Tres", "Cuatro"):
            self.motor.abandonar()
            self.motor.nueva_partida()
            self.motor.iniciar(nombre)
        estado = tactico.estado()
        self.assertTrue(estado["tactico_disponible"])
        selecciones = estado["selecciones"]
        selecciones[0]["personaje_id"] = self.motor.jugador.id
        tactico.preparar(selecciones)
        ilegal = deepcopy(selecciones)
        ilegal[0]["arma"] = "maza_hierro"
        with self.assertRaises(ValueError):
            tactico.preparar(ilegal)
        antes = self.roster.personajes
        tactico.iniciar()
        for actor in tactico.combate.party:
            datos = self.roster.obtener(actor.id)
            self.assertEqual(actor.modelo.fuerza, datos["estadisticas"]["fuerza"])
            self.assertEqual(actor.modelo.nivel, datos["nivel"])
            self.assertEqual(AIController.elegir(actor, tactico.combate.party, tactico.combate.jefe, 100).tipo, "ataque")
        while tactico.fase == "combate":
            tactico.avanzar()
        self.assertEqual(self.roster.personajes, antes)

    def test_legacy_importa_slots_y_no_modifica_originales(self):
        with TemporaryDirectory() as carpeta:
            legacy = GestorGuardado(carpeta)
            jugador = Personaje("Viejo", "espada_hierro", {"fuerza": 5, "destreza": 2, "constitucion": 3})
            datos = {"nombre": jugador.nombre, "arma": jugador.arma,
                     "inventario": jugador.inventario.serializar(), "fuerza": 5,
                     "destreza": 2, "constitucion": 3, "nivel": 15, "oro": 60,
                     "exp": 430, "hp": 0, "habilidades": {"hack_slash": 2}, "puntos_habilidad": 3}
            legacy.guardar(2, {"jugador": datos, "fase": "muerte", "numero_habitacion": 40})
            ruta = legacy.directorio / "save_slot_2.json"
            original = ruta.read_bytes()
            roster = CharacterRoster(carpeta)
            self.assertEqual(len(roster.personajes), 1)
            registro = roster.personajes[0]
            self.assertEqual(registro["nivel"], 15)
            self.assertEqual(registro["puntos_habilidad"], 5)
            self.assertEqual(registro["habilidades"], {})
            self.assertEqual(CharacterRoster(carpeta).personajes, roster.personajes)
            roster.save_to_disk(deserializar_personaje(registro))
            self.assertEqual(ruta.read_bytes(), original)
            self.assertEqual(CharacterRoster(carpeta).personajes, roster.personajes)


if __name__ == "__main__":
    unittest.main()
