import json
import logging
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from config import cargar_configuracion
from game_engine import ErrorJuego, MotorJuego
from persistence import ErrorGuardado, GestorGuardado


configuracion = cargar_configuracion()
gestor_guardado = GestorGuardado(configuracion.data_dir)
motor = MotorJuego()
servidor_activo = None
UI_VERSION = "14"


def configurar_logging():
    nivel = logging.DEBUG if configuracion.debug else logging.ERROR
    logging.basicConfig(
        filename=configuracion.data_dir / "dungeon.log",
        level=nivel,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )


def mostrar_error_fatal():
    """Informa el fallo sin consola ni stack trace en la build windowed."""
    if sys.platform != "win32" or configuracion.debug:
        return
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            0,
            "Dungeon no pudo iniciarse. Revisa dungeon.log en AppData Local.",
            "Dungeon",
            0x10,
        )
    except Exception:
        pass


class ServidorDungeon(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class ManejadorDungeon(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(configuracion.web_dir), **kwargs)

    def end_headers(self):
        """Evita que la UI reutilice HTML, CSS o JavaScript de otra versión."""
        if not urlparse(self.path).path.startswith("/api/"):
            self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def _estado(self):
        estado = motor.estado()
        estado["guardado_disponible"] = gestor_guardado.existe()
        estado["slots"] = gestor_guardado.listar_slots()
        estado["slot_activo"] = gestor_guardado.slot_activo
        estado["ui_version"] = UI_VERSION
        estado["entorno"] = configuracion.entorno
        return estado

    def _json(self, datos, codigo=200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _leer_json(self):
        longitud = int(self.headers.get("Content-Length", 0))
        if longitud > 16_384:
            raise ErrorJuego("La solicitud es demasiado grande.")
        return json.loads(self.rfile.read(longitud) or b"{}")

    def do_GET(self):
        if urlparse(self.path).path == "/api/estado":
            self._json(self._estado())
            return
        super().do_GET()

    def do_POST(self):
        ruta = urlparse(self.path).path
        try:
            datos = self._leer_json()
            guardar = False
            if ruta == "/api/nueva":
                gestor_guardado.desactivar_slot()
                motor.nueva_partida()
            elif ruta == "/api/cargar":
                motor.importar_guardado(gestor_guardado.cargar(datos.get("slot")))
            elif ruta == "/api/guardar":
                gestor_guardado.guardar(
                    datos.get("slot"),
                    motor.exportar_guardado(),
                )
            elif ruta == "/api/iniciar":
                motor.iniciar(datos.get("nombre", ""), datos.get("arma", ""))
                guardar = True
            elif ruta == "/api/accion":
                motor.actuar(
                    datos.get("accion", ""),
                    datos.get("habilidad"),
                )
                guardar = True
            elif ruta == "/api/nivel":
                motor.subir_nivel(datos.get("estadistica", ""))
                guardar = True
            elif ruta == "/api/comprar":
                motor.comprar(datos.get("categoria", ""), datos.get("nombre", ""))
                guardar = True
            elif ruta == "/api/mejorar-habilidad":
                motor.mejorar_habilidad(datos.get("habilidad", ""))
                guardar = True
            elif ruta == "/api/equipar":
                motor.equipar_item(datos.get("item", ""))
                guardar = True
            elif ruta == "/api/desequipar":
                motor.desequipar_item(datos.get("slot", ""))
                guardar = True
            elif ruta == "/api/usar-item":
                motor.usar_item(datos.get("item", ""))
                guardar = True
            elif ruta == "/api/continuar":
                motor.siguiente_habitacion()
                guardar = True
            elif ruta == "/api/respawn":
                motor.respawn()
                guardar = True
            elif ruta == "/api/reiniciar":
                motor.reiniciar()
                gestor_guardado.desactivar_slot()
            elif ruta == "/api/salir":
                self._json({"cerrando": True})
                threading.Thread(
                    target=self.server.shutdown,
                    daemon=True,
                ).start()
                return
            else:
                self._json({"error": "Ruta no encontrada."}, 404)
                return

            if guardar and gestor_guardado.slot_activo is not None:
                gestor_guardado.guardar(
                    gestor_guardado.slot_activo,
                    motor.exportar_guardado(),
                )
            self._json(self._estado())
        except (ErrorJuego, ErrorGuardado, ValueError, json.JSONDecodeError) as error:
            self._json({"error": str(error), "estado": self._estado()}, 400)
        except Exception:
            logging.exception("Error no controlado procesando %s", ruta)
            self._json(
                {
                    "error": "Se produjo un error interno. Reinicia o carga la partida.",
                    "estado": self._estado(),
                },
                500,
            )

    def log_message(self, formato, *args):
        if configuracion.request_logging:
            logging.info(formato, *args)


def ejecutar():
    global servidor_activo
    configurar_logging()
    url = f"http://{configuracion.host}:{configuracion.port}/?ui={UI_VERSION}"
    try:
        servidor_activo = ServidorDungeon(
            (configuracion.host, configuracion.port),
            ManejadorDungeon,
        )
        if configuracion.open_browser:
            threading.Timer(0.5, lambda: webbrowser.open(url)).start()
        servidor_activo.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception:
        logging.exception("Error fatal al iniciar Dungeon")
        mostrar_error_fatal()
        return 1
    finally:
        if servidor_activo:
            servidor_activo.server_close()
    return 0
