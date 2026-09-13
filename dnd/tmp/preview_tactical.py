import sys
from pathlib import Path
from dataclasses import replace
from tempfile import TemporaryDirectory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
original = config.cargar_configuracion
with TemporaryDirectory() as temp:
    config.cargar_configuracion = lambda: replace(original(), data_dir=Path(temp), request_logging=False)
    import server
    from tactical_controller import PrototypeController
    server.prototipo = PrototypeController()
    http = server.ServidorDungeon(('127.0.0.1', 8012), server.ManejadorDungeon)
    print('Preview http://127.0.0.1:8012/tactical.html', flush=True)
    http.serve_forever()
