import unittest
from dataclasses import replace

from enemy_ai import BlancoIA, CerebroEnemigo, PerfilIA
from tactical_board import Tablero, distancia
from tactical_combat import CombatResolver
from tactical_models import Encuentro, preparacion_ofensiva


class EnemyAITests(unittest.TestCase):
    def setUp(self):
        self.tanque = BlancoIA("tanque", 1, 1, defensa=100)
        self.healer = BlancoIA("healer", 1, 4, roles=("sanador",))
        self.blancos = [self.tanque, self.healer]

    def test_bestia_y_tags(self):
        for tags, esperado in [((), "tanque"), (("cazador_healer",), "healer"),
                               (("rompe_tanque",), "tanque")]:
            ia = CerebroEnemigo(PerfilIA(tags=tags))
            self.assertEqual(ia.elegir(1, self.blancos).objetivo_id, esperado)
        herido = replace(self.healer, vida_pct=.1)
        ia = CerebroEnemigo(PerfilIA(tags=("oportunista",)))
        self.assertEqual(ia.elegir(1, [self.tanque, herido]).objetivo_id, "healer")

    def test_soldado_recupera_orden(self):
        ia = CerebroEnemigo(PerfilIA("soldado", objetivo_prioritario="healer"))
        self.assertEqual(ia.elegir(1, self.blancos).objetivo_id, "healer")
        self.assertEqual(ia.elegir(1, [self.tanque]).objetivo_id, "tanque")
        self.assertEqual(ia.elegir(1, self.blancos).objetivo_id, "healer")

    def test_comandante_cadencia_e_invalidez(self):
        ia = CerebroEnemigo(PerfilIA("comandante"))
        self.assertEqual(ia.elegir(1, self.blancos).objetivo_id, "tanque")
        nuevos = [self.tanque, replace(self.healer, amenaza=1)]
        segunda = ia.elegir(1, nuevos)
        self.assertFalse(segunda.reevaluado)
        self.assertEqual(segunda.objetivo_id, "tanque")
        self.assertEqual(ia.elegir(1, nuevos).objetivo_id, "healer")
        self.assertEqual(ia.elegir(1, [self.tanque]).objetivo_id, "tanque")

    def test_provocacion_e_inmunidad(self):
        for inmune, esperado in [(False, "tanque"), (True, "healer")]:
            ia = CerebroEnemigo(PerfilIA(tags=("cazador_healer",), ignora_provocacion=inmune))
            self.assertEqual(ia.elegir(1, self.blancos, provocado_por="tanque").objetivo_id, esperado)

    def test_huida_dos_turnos_y_umbral_estricto(self):
        ia = CerebroEnemigo(PerfilIA(tags=("cobarde",)))
        self.assertEqual(ia.elegir(.30, self.blancos).tipo, "atacar")
        self.assertEqual(ia.elegir(.29, self.blancos).tipo, "huir")
        self.assertEqual(ia.elegir(.8, self.blancos).tipo, "huir")
        self.assertEqual(ia.elegir(.1, self.blancos).tipo, "atacar")

    def test_fanatico_no_cambia_por_puntuacion(self):
        ia = CerebroEnemigo(PerfilIA("comandante", ("fanatico",)))
        ia.elegir(1, self.blancos)
        for _ in range(4):
            self.assertEqual(ia.elegir(.1, [self.tanque, replace(self.healer, amenaza=1)]).objetivo_id, "tanque")
        self.assertEqual(ia.elegir(.1, [self.healer]).objetivo_id, "healer")

    def test_protector_y_backline(self):
        ia = CerebroEnemigo(PerfilIA("comandante", ("cazador_healer", "protector")))
        decision = ia.elegir(1, self.blancos, [BlancoIA("arquero", .3, 2)])
        self.assertEqual((decision.tipo, decision.objetivo_id), ("proteger", "arquero"))
        ia = CerebroEnemigo(PerfilIA(tags=("asesino_backline",)))
        arquero = BlancoIA("arquero", 1, 5, roles=("dano",), linea="retaguardia")
        self.assertEqual(ia.elegir(1, [self.tanque, arquero]).objetivo_id, "arquero")

    def test_invalidos_empates_y_memoria_aislada(self):
        with self.assertRaises(ValueError):
            PerfilIA(tags=("cobarde", "fanatico"))
        with self.assertRaises(ValueError):
            PerfilIA(tags=("inventado",))
        ia = CerebroEnemigo()
        self.assertEqual(ia.elegir(1, [replace(self.tanque, vida_pct=0),
                                     replace(self.healer, distancia=float("inf"))]).tipo, "esperar")
        self.assertEqual(CerebroEnemigo().turno, 0)
        self.assertEqual(ia.elegir(1, self.blancos), CerebroEnemigo().elegir(1, self.blancos[::-1]))

    def test_integracion_reproducible_y_perfil_serializable(self):
        encuentro = Encuentro(perfil_ia={"cerebro": "comandante", "tags": ["rompe_tanque", "cobarde"]})
        def ejecutar():
            return CombatResolver(preparacion_ofensiva(), encuentro, seed=23).ejecutar()
        a = ejecutar()
        self.assertEqual(a, ejecutar())
        self.assertTrue(any(e["tipo"] == "decision_ia" for e in a["eventos"]))
        self.assertEqual(encuentro.estado()["perfil_ia"]["cerebro"], "comandante")

    def test_huida_tablero_y_bloqueo(self):
        party = preparacion_ofensiva()
        campo = Tablero.inicial([s.personaje_id for s in party], "guardian_verdugo").plan()
        combate = CombatResolver(party, Encuentro(perfil_ia=PerfilIA(tags=("cobarde",))), tablero=campo)
        origen = combate.tablero.posiciones[combate.jefe.id]
        combate.jefe.hp = combate.jefe.hp_max * .2
        combate._accion_jefe()
        destino = combate.tablero.posiciones[combate.jefe.id]
        self.assertGreater(min(distancia(destino, combate.tablero.posiciones[a.id]) for a in combate.party),
                           min(distancia(origen, combate.tablero.posiciones[a.id]) for a in combate.party))
        self.assertFalse(any(e.tipo == "accion" for e in combate.log.eventos))
        combate.jefe.estados["inmovilizado"] = {"vence": 10}
        combate._accion_jefe()
        self.assertEqual(destino, combate.tablero.posiciones[combate.jefe.id])


if __name__ == "__main__":
    unittest.main()
