

objetos = {
    "armas": {
        "Espada y escudo de hierro": {
            "tier": 1,
            "ataque": (2, 4),
            "escalado_defensa": {"fuerza": 1.20, "constitucion": 1.01},
            "descripcion_defensa": "120% Fuerza + 101% Constitución",
            "precio": 50,
            "tecnica": "Bloqueo y contraataque",
            "tipo_tecnica": "constitucion",
            "descripcion_tecnica": "ataca y aumenta la defensa con Constitución",
        },
        "Hacha de hierro": {
            "tier": 1,
            "ataque": (4, 8),
            "escalado_defensa": {"destreza": 1.10, "constitucion": 1.01},
            "descripcion_defensa": "110% Destreza + 101% Constitución",
            "precio": 50,
            "tecnica": "Golpe preciso",
            "tipo_tecnica": "destreza",
            "descripcion_tecnica": "aumenta el daño con Destreza y puede esquivar",
        },
        "Maza de hierro": {
            "tier": 1,
            "ataque": (6, 13),
            "escalado_defensa": {
                "fuerza": 1.05,
                "destreza": 1.05,
                "constitucion": 1.01,
            },
            "descripcion_defensa": (
                "110% Fuerza + 110% Destreza + 101% Constitución"
            ),
            "precio": 50,
            "tecnica": "Golpe aplastante",
            "tipo_tecnica": "fuerza",
            "descripcion_tecnica": "duplica Fuerza y puede aturdir según Fuerza y tier",
        },
    },
    "pociones": {
        "Pocion pequeña": {"salud": (1, 4), "precio": 10},
        "Pocion mediana": {"salud": (3, 9), "precio": 20},
        "Pocion grande": {"salud": (6, 10), "precio": 50},
        "Pocion extra grande": {"salud": (8, 24), "precio": 70},
    }
}


def calcular_defensa(nombre_arma, fuerza, destreza, constitucion):
    """Calcula la defensa del arma a partir de las estadísticas del personaje."""
    estadisticas = {
        "fuerza": fuerza,
        "destreza": destreza,
        "constitucion": constitucion,
    }
    escalado = objetos["armas"][nombre_arma]["escalado_defensa"]

    defensa = sum(
        estadisticas[estadistica] * multiplicador
        for estadistica, multiplicador in escalado.items()
    )
    return int(defensa)
