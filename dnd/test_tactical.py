import unittest
from dataclasses import asdict, replace

from simulate_tactical import perfiles, simular
from tactical_ai import AIController
from tactical_combat import CombatResolver
from tactical_controller import PrototypeController
from tactical_diagnostics import CombatLog, DiagnosticEngine
from tactical_models import BuildManager, Encuentro, preparacion_adaptada, preparacion_ofensiva


class TacticalTests(unittest.TestCase):
    def test_t01_combate_3v1_finaliza_sin_input(self):
        combate = CombatResolver(preparacion_ofensiva())
        resultado = combate.ejecutar()
        self.assertIn(resultado["resultado"], ("victoria", "derrota"))
        self.assertLessEqual(resultado["rondas"], combate.encuentro.limite_rondas)
        self.assertEqual(len(resultado["inicial"]["party"]), 3)
        self.assertTrue(any(e["tipo"] == "iniciativa" for e in resultado["eventos"]))
        self.assertEqual(resultado["eventos"][-1]["tipo"], resultado["resultado"])

    def test_t02_ofensiva_registra_fallo_de_escudo_y_castigo(self):
        # Ofensiva con las tres armas disponibles, sin adaptación ni prioridad táctica.
        resultado = CombatResolver(perfiles()["solo_arma"]).ejecutar()
        tipos = [e["tipo"] for e in resultado["eventos"]]
        self.assertIn("escudo_no_roto", tipos)
        self.assertIn("castigo_escudo", tipos)
        self.assertLess(tipos.index("escudo_no_roto"), tipos.index("castigo_escudo"))
        self.assertTrue(any(e["tipo"] == "dano_recibido" and e["fuente_tag"] == "escudo_no_roto" for e in resultado["eventos"]))

    def test_t03_ruptura_mejora_con_preparacion(self):
        ofensiva = simular(Encuentro(), preparacion_ofensiva(), n=30)
        adaptada = simular(Encuentro(), preparacion_adaptada(), n=30)
        self.assertGreater(adaptada["ruptura_exitosa_pct"], ofensiva["ruptura_exitosa_pct"] + 40)
        self.assertGreater(adaptada["victorias_pct"], ofensiva["victorias_pct"] + 40)

    def test_t04_derrota_real_por_sangrado(self):
        resultado = CombatResolver(preparacion_ofensiva()).ejecutar()
        self.assertEqual(resultado["resultado"], "derrota")
        self.assertEqual(resultado["diagnostico"]["causa"], "sangrado")
        self.assertGreaterEqual(resultado["diagnostico"]["contribucion_pct"], 40)

    def test_derrota_real_por_escudo_tiene_diagnostico_distinto(self):
        resultado = CombatResolver(preparacion_adaptada(), seed=1234).ejecutar()
        self.assertEqual(resultado["resultado"], "derrota")
        self.assertEqual(resultado["diagnostico"]["causa"], "escudo_no_roto")
        self.assertGreaterEqual(resultado["diagnostico"]["contribucion_pct"], 40)

    def test_t05_causas_mezcladas(self):
        log = CombatLog()
        for tag in ("sangrado", "fisico", "escudo_no_roto"):
            log.registrar(1, "dano_recibido", fuente_tag=tag, cantidad=10)
        diagnostico = DiagnosticEngine.analizar(log)
        self.assertEqual(diagnostico["causa"], "desgaste_general")
        self.assertAlmostEqual(diagnostico["contribucion_pct"], 33.33)

    def test_t05_derrota_real_mezclada(self):
        resultado = CombatResolver(perfiles()["solo_build"], seed=1235).ejecutar()
        self.assertEqual(resultado["resultado"], "derrota")
        self.assertEqual(resultado["diagnostico"]["causa"], "desgaste_general")

    def test_t06_builds_no_acumulan_stats(self):
        base = [a.estado() for a in BuildManager.crear_party(preparacion_ofensiva())]
        for _ in range(5):
            BuildManager.crear_party(preparacion_adaptada())
        self.assertEqual(base, [a.estado() for a in BuildManager.crear_party(preparacion_ofensiva())])

    def test_t07_reintento_limpio_conserva_selecciones(self):
        controller = PrototypeController()
        inicial = controller.iniciar(1235)["combate"]
        while controller.fase == "combate":
            controller.avanzar()
        log_anterior = controller.combate.log.serializar()
        self.assertTrue(log_anterior)
        selecciones = controller.estado()["selecciones"]
        controller.reajustar()
        self.assertEqual(controller.estado()["selecciones"], selecciones)
        nuevo = controller.iniciar(1235)
        self.assertEqual(nuevo["combate"], inicial)
        self.assertEqual(nuevo["eventos"], [])
        self.assertTrue(all(not a.estados and not a.cooldowns for a in controller.combate.party))

    def test_t08_victoria_tras_reajuste_sin_subir_nivel(self):
        controller = PrototypeController()
        controller.iniciar(1235)
        while controller.fase == "combate":
            controller.avanzar()
        self.assertEqual(controller.estado()["resultado"]["resultado"], "derrota")
        controller.reajustar()
        controller.preparar([asdict(s) for s in preparacion_adaptada()])
        controller.iniciar(1235)
        while controller.fase == "combate":
            controller.avanzar()
        resultado = controller.estado()["resultado"]
        self.assertEqual(resultado["resultado"], "victoria")
        self.assertEqual(len(resultado["supervivientes"]), 3)
        self.assertTrue(all(a["nivel"] == 1 for a in resultado["final"]["party"]))

    def test_t09_seed_reproducible(self):
        for preparacion in (preparacion_ofensiva(), preparacion_adaptada()):
            self.assertEqual(CombatResolver(preparacion, seed=54).ejecutar(),
                             CombatResolver(preparacion, seed=54).ejecutar())

    def test_log_no_duplica_dano_ni_pesa_muertes(self):
        log = CombatLog()
        log.registrar(1, "dano_recibido", fuente_tag="sangrado", cantidad=40)
        log.registrar(1, "tick_sangrado", fuente_tag="sangrado", cantidad=40)
        log.registrar(1, "muerte", fuente_tag="sangrado", cantidad=40)
        log.registrar(1, "dano_recibido", fuente_tag="fisico", cantidad=60)
        self.assertEqual(DiagnosticEngine.analizar(log)["dano_total"], 100)

    def test_ia_primera_coincidencia_y_cooldown(self):
        combate = CombatResolver(preparacion_adaptada())
        cora = combate.party[2]
        cora.estados["sangrado"] = {"cargas": 3, "vence": 4}
        cora.hp = 20
        self.assertEqual(AIController.elegir(cora, combate.party, combate.jefe, 100).tipo, "limpiar")
        cora.cooldowns["limpiar"] = 2
        self.assertEqual(AIController.elegir(cora, combate.party, combate.jefe, 100).tipo, "curar")
        cora.cooldowns["curar"] = 1
        self.assertEqual(AIController.elegir(cora, combate.party, combate.jefe, 100).tipo, "muralla")

    def test_escudo_tiene_dos_rondas_completas(self):
        resultado = CombatResolver(perfiles()["solo_arma"]).ejecutar()
        activacion = next(e for e in resultado["eventos"] if e["tipo"] == "escudo_activado")
        fallo = next(e for e in resultado["eventos"] if e["tipo"] == "escudo_no_roto")
        self.assertEqual(fallo["turno"], activacion["turno"] + 2)

    def test_guerrero_reserva_habilidad_hasta_escudo_y_la_libera_despues(self):
        combate = CombatResolver(preparacion_adaptada())
        bruno = combate.party[1]
        self.assertEqual(AIController.elegir(bruno, combate.party, combate.jefe, 0).tipo, "ataque")
        self.assertEqual(AIController.elegir(bruno, combate.party, combate.jefe, 100, True).tipo, "romper")
        self.assertEqual(AIController.elegir(bruno, combate.party, combate.jefe, 0, True).tipo, "golpe_demoledor")

    def test_overkill_registra_solo_hp_perdido_y_muerte_una_vez(self):
        combate = CombatResolver(preparacion_ofensiva())
        actor = combate.party[0]
        actor.hp = 3
        combate._dano(combate.jefe, actor, 9999, "sangrado")
        combate._dano(combate.jefe, actor, 9999, "sangrado")
        eventos = combate.log.eventos
        self.assertEqual([e.cantidad for e in eventos if e.tipo == "dano_recibido"], [3])
        self.assertEqual(sum(e.tipo == "muerte" for e in eventos), 1)

    def test_no_hay_acciones_de_actores_muertos(self):
        resultado = CombatResolver(preparacion_ofensiva()).ejecutar()
        muertos = set()
        for evento in resultado["eventos"]:
            if evento["tipo"] == "muerte":
                muertos.add(evento["objetivo_id"])
            elif evento["tipo"] == "accion":
                self.assertNotIn(evento["actor_id"], muertos)

    def test_cambio_bloqueado_en_combate_y_seleccion_atomica(self):
        controller = PrototypeController()
        inicial = controller.estado()["selecciones"]
        with self.assertRaises(ValueError):
            controller.preparar([inicial[0]] * 3)
        self.assertEqual(controller.estado()["selecciones"], inicial)
        controller.iniciar()
        with self.assertRaises(ValueError):
            controller.preparar(inicial)
        with self.assertRaises(ValueError):
            controller.reajustar()

    def test_limite_seguridad_termina_combate(self):
        resultado = CombatResolver(preparacion_ofensiva(), replace(Encuentro(), limite_rondas=1)).ejecutar()
        self.assertEqual(resultado["motivo"], "limite_seguridad")
        self.assertEqual(resultado["diagnostico"]["causa"], "desgaste_general")

    def test_diagnostico_vacio_y_umbral_exacto(self):
        log = CombatLog()
        self.assertEqual(DiagnosticEngine.analizar(log)["causa"], "desgaste_general")
        for tag, dano in (("sangrado", 40), ("fisico", 30), ("escudo_no_roto", 30)):
            log.registrar(1, "dano_recibido", fuente_tag=tag, cantidad=dano)
        self.assertEqual(DiagnosticEngine.analizar(log)["causa"], "sangrado")


if __name__ == "__main__":
    unittest.main()
