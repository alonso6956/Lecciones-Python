"""Servidor web local para Dungeon. Ejecuta: python3 test.py"""

import json
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from game_engine import ErrorJuego, MotorJuego

HOST = "127.0.0.1"
PORT = 8000
WEB_DIR = Path(__file__).with_name("web")
motor = MotorJuego()


class ManejadorDungeon(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def _json(self, datos, codigo=200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _leer_json(self):
        longitud = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(longitud) or b"{}")

    def do_GET(self):
        if urlparse(self.path).path == "/api/estado":
            self._json(motor.estado())
            return
        super().do_GET()

    def do_POST(self):
        ruta = urlparse(self.path).path
        try:
            datos = self._leer_json()
            if ruta == "/api/iniciar":
                motor.iniciar(datos.get("nombre", ""), datos.get("arma", ""))
            elif ruta == "/api/accion":
                motor.actuar(datos.get("accion", ""))
            elif ruta == "/api/nivel":
                motor.subir_nivel(datos.get("estadistica", ""))
            elif ruta == "/api/comprar":
                motor.comprar(datos.get("categoria", ""), datos.get("nombre", ""))
            elif ruta == "/api/continuar":
                motor.siguiente_habitacion()
            elif ruta == "/api/reiniciar":
                motor.reiniciar()
            else:
                self._json({"error": "Ruta no encontrada."}, 404)
                return
            self._json(motor.estado())
        except (ErrorJuego, ValueError, json.JSONDecodeError) as error:
            self._json({"error": str(error), "estado": motor.estado()}, 400)

    def log_message(self, formato, *args):
        if args and str(args[1]) != "200":
            super().log_message(formato, *args)


def ejecutar():
    servidor = ThreadingHTTPServer((HOST, PORT), ManejadorDungeon)
    url = f"http://{HOST}:{PORT}"
    print(f"Dungeon disponible en {url}")
    print("Presiona Ctrl+C para detener el servidor.")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    ejecutar()
