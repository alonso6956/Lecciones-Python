"""Tablero táctico: preparación validada, rutas y efectos espaciales."""

from copy import deepcopy
from heapq import heappop, heappush

ANCHO, ALTO = 10, 8
TERRENOS = {
    "suelo": {"nombre": "Suelo", "limite": 80, "descripcion": "Movimiento normal. Borra el terreno de una casilla."},
    "muro": {"nombre": "Obstáculo", "limite": 10, "descripcion": "Bloquea movimiento y línea de visión. Solo en columnas D–G."},
    "cobertura": {"nombre": "Cobertura", "limite": 8, "descripcion": "Recibes un 20 % menos de daño directo en esta casilla."},
    "altura": {"nombre": "Elevación", "limite": 6, "descripcion": "Cuesta 2 puntos entrar. +15 % de daño al atacar suelo bajo; −15 % al atacar hacia arriba."},
    "barro": {"nombre": "Barro", "limite": 8, "descripcion": "Cuesta 2 puntos de movimiento entrar."},
    "trampa_aliada": {"nombre": "Trampa aliada", "limite": 3, "descripcion": "Solo D–G. Inflige 12 de daño al rival y detiene su movimiento; se consume."},
    "trampa_rival": {"nombre": "Trampa rival", "limite": 3, "descripcion": "Solo D–G. Inflige 12 de daño a un aliado y detiene su movimiento; se consume."},
}
MANIOBRAS = {
    "ninguna": {"nombre": "Sin maniobra", "descripcion": "Dedica sus acciones a moverse y combatir."},
    "humo": {"nombre": "Cortina de humo", "descripcion": "Una vez por combate: crea humo a radio 1 durante 2 rondas completas. Reduce el daño directo recibido un 25 %. Consume la acción."},
    "cobertura": {"nombre": "Fortificar posición", "descripcion": "Una vez por combate: convierte su casilla en cobertura. Consume la acción."},
    "trampa": {"nombre": "Tender trampa", "descripcion": "Una vez por combate: coloca una trampa a un máximo de 3 casillas, cerca del rival. Inflige 12 de daño y detiene al rival al pisarla. Consume la acción."},
}


def distancia(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class Tablero:
    def __init__(self, datos, aliados, jefe_id):
        self.aliados = set(aliados)
        self.jefe_id = jefe_id
        self.enemigos = {jefe_id} if isinstance(jefe_id, str) else set(jefe_id)
        if not isinstance(datos, dict) or set(datos) != {"posiciones", "celdas"}:
            raise ValueError("El tablero debe contener posiciones y celdas.")
        posiciones = datos["posiciones"]
        if not isinstance(posiciones, dict) or set(posiciones) != self.aliados | self.enemigos:
            raise ValueError("Coloca a todos los personajes elegidos y al guardián.")
        self.posiciones = {k: self.coordenada(v) for k, v in posiciones.items()}
        if len(set(self.posiciones.values())) != len(self.posiciones):
            raise ValueError("Dos personajes no pueden ocupar la misma casilla.")
        if any(p[0] > 2 for k, p in self.posiciones.items() if k in self.aliados):
            raise ValueError("Despliega a tus personajes en las columnas A–C.")
        if any(self.posiciones[id][0] < 7 for id in self.enemigos):
            raise ValueError("Despliega al guardián en las columnas H–J.")
        self.celdas = {}
        self.efectos = {}
        if not isinstance(datos["celdas"], list) or len(datos["celdas"]) > 38:
            raise ValueError("Demasiadas casillas de terreno.")
        cuentas = {}
        for celda in datos["celdas"]:
            if not isinstance(celda, dict) or set(celda) != {"x", "y", "tipo"}:
                raise ValueError("Casilla de terreno inválida.")
            punto = self.coordenada([celda["x"], celda["y"]])
            tipo = celda["tipo"]
            if not isinstance(tipo, str) or tipo not in TERRENOS or punto in self.celdas:
                raise ValueError("Tipo de terreno inválido o casilla repetida.")
            if tipo == "suelo":
                raise ValueError("Omite las casillas de suelo del plano.")
            if (tipo == "muro" or tipo.startswith("trampa")) and not 3 <= punto[0] <= 6:
                raise ValueError("Los obstáculos y trampas iniciales solo van en las columnas D–G.")
            cuentas[tipo] = cuentas.get(tipo, 0) + 1
            if cuentas[tipo] > TERRENOS[tipo]["limite"]:
                raise ValueError(f"Límite de {TERRENOS[tipo]['nombre']}: {TERRENOS[tipo]['limite']}.")
            self.celdas[punto] = tipo
        if any(self.terreno(p) == "muro" for p in self.posiciones.values()):
            raise ValueError("No puedes desplegar sobre un obstáculo.")
        # Comprueba conectividad sin unidades: evita arenas cerradas al editar.
        for aliado in self.aliados:
            if any(self.ruta(aliado, self.posiciones[id], 1, set()) is None for id in self.enemigos):
                raise ValueError("El terreno debe dejar una ruta al guardián para cada personaje.")

    @staticmethod
    def coordenada(valor):
        if not isinstance(valor, (list, tuple)) or len(valor) != 2 or any(type(v) is not int for v in valor):
            raise ValueError("Las coordenadas deben ser dos enteros.")
        x, y = valor
        if not 0 <= x < ANCHO or not 0 <= y < ALTO:
            raise ValueError("La casilla está fuera del tablero.")
        return x, y

    @classmethod
    def inicial(cls, aliados, jefe_id):
        return cls({"posiciones": {**{k: [1 + i % 2, 1 + i] for i, k in enumerate(aliados)}, jefe_id: [8, 3]},
                    "celdas": [{"x": 4, "y": 2, "tipo": "muro"}, {"x": 5, "y": 5, "tipo": "muro"},
                               {"x": 2, "y": 2, "tipo": "cobertura"}, {"x": 3, "y": 5, "tipo": "altura"},
                               {"x": 6, "y": 3, "tipo": "barro"}]}, aliados, jefe_id)

    def plan(self):
        return {"posiciones": {k: list(v) for k, v in self.posiciones.items()},
                "celdas": [{"x": p[0], "y": p[1], "tipo": t} for p, t in sorted(self.celdas.items())]}

    def estado(self):
        return {**self.plan(), "ancho": ANCHO, "alto": ALTO,
                "efectos": [{"x": p[0], "y": p[1], **deepcopy(e)} for p, e in sorted(self.efectos.items())]}

    def terreno(self, punto):
        return self.celdas.get(tuple(punto), "suelo")

    def vecinos(self, punto):
        x, y = punto
        return [(a, b) for a, b in ((x + 1, y), (x, y + 1), (x, y - 1), (x - 1, y))
                if 0 <= a < ANCHO and 0 <= b < ALTO and self.terreno((a, b)) != "muro"]

    def coste(self, punto):
        return 2 if self.terreno(punto) in {"barro", "altura"} else 1

    def visible(self, origen, destino):
        # Supercover: un segmento no atraviesa muros ni esquinas cerradas.
        x, y = origen
        dx, dy = destino[0] - x, destino[1] - y
        nx, ny = abs(dx), abs(dy)
        sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
        ix = iy = 0
        while ix < nx or iy < ny:
            lhs, rhs = (1 + 2 * ix) * ny, (1 + 2 * iy) * nx
            if lhs == rhs:
                if self.terreno((x + sx, y)) == "muro" or self.terreno((x, y + sy)) == "muro":
                    return False
                x += sx; y += sy; ix += 1; iy += 1
            elif lhs < rhs:
                x += sx; ix += 1
            else:
                y += sy; iy += 1
            if self.terreno((x, y)) == "muro":
                return False
        return True

    def en_alcance(self, origen, destino, alcance):
        return distancia(origen, destino) <= alcance and self.visible(origen, destino)

    def ruta(self, actor_id, destino, alcance, ocupados):
        origen = self.posiciones[actor_id]
        pendientes = [(0, origen)]
        costes, padres = {origen: 0}, {}
        while pendientes:
            coste, punto = heappop(pendientes)
            if coste != costes[punto]:
                continue
            if self.en_alcance(punto, destino, alcance):
                ruta = []
                while punto != origen:
                    ruta.append(punto)
                    punto = padres[punto]
                return ruta[::-1]
            for siguiente in self.vecinos(punto):
                if siguiente in ocupados or siguiente == destino:
                    continue
                nuevo = coste + self.coste(siguiente)
                if nuevo < costes.get(siguiente, float("inf")):
                    costes[siguiente], padres[siguiente] = nuevo, punto
                    heappush(pendientes, (nuevo, siguiente))
        return None

    def multiplicador(self, actor_id, objetivo_id, vivos):
        origen, destino = self.posiciones[actor_id], self.posiciones[objetivo_id]
        altura = int(self.terreno(origen) == "altura") - int(self.terreno(destino) == "altura")
        factor = 1 + altura * .15
        razones = ["altura"] if altura else []
        if self.terreno(destino) == "cobertura":
            factor *= .8
            razones.append("cobertura")
        if self.efectos.get(destino, {}).get("tipo") == "humo":
            factor *= .75
            razones.append("humo")
        equipo = self.aliados if actor_id in self.aliados else self.enemigos
        if distancia(origen, destino) == 1:
            opuesta = (2 * destino[0] - origen[0], 2 * destino[1] - origen[1])
            if any(k != actor_id and k in vivos and self.posiciones[k] == opuesta for k in equipo):
                factor *= 1.15
                razones.append("flanqueo")
        return factor, razones

    def expirar(self, ronda):
        self.efectos = {p: e for p, e in self.efectos.items() if e["vence"] > ronda}
