"""Bucle de preparación/reintento compartido por HTTP y pruebas sin UI."""

from dataclasses import asdict
from threading import RLock

from item_factory import item_factory
from tactical_combat import CombatResolver
from tactical_models import ARMAS, BUILDS, PRIORIDADES, ROSTER, BuildManager, Encuentro, Seleccion, preparacion_ofensiva


class PrototypeController:
    def __init__(self, encuentro=None):
        self.lock = RLock()
        self.encuentro = encuentro or Encuentro()
        self.selecciones = preparacion_ofensiva()
        self.combate = None
        self.fase = "preparacion"
        self.intentos = 0

    def preparar(self, datos):
        with self.lock:
            if self.fase != "preparacion":
                raise ValueError("Vuelve a preparación antes de cambiar el equipo.")
            if not isinstance(datos, list) or len(datos) != 3:
                raise ValueError("La party debe contener tres selecciones.")
            try:
                selecciones = [Seleccion(**d) for d in datos]
                if any(not isinstance(v, str) for s in selecciones for v in asdict(s).values()):
                    raise ValueError("Las selecciones deben usar identificadores de texto.")
                BuildManager.validar(selecciones)
            except (TypeError, KeyError) as error:
                raise ValueError("Selección de party no válida.") from error
            # Validación completa antes de publicar la nueva configuración.
            self.selecciones = selecciones
            return self.estado()

    def iniciar(self, seed=1234):
        with self.lock:
            if self.fase != "preparacion":
                raise ValueError("El combate solo puede iniciarse desde preparación.")
            if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
                raise ValueError("La semilla debe ser un entero entre 0 y 4294967295.")
            self.combate = CombatResolver(self.selecciones, self.encuentro, seed)
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
            resultado = self.combate.resumen() if self.fase == "resultado" else None
            if resultado:
                # El log completo ya viaja en eventos; no duplicar todas las rondas en HTTP.
                resultado = {k: v for k, v in resultado.items() if k not in ("frames", "eventos")}
            return {"fase": self.fase, "intentos": self.intentos,
                    "selecciones": [asdict(s) for s in self.selecciones],
                    "party": [a.estado() for a in BuildManager.crear_party(self.selecciones)],
                    "combate": self.combate.estado() if self.combate else None,
                    "eventos": self.combate.log.serializar() if self.combate else [],
                    "resultado": resultado,
                    "catalogo": {"personajes": ROSTER, "builds": BUILDS, "prioridades": PRIORIDADES,
                                 "armas": {k: {**v, "nombre": item_factory.crear(k).nombre} for k, v in ARMAS.items()}},
                    "encuentro": asdict(self.encuentro)}
