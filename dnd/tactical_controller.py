"""Bucle de preparación/reintento compartido por HTTP y pruebas sin UI."""

from dataclasses import asdict
from threading import RLock

from item_factory import item_factory
from tactical_combat import CombatResolver
from tactical_models import ARMAS, BUILDS, PRIORIDADES, ROSTER, BuildManager, Encuentro, Seleccion, preparacion_ofensiva
from character_roster import MENSAJE_BLOQUEO
from progression import CLASES


class PrototypeController:
    def __init__(self, encuentro=None, roster=None):
        self.roster = roster
        self.lock = RLock()
        self.encuentro = encuentro or Encuentro()
        self.selecciones = preparacion_ofensiva() if roster is None else []
        self.combate = None
        self.fase = "preparacion"
        self.intentos = 0

    def _datos_roster(self):
        return self.roster.personajes if self.roster is not None else None

    def _exigir_roster(self):
        if self.roster is not None and not self.roster.tactico_disponible:
            raise ValueError(MENSAJE_BLOQUEO)

    def _sincronizar(self):
        if self.roster is None or self.fase != "preparacion":
            return
        datos = self.roster.personajes
        if len(datos) < 3:
            self.selecciones = []
            return
        try:
            BuildManager.validar(self.selecciones, datos)
        except ValueError:
            self.selecciones = [Seleccion(d["id"], arma=d["arma_equipada"]) for d in datos[:3]]

    def preparar(self, datos):
        with self.lock:
            self._exigir_roster()
            if self.fase != "preparacion":
                raise ValueError("Vuelve a preparación antes de cambiar el equipo.")
            if not isinstance(datos, list) or len(datos) != 3:
                raise ValueError("La party debe contener tres selecciones.")
            try:
                selecciones = [Seleccion(**d) for d in datos]
                if any(not isinstance(v, str) for s in selecciones for v in asdict(s).values()):
                    raise ValueError("Las selecciones deben usar identificadores de texto.")
                BuildManager.validar(selecciones, self._datos_roster())
            except (TypeError, KeyError) as error:
                raise ValueError("Selección de party no válida.") from error
            # Validación completa antes de publicar la nueva configuración.
            self.selecciones = selecciones
            return self.estado()

    def iniciar(self, seed=1234):
        with self.lock:
            self._exigir_roster()
            self._sincronizar()
            if self.fase != "preparacion":
                raise ValueError("El combate solo puede iniciarse desde preparación.")
            if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
                raise ValueError("La semilla debe ser un entero entre 0 y 4294967295.")
            self.combate = CombatResolver(self.selecciones, self.encuentro, seed, self._datos_roster())
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
                    "tactico_disponible": disponible, "mensaje_bloqueo": "" if disponible else MENSAJE_BLOQUEO,
                    "selecciones": [asdict(s) for s in self.selecciones],
                    "party": ([a.estado() for a in (self.combate.party if self.combate else BuildManager.crear_party(self.selecciones, self._datos_roster()))] if disponible else []),
                    "combate": self.combate.estado() if self.combate else None,
                    "eventos": self.combate.log.serializar() if self.combate else [],
                    "resultado": resultado,
                    "catalogo": {"personajes": personajes, "builds": BUILDS, "prioridades": PRIORIDADES,
                                 "armas": {k: {**v, "nombre": item_factory.crear(k).nombre} for k, v in ARMAS.items()}},
                    "encuentro": self.encuentro.estado()}
