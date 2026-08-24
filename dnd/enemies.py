from dataclasses import dataclass, field
from typing import Optional

from combat_formulas import calcular_evasion, calcular_velocidad
from habilidades import habilidad_factory
from item import Arma, Secundario
from item_factory import item_factory
from items import calcular_factor_arma


RAZAS = {
    "Goblin": {"base": 1, "oro": (3, 5), "exp": 10},
    "Esqueleto": {"base": 2, "oro": (5, 10), "exp": 15},
    "Bandido": {"base": 3, "oro": (8, 13), "exp": 20},
    "Orco": {"base": 4, "oro": (10, 15), "exp": 30},
    "Troll": {"base": 5, "oro": (15, 22), "exp": 40},
    "Guardián": {"base": 5, "oro": (30, 45), "exp": 100},
}

ARQUETIPOS = {
    "Rogue": {
        "bonificaciones": {"destreza": 1},
        "arma": "Dagas de hierro",
    },
    "Guerrero": {
        "bonificaciones": {"constitucion": 1},
        "arma": "Espada de hierro",
        "secundario": "Escudo de hierro",
    },
    "Bárbaro": {
        "bonificaciones": {"fuerza": 1},
        "arma": "Maza de hierro",
    },
    "Jefe": {
        "bonificaciones": {
            "fuerza": 5,
            "destreza": 0,
            "constitucion": 10,
        },
        "arma": "Morning Star",
        "habilidades": {
            "golpe_aplastante": 1,
        },
    },
}

ARQUETIPOS_COMUNES = ("Rogue", "Guerrero", "Bárbaro")

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
    secundario: Optional[str] = None
    habilidades: dict = field(default_factory=dict)
    cooldowns_habilidad: dict = field(default_factory=dict)
    efectos_habilidad: dict = field(default_factory=dict)
    sangrado_dano: int = 0
    sangrado_turnos: int = 0

    def __post_init__(self):
        for habilidad_id in self.habilidades:
            self.cooldowns_habilidad.setdefault(habilidad_id, 0)
            self.efectos_habilidad.setdefault(habilidad_id, 0)

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
        # Armas y escudos no aportan armadura; el escudo bloquea por separado.
        return self.calcular_defensa_base()

    @property
    def evasion(self):
        return calcular_evasion(self.destreza)

    @property
    def velocidad(self):
        return calcular_velocidad(self.VELOCIDAD_BASE, self.destreza)

    def nivel_habilidad(self, habilidad_id):
        return self.habilidades.get(habilidad_id, 0)

    def habilidad_activa(self, habilidad_id):
        return self.efectos_habilidad.get(habilidad_id, 0) > 0

    @property
    def mitigar_dano_activo(self):
        return self.habilidad_activa("mitigar_dano")

    @property
    def mitigar_dano_turnos(self):
        return self.efectos_habilidad.get("mitigar_dano", 0)

    def puede_usar_habilidad(self, habilidad_id):
        if self.nivel_habilidad(habilidad_id) < 1:
            return False
        habilidad = habilidad_factory.crear(habilidad_id)
        arma = item_factory.crear(self.arma)
        secundario = item_factory.crear(self.secundario) if self.secundario else None
        tipos = set()
        if isinstance(arma, Arma):
            tipos.add(arma.tipo_arma)
        if isinstance(secundario, Secundario):
            tipos.add(secundario.tipo_secundario)
        return habilidad.tipo_arma_requerida in tipos

    def reduccion_dano_activa(self):
        mayor = 0
        for habilidad_id, turnos in self.efectos_habilidad.items():
            if turnos <= 0:
                continue
            habilidad = habilidad_factory.crear(habilidad_id)
            if habilidad.tipo_efecto == "reduccion_dano":
                valor = getattr(self, habilidad.atributo_escalado)
                escudo = (
                    item_factory.crear(self.secundario)
                    if self.secundario
                    else None
                )
                mayor = max(
                    mayor,
                    habilidad.calcular_efecto(
                        self.nivel_habilidad(habilidad_id), valor, escudo
                    ),
                )
        return mayor


def crear_enemigo(raza, arquetipo):
    datos_raza = RAZAS[raza]
    datos_arquetipo = ARQUETIPOS[arquetipo]
    arma = item_factory.crear(datos_arquetipo["arma"])
    if not isinstance(arma, Arma):
        raise ValueError(f"El arma de {arquetipo} no existe.")
    secundario_nombre = datos_arquetipo.get("secundario")
    if secundario_nombre:
        secundario = item_factory.crear(secundario_nombre)
        if not isinstance(secundario, Secundario):
            raise ValueError(f"El secundario de {arquetipo} no existe.")

    stats = {
        nombre: datos_raza["base"]
        for nombre in ("fuerza", "destreza", "constitucion")
    }
    for estadistica, bonus in datos_arquetipo["bonificaciones"].items():
        stats[estadistica] += bonus
    salud_maxima = round(30 * (1 + (stats["constitucion"] - 1) * 0.20))
    return Enemigo(
        raza=raza,
        arquetipo=arquetipo,
        hp=salud_maxima,
        salud_maxima=salud_maxima,
        arma=arma.nombre,
        secundario=secundario_nombre,
        habilidades=dict(datos_arquetipo.get("habilidades", {})),
        oro=datos_raza["oro"],
        exp=datos_raza["exp"],
        **stats,
    )


def elegir_enemigo(numero_habitacion, rng):
    """La habitación 50 siempre contiene al primer jefe."""
    if numero_habitacion == 50:
        return crear_enemigo("Guardián", "Jefe")
    for minimo, maximo, pesos_por_raza in SPAWN_POR_HABITACION:
        if minimo <= numero_habitacion <= maximo:
            razas = list(pesos_por_raza)
            raza = rng.choices(
                razas,
                weights=pesos_por_raza.values(),
                k=1,
            )[0]
            arquetipo = rng.choice(ARQUETIPOS_COMUNES)
            return crear_enemigo(raza, arquetipo)
    raise ValueError(f"No hay tabla de spawn para la habitación {numero_habitacion}")
