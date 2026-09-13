"""Bucle de preparación/reintento compartido por HTTP y pruebas sin UI."""

from dataclasses import asdict
from threading import RLock

from item_factory import item_factory
from tactical_combat import CombatResolver
from tactical_models import ARMAS, BUILDS, PRIORIDADES, ROSTER, BuildManager, Encuentro, Seleccion, preparacion_ofensiva
from character_roster import MENSAJE_BLOQUEO
from progression import CLASES
from tactical_board import Tablero, TERRENOS, MANIOBRAS
from tactical_scenarios import ESCENARIOS, crear_encuentro, crear_tablero


class PrototypeController:
    def __init__(self, encuentro=None, roster=None):
        self.roster = roster
        self.lock = RLock()
        self.escenario_id = "guardian_patio" if encuentro and not encuentro.grupo else "patrulla_ruinas"
        self.encuentro = encuentro or crear_encuentro(self.escenario_id)
        self.selecciones = preparacion_ofensiva() if roster is None else []
        self.combate = None
        self.fase = "preparacion"
        self.intentos = 0
        self.tablero = None

    def _datos_roster(self):
        return self.roster.personajes if self.roster is not None else None

    def _exigir_roster(self):
        if self.roster is not None and not self.roster.tactico_disponible:
            raise ValueError(MENSAJE_BLOQUEO)

    def _sincronizar(self):
        if self.fase != "preparacion":
            return
        if self.roster is not None:
            datos = self.roster.personajes
            if len(datos) < 3:
                self.selecciones = []
            else:
                try:
                    BuildManager.validar(self.selecciones, datos)
                except ValueError:
                    self.selecciones = [Seleccion(d["id"], arma=d["arma_equipada"]) for d in datos[:3]]
        ids = [s.personaje_id for s in self.selecciones]
        if self.tablero is None or self.tablero.aliados != set(ids):
            self.tablero = crear_tablero(self.escenario_id, ids, self.encuentro.ids_enemigos)

    def preparar(self, datos):
        with self.lock:
            self._exigir_roster()
            if self.fase != "preparacion":
                raise ValueError("Vuelve a preparación antes de cambiar el equipo.")
            if not isinstance(datos, list) or not 3 <= len(datos) <= 6:
                raise ValueError("El grupo debe contener entre 3 y 6 selecciones.")
            try:
                selecciones = [Seleccion(**d) for d in datos]
                if any(not isinstance(v, str) for s in selecciones for v in asdict(s).values()):
                    raise ValueError("Las selecciones deben usar identificadores de texto.")
                BuildManager.validar(selecciones, self._datos_roster())
                if any(s.maniobra != "ninguna" for s in selecciones):
                    raise ValueError("Las maniobras proceden de habilidades del personaje, no del despliegue.")
            except (TypeError, KeyError) as error:
                raise ValueError("Selección de party no válida.") from error
            # Validación completa antes de publicar la nueva configuración.
            self._sincronizar()
            ids = [s.personaje_id for s in selecciones]
            plan = self.tablero.plan()
            anteriores = [s.personaje_id for s in self.selecciones]
            posiciones = {k: plan["posiciones"][k] for k in ids if k in plan["posiciones"]}
            libres = [plan["posiciones"][k] for k in anteriores if k not in ids]
            for k in ids:
                if k not in posiciones:
                    posiciones[k] = libres.pop(0) if libres else next(
                        [x, y] for y in range(8) for x in range(3) if [x, y] not in posiciones.values())
            plan["posiciones"] = {**posiciones, **{id: plan["posiciones"][id] for id in self.encuentro.ids_enemigos}}
            tablero = Tablero(plan, ids, self.encuentro.ids_enemigos)
            self.selecciones, self.tablero = selecciones, tablero
            return self.estado()

    def configurar_campo(self, datos):
        with self.lock:
            self._exigir_roster()
            if self.fase != "preparacion":
                raise ValueError("El campo solo se puede editar antes de iniciar el combate.")
            self._sincronizar()
            tablero = Tablero(datos, [s.personaje_id for s in self.selecciones], self.encuentro.ids_enemigos)
            if tablero.celdas != self.tablero.celdas or any(
                    tablero.posiciones[id] != self.tablero.posiciones[id] for id in self.encuentro.ids_enemigos):
                raise ValueError("El terreno y el despliegue enemigo están fijados por el escenario.")
            self.tablero = tablero
            return self.estado()

    def seleccionar_escenario(self, escenario_id):
        with self.lock:
            if self.fase != "preparacion":
                raise ValueError("Termina el combate y vuelve a preparación para cambiar de escenario.")
            if not isinstance(escenario_id, str) or escenario_id not in ESCENARIOS:
                raise ValueError("Escenario desconocido")
            encuentro = crear_encuentro(escenario_id)
            self._sincronizar()
            tablero = crear_tablero(escenario_id, [s.personaje_id for s in self.selecciones], encuentro.ids_enemigos)
            for id in tablero.aliados:
                tablero.posiciones[id] = self.tablero.posiciones[id]
            self.encuentro, self.tablero, self.escenario_id = encuentro, tablero, escenario_id
            return self.estado()

    def iniciar(self, seed=1234):
        with self.lock:
            self._exigir_roster()
            self._sincronizar()
            if self.fase != "preparacion":
                raise ValueError("El combate solo puede iniciarse desde preparación.")
            if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
                raise ValueError("La semilla debe ser un entero entre 0 y 4294967295.")
            self.combate = CombatResolver(self.selecciones, self.encuentro, seed, self._datos_roster(), self.tablero.plan())
            self.fase = "combate"
            self.intentos += 1
            return self.estado()

    def avanzar(self):
        with self.lock:
            if self.fase != "combate":
                raise ValueError("No hay un combate activo.")
            self.combate.paso()
            if self.combate.resultado:
                self.fase = "resultado"
            return self.estado()

    def reajustar(self):
        with self.lock:
            if self.fase == "combate":
                raise ValueError("Espera al resultado para cambiar la preparación.")
            self.combate = None
            self.fase = "preparacion"
            return self.estado()

    def estado(self):
        with self.lock:
            self._sincronizar()
            disponible = self.roster is None or self.roster.tactico_disponible
            personajes = ROSTER if self.roster is None else {
                d["id"]: {**d, "rol": CLASES.get(d["clase"], {}).get("nombre", "Sin clase"),
                          "descripcion": f"Nivel {d['nivel']} · " + CLASES.get(d["clase"], {}).get("nombre", "Sin clase"),
                          "armas": [i["id"] for i in d["inventario"] if i["id"] in ARMAS]}
                for d in self.roster.personajes}
            resultado = self.combate.resumen() if self.fase == "resultado" else None
            if resultado:
                # El log completo ya viaja en eventos; no duplicar todas las rondas en HTTP.
                resultado = {k: v for k, v in resultado.items() if k not in ("frames", "eventos")}
            return {"fase": self.fase, "intentos": self.intentos,
                    "escenario_id": self.escenario_id, "mapa": ESCENARIOS[self.escenario_id]["mapa"],
                    "tablero": self.combate.tablero.estado() if self.combate else self.tablero.estado(),
                    "reproduccion": self.combate.vistas if self.combate else [],
                    "tactico_disponible": disponible, "mensaje_bloqueo": "" if disponible else MENSAJE_BLOQUEO,
                    "selecciones": [asdict(s) for s in self.selecciones],
                    "party": ([a.estado() for a in (self.combate.party if self.combate else BuildManager.crear_party(self.selecciones, self._datos_roster()))] if disponible else []),
                    "combate": self.combate.estado() if self.combate else None,
                    "eventos": self.combate.log.serializar() if self.combate else [],
                    "resultado": resultado,
                    "catalogo": {"personajes": personajes, "builds": BUILDS, "prioridades": PRIORIDADES,
                                 "terrenos": TERRENOS, "maniobras": MANIOBRAS,
                                 "escenarios": {k: {f: v[f] for f in ("nombre", "mapa", "descripcion")} for k, v in ESCENARIOS.items()},
                                 "armas": {k: {**v, "nombre": item_factory.crear(k).nombre} for k, v in ARMAS.items()}},
                    "encuentro": self.encuentro.estado()}
