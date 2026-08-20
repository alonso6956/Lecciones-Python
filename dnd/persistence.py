import hashlib
import json
import os
import shutil
from pathlib import Path


SAVE_VERSION = 1


class ErrorGuardado(ValueError):
    pass


class GestorGuardado:
    """Persistencia JSON con checksum, backup y reemplazo atómico."""

    def __init__(self, directorio):
        self.directorio = Path(directorio)
        self.ruta = self.directorio / "save.json"
        self.respaldo = self.directorio / "save.backup.json"

    @staticmethod
    def _serializar(datos):
        return json.dumps(
            datos,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def existe(self):
        return self.ruta.is_file() or self.respaldo.is_file()

    def guardar(self, estado):
        self.directorio.mkdir(parents=True, exist_ok=True)
        contenido = {"version": SAVE_VERSION, "state": estado}
        contenido["checksum"] = hashlib.sha256(
            self._serializar(contenido).encode("utf-8")
        ).hexdigest()
        temporal = self.ruta.with_suffix(".tmp")

        try:
            with temporal.open("w", encoding="utf-8") as archivo:
                json.dump(contenido, archivo, ensure_ascii=False, indent=2)
                archivo.flush()
                os.fsync(archivo.fileno())
            if self.ruta.exists():
                shutil.copy2(self.ruta, self.respaldo)
            os.replace(temporal, self.ruta)
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
            if not isinstance(contenido.get("state"), dict):
                raise ErrorGuardado("El guardado no contiene un estado válido.")
            return contenido["state"]
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
            raise ErrorGuardado("El archivo de guardado está dañado.") from error

    def cargar(self):
        errores = []
        for ruta in (self.ruta, self.respaldo):
            if not ruta.exists():
                continue
            try:
                return self._leer(ruta)
            except ErrorGuardado as error:
                errores.append(error)
        if errores:
            raise errores[0]
        raise ErrorGuardado("No existe una partida guardada.")
