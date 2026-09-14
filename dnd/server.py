import json
import logging
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from config import cargar_configuracion
from game_engine import ErrorJuego, MotorJuego
from persistence import ErrorGuardado
from character_roster import CharacterRoster, MENSAJE_BLOQUEO
from tactical_controller import PrototypeController
from workshop import Workshop
from shop import Shop


configuracion = cargar_configuracion()
roster = CharacterRoster(configuracion.data_dir)
motor = MotorJuego(roster=roster)
prototipo = PrototypeController(roster=roster)
estado_lock = threading.RLock()
servidor_activo = None
UI_VERSION = "25"


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
        estado["roster"] = roster.personajes
        estado["guardado_disponible"] = bool(roster.personajes)
        estado["slots"] = roster.listar_slots()
        estado["slot_activo"] = next((s["slot"] for s in estado["slots"] if motor.jugador and s["id"] == motor.jugador.id), None)
        estado["tactico_disponible"] = roster.tactico_disponible
        estado["mensaje_bloqueo_tactico"] = "" if roster.tactico_disponible else MENSAJE_BLOQUEO
        estado["avisos_roster"] = roster.avisos
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
        with estado_lock:
            self._get()

    def _get(self):
        if urlparse(self.path).path == "/api/taller/previsualizar":
            try:
                parametros = parse_qs(urlparse(self.path).query)
                seleccion = {k: parametros.get(k, [None])[0] for k in ("personaje_id", "tipo", "material", "componente")}
                if "componente" in parametros:
                    seleccion["componente"] = parametros["componente"]
                self._json(Workshop(roster).previsualizar(**seleccion))
            except ValueError as error:
                self._json({"error": str(error)}, 400)
            return
        if urlparse(self.path).path == "/api/tienda/estado":
            try:
                personaje_id = parse_qs(urlparse(self.path).query).get("personaje_id", [None])[0]
                estado = Shop(roster).estado(personaje_id)
                estado["disponible"] = motor.fase == "menu" and prototipo.fase != "combate"
                self._json(estado)
            except ValueError as error:
                self._json({"error": str(error)}, 400)
            return
        if urlparse(self.path).path == "/api/taller/estado":
            try:
                personaje_id = parse_qs(urlparse(self.path).query).get("personaje_id", [None])[0]
                estado = Workshop(roster).estado(personaje_id)
                estado["disponible"] = motor.fase == "menu" and prototipo.fase != "combate"
                self._json(estado)
            except ValueError as error:
                self._json({"error": str(error)}, 400)
            return
        if urlparse(self.path).path == "/api/tactico/estado":
            self._json(prototipo.estado())
            return
        if urlparse(self.path).path == "/api/estado":
            self._json(self._estado())
            return
        super().do_GET()

    def do_POST(self):
        with estado_lock:
            self._post()

    def _post(self):
        ruta = urlparse(self.path).path
        try:
            datos = self._leer_json()
            if not isinstance(datos, dict):
                raise ErrorJuego("Se esperaba un objeto JSON.")
            if ruta == "/api/tienda/vender":
                if motor.fase != "menu" or prototipo.fase == "combate":
                    raise ErrorJuego("La tienda solo está disponible desde el menú, fuera de los combates.")
                if any(k not in {"personaje_id", "instance_id", "cantidad"} for k in datos):
                    raise ErrorJuego("La solicitud de venta contiene campos no válidos.")
                estado = Shop(roster).vender(datos.get("personaje_id"), datos.get("instance_id"), datos.get("cantidad", 1))
                self._json({**estado, "disponible": True})
                return
            if ruta in {"/api/tienda/comprar", "/api/comprar"}:
                if motor.fase != "menu" or prototipo.fase == "combate":
                    raise ErrorJuego("La tienda solo está disponible desde el menú, fuera de los combates.")
                estado = motor.comprar(datos.get("categoria"), datos.get("nombre"),
                                       datos.get("personaje_id"), datos.get("cantidad", 1))
                self._json({**estado, "disponible": True})
                return
            if ruta.startswith("/api/taller/"):
                if motor.fase != "menu" or prototipo.fase == "combate":
                    raise ErrorJuego("Vuelve al menú y termina el combate táctico para usar el taller o vault.")
                personaje_id = datos.pop("personaje_id", None)
                if any(k not in {"tipo", "material", "componente", "instance_id", "cantidad", "item_id", "nombre", "slot"} for k in datos):
                    raise ErrorJuego("La solicitud de taller contiene campos no válidos.")
                self._json(Workshop(roster).ejecutar(ruta.rsplit("/", 1)[-1], personaje_id, **datos))
                return
            if ruta.startswith("/api/tactico/"):
                if ruta == "/api/tactico/preparar":
                    estado_tactico = prototipo.preparar(datos.get("selecciones"))
                elif ruta == "/api/tactico/escenario":
                    estado_tactico = prototipo.seleccionar_escenario(datos.get("escenario_id"))
                elif ruta == "/api/tactico/campo":
                    estado_tactico = prototipo.configurar_campo(datos.get("tablero"))
                elif ruta == "/api/tactico/iniciar":
                    estado_tactico = prototipo.iniciar(datos.get("seed", 1234))
                elif ruta == "/api/tactico/avanzar":
                    estado_tactico = prototipo.avanzar()
                elif ruta == "/api/tactico/reajustar":
                    estado_tactico = prototipo.reajustar()
                else:
                    self._json({"error": "Ruta no encontrada."}, 404)
                    return
                self._json(estado_tactico)
                return
            if ruta == "/api/nueva":
                if motor.fase not in {"menu", "inicio"}:
                    raise ErrorJuego("Vuelve al menú antes de crear otro personaje.")
                motor.nueva_partida()
            elif ruta == "/api/cargar":
                if motor.fase not in {"menu", "inicio"}:
                    raise ErrorJuego("Vuelve al menú antes de cargar otro personaje.")
                personaje_id = datos.get("id")
                if personaje_id is None:
                    slot = datos.get("slot")
                    if type(slot) is not int or not 1 <= slot <= len(roster.personajes):
                        raise ErrorJuego("Selecciona un personaje válido.")
                    personaje_id = roster.personajes[slot - 1]["id"]
                motor.cargar_personaje(personaje_id)
            elif ruta == "/api/descartar":
                if motor.fase != "menu":
                    raise ErrorJuego("Vuelve al menú antes de descartar personajes.")
                if prototipo.fase == "combate":
                    raise ErrorJuego("Termina el combate táctico antes de descartar personajes.")
                if datos.get("confirmado") is not True:
                    raise ErrorJuego("Confirma qué personaje quieres descartar.")
                roster.descartar(datos.get("id"))
                prototipo.reajustar()
            elif ruta == "/api/guardar":
                raise ErrorJuego("El progreso se guarda al avanzar de habitación, comprar en el menú o morir.")
            elif ruta == "/api/iniciar":
                motor.iniciar(datos.get("nombre", ""))
            elif ruta == "/api/accion":
                motor.actuar(
                    datos.get("accion", ""),
                    datos.get("habilidad"),
                )
            elif ruta == "/api/nivel":
                motor.subir_nivel(datos.get("estadistica", ""))
            elif ruta == "/api/clase":
                motor.elegir_clase(datos.get("clase", ""))
            elif ruta == "/api/mejorar-habilidad":
                motor.mejorar_habilidad(datos.get("habilidad", ""))
            elif ruta == "/api/equipar":
                motor.equipar_item(datos.get("item", ""), datos.get("slot"))
            elif ruta == "/api/desequipar":
                motor.desequipar_item(datos.get("slot", ""))
            elif ruta == "/api/usar-item":
                motor.usar_item(datos.get("item", ""))
            elif ruta == "/api/continuar":
                motor.siguiente_habitacion()
            elif ruta == "/api/respawn":
                motor.respawn()
            elif ruta == "/api/reiniciar":
                if motor.fase == "inicio":
                    motor.reiniciar()
                else:
                    motor.abandonar()
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
