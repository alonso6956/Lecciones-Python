from dataclasses import dataclass

from combat_formulas import calcular_evasion, calcular_velocidad
from items import calcular_factor_arma, objetos


RAZAS = {
    "Goblin": {"base": 1, "oro": (3, 5), "exp": 10},
    "Esqueleto": {"base": 2, "oro": (5, 10), "exp": 15},
    "Bandido": {"base": 3, "oro": (8, 13), "exp": 20},
    "Orco": {"base": 4, "oro": (10, 15), "exp": 30},
    "Troll": {"base": 5, "oro": (15, 22), "exp": 40},
}

ARQUETIPOS = {
    "Rogue": {
        "bonus": "destreza",
        "arma": "Dagas de hierro",
    },
    "Guerrero": {
        "bonus": "constitucion",
        "arma": "Espada y escudo de hierro",
    },
    "Bárbaro": {
        "bonus": "fuerza",
        "arma": "Maza de hierro",
    },
}

SPAWN_POR_HABITACION = (
    (1, 9, {"Goblin": 90, "Esqueleto": 10}),
    (10, 19, {"Goblin": 70, "Esqueleto": 20, "Bandido": 10}),
    (20, 29, {"Esqueleto": 50, "Bandido": 30, "Orco": 20}),
    (30, 39, {"Bandido": 50, "Orco": 30, "Troll": 20}),
    (40, 49, {"Orco": 60, "Troll": 40}),
)


@dataclass
class Enemigo:
    VELOCIDAD_BASE = 10

    raza: str
    arquetipo: str
    fuerza: int
    destreza: int
    constitucion: int
    hp: int
    salud_maxima: int
    arma: str
    oro: tuple
    exp: int

    @property
    def nombre(self):
        return f"{self.raza} {self.arquetipo}"

    def calcular_dano_base(self):
        factor = calcular_factor_arma(self.arma, self.fuerza, self.destreza)
        return round(3 * factor)

    def calcular_defensa_base(self):
        """Los enemigos usan el mismo escalado controlado de CON."""
        return 1 + self.constitucion // 2

    @property
    def defensa_total(self):
        return self.calcular_defensa_base() + objetos["armas"][self.arma]["defensa"]

    @property
    def evasion(self):
        return calcular_evasion(self.destreza)

    @property
    def velocidad(self):
        return calcular_velocidad(self.VELOCIDAD_BASE, self.destreza)


def crear_enemigo(raza, arquetipo):
    datos_raza = RAZAS[raza]
    datos_arquetipo = ARQUETIPOS[arquetipo]
    if datos_arquetipo["arma"] not in objetos["armas"]:
        raise ValueError(
            f"El equipo {datos_arquetipo['arma']} de {arquetipo} no existe."
        )
    stats = {
        nombre: datos_raza["base"]
        for nombre in ("fuerza", "destreza", "constitucion")
    }
    stats[datos_arquetipo["bonus"]] += 1
    salud_maxima = round(18 * (1 + (stats["constitucion"] - 1) * 0.20))
    return Enemigo(
        raza=raza,
        arquetipo=arquetipo,
        hp=salud_maxima,
        salud_maxima=salud_maxima,
        arma=datos_arquetipo["arma"],
        oro=datos_raza["oro"],
        exp=datos_raza["exp"],
        **stats,
    )


def elegir_enemigo(numero_habitacion, rng):
    """Selecciona primero raza ponderada y luego arquetipo equiprobable."""
    for minimo, maximo, pesos_por_raza in SPAWN_POR_HABITACION:
        if minimo <= numero_habitacion <= maximo:
            razas = list(pesos_por_raza)
            raza = rng.choices(
                razas,
                weights=pesos_por_raza.values(),
                k=1,
            )[0]
            arquetipo = rng.choice(list(ARQUETIPOS))
            return crear_enemigo(raza, arquetipo)
    raise ValueError(f"No hay tabla de spawn para la habitación {numero_habitacion}")
