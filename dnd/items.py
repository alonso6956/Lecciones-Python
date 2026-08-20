"""Catálogo de equipo y estrategias de escalado compartidas por entidades."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WeaponScalingStrategy:
    """Asocia cada tipo de arma con una única estadística ofensiva."""

    estadistica_principal: str
    crecimiento_por_punto: float = 0.10

    def factor(self, fuerza, destreza):
        estadisticas = {"fuerza": fuerza, "destreza": destreza}
        valor = estadisticas[self.estadistica_principal]
        return 1 + max(0, valor - 1) * self.crecimiento_por_punto


ESTRATEGIAS_ESCALADO = {
    "espada_escudo": WeaponScalingStrategy("fuerza"),
    "dagas": WeaponScalingStrategy("destreza"),
    "maza": WeaponScalingStrategy("fuerza"),
}

objetos = {
    "armas": {
        "Espada y escudo de hierro": {
            "tipo": "espada_escudo",
            "tier": 1,
            "inicial": True,
            "ataque": (2, 4),
            "defensa": 5,
            "precio": 50,
            "tecnica": "Bloqueo y contraataque",
            "tipo_tecnica": "constitucion",
            "descripcion_tecnica": (
                "escala con Fuerza; aumenta temporalmente la defensa"
            ),
        },
        "Dagas de hierro": {
            "tipo": "dagas",
            "tier": 1,
            "inicial": True,
            "ataque": (4, 8),
            "defensa": 2,
            "precio": 50,
            "tecnica": "Corte certero",
            "tipo_tecnica": "destreza",
            "descripcion_tecnica": (
                "escala con Destreza y puede esquivar"
            ),
        },
        "Maza de hierro": {
            "tipo": "maza",
            "tier": 1,
            "inicial": True,
            "ataque": (6, 13),
            "defensa": 1,
            "precio": 50,
            "tecnica": "Golpe aplastante",
            "tipo_tecnica": "fuerza",
            "descripcion_tecnica": "escala con Fuerza y puede aturdir",
        },
        "Morning Star": {
            "tipo": "maza",
            "tier": 3,
            "inicial": False,
            "ataque": (18, 27),
            "defensa": 4,
            "precio": 1,
            "tecnica": "Golpe aplastante",
            "tipo_tecnica": "fuerza",
            "descripcion_tecnica": "escala con Fuerza y puede aturdir",
        },
        "Estoque de acero": {
            "tipo": "dagas",
            "tier": 3,
            "inicial": False,
            "ataque": (10, 14),
            "defensa": 8,
            "precio": 1,
            "tecnica": "Corte certero",
            "tipo_tecnica": "destreza",
            "descripcion_tecnica": (
                "escala con Destreza y puede esquivar"
            ),
        },
    },
    "pociones": {
        "Pocion pequeña": {"salud": 5, "precio": 10},
        "Pocion mediana": {"salud": 15, "precio": 25},
        "Pocion grande": {"salud": 30, "precio": 50},
        "Pocion extra grande": {"salud": 50, "precio": 70},
    },
}


def obtener_estrategia_arma(nombre_arma):
    tipo = objetos["armas"][nombre_arma]["tipo"]
    return ESTRATEGIAS_ESCALADO[tipo]


def calcular_factor_arma(nombre_arma, fuerza, destreza):
    return obtener_estrategia_arma(nombre_arma).factor(fuerza, destreza)


def obtener_dano_arma(nombre_arma, rng):
    """Devuelve únicamente el daño fijo variable definido por el arma."""
    return rng.randint(*objetos["armas"][nombre_arma]["ataque"])


def obtener_defensa_arma(nombre_arma):
    """Devuelve únicamente la defensa fija definida por el arma."""
    return objetos["armas"][nombre_arma]["defensa"]
