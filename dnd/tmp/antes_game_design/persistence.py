import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


SAVE_VERSION = 1


class ErrorGuardado(ValueError):
    pass


class GestorGuardado:
    """Persistencia de tres slots JSON con checksum y reemplazo atómico."""

    TOTAL_SLOTS = 3

    def __init__(self, directorio):
        self.directorio = Path(directorio)
        self.slot_activo = None

    def _validar_slot(self, slot):
        try:
            slot = int(slot)
        except (TypeError, ValueError) as error:
            raise ErrorGuardado("El slot seleccionado no es válido.") from error
        if not 1 <= slot <= self.TOTAL_SLOTS:
            raise ErrorGuardado("El slot seleccionado no es válido.")
        return slot

    def _rutas(self, slot):
        slot = self._validar_slot(slot)
        return (
            self.directorio / f"save_slot_{slot}.json",
            self.directorio / f"save_slot_{slot}.backup.json",
        )

    @staticmethod
    def _serializar(datos):
        return json.dumps(
            datos,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def existe(self, slot=None):
        slots = range(1, self.TOTAL_SLOTS + 1) if slot is None else (slot,)
        return any(any(ruta.is_file() for ruta in self._rutas(numero)) for numero in slots)

    @staticmethod
    def _crear_resumen(estado, fecha):
        jugador = estado.get("jugador") or {}
        return {
            "fecha": fecha,
            "personaje": str(jugador.get("nombre", "Aventurero")),
            "nivel": int(jugador.get("nivel", 1)),
            "habitacion": int(estado.get("numero_habitacion", 1)),
            "fase": str(estado.get("fase", "desconocida")),
        }

    def guardar(self, slot, estado):
        slot = self._validar_slot(slot)
        ruta, respaldo = self._rutas(slot)
        self.directorio.mkdir(parents=True, exist_ok=True)
        fecha = datetime.now(timezone.utc).isoformat(timespec="seconds")
        contenido = {
            "version": SAVE_VERSION,
            "active_slot": slot,
            "summary": self._crear_resumen(estado, fecha),
            "state": estado,
        }
        contenido["checksum"] = hashlib.sha256(
            self._serializar(contenido).encode("utf-8")
        ).hexdigest()
        temporal = ruta.with_suffix(".tmp")

        try:
            with temporal.open("w", encoding="utf-8") as archivo:
                json.dump(contenido, archivo, ensure_ascii=False, indent=2)
                archivo.flush()
                os.fsync(archivo.fileno())
            if ruta.exists():
                shutil.copy2(ruta, respaldo)
            os.replace(temporal, ruta)
            self.slot_activo = slot
        except OSError as error:
            temporal.unlink(missing_ok=True)
            raise ErrorGuardado("No se pudo guardar la partida.") from error

    def _leer(self, ruta):
        try:
            with ruta.open(encoding="utf-8") as archivo:
                contenido = json.load(archivo)
            checksum = contenido.pop("checksum")
            esperado = hashlib.sha256(
                self._serializar(contenido).encode("utf-8")
            ).hexdigest()
            if checksum != esperado or contenido.get("version") != SAVE_VERSION:
                raise ErrorGuardado("El archivo de guardado no es válido.")
            if (
                not isinstance(contenido.get("state"), dict)
                or not isinstance(contenido.get("summary"), dict)
            ):
                raise ErrorGuardado("El guardado no contiene un estado válido.")
            return contenido
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
            raise ErrorGuardado("El archivo de guardado está dañado.") from error

    def cargar(self, slot):
        slot = self._validar_slot(slot)
        errores = []
        for ruta in self._rutas(slot):
            if not ruta.exists():
                continue
            try:
                contenido = self._leer(ruta)
                self.slot_activo = slot
                return contenido["state"]
            except ErrorGuardado as error:
                errores.append(error)
        if errores:
            raise errores[0]
        raise ErrorGuardado(f"No existe una partida en el slot {slot}.")

    def listar_slots(self):
        slots = []
        for slot in range(1, self.TOTAL_SLOTS + 1):
            entrada = {"slot": slot, "ocupado": False, "resumen": None}
            for ruta in self._rutas(slot):
                if not ruta.exists():
                    continue
                try:
                    entrada.update(ocupado=True, resumen=self._leer(ruta)["summary"])
                    break
                except ErrorGuardado:
                    entrada["error"] = "Guardado dañado"
            slots.append(entrada)
        return slots

    def desactivar_slot(self):
        self.slot_activo = None
