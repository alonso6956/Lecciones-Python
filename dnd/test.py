import random
import math
from items import objetos
from enemies import enemigos
from character import Personaje

# --- Inicialización ---
personaje = input("¿Cómo te llamas? ")

stat_base = {
    "fuerza": 1,
    "destreza": 1,
    "Constitución": 1,
    "Inteligencia": 1,
    "Carisma": 1,
}

exp_level = {
    1: {"exp": 30, "stats": 1},
    2: {"exp": 70, "stats": 1},
    3: {"exp": 130, "stats": 2},
    4: {"exp": 210, "stats": 2},
    5: {"exp": 310, "stats": 2},
    6: {"exp": 430, "stats": 3},
    7: {"exp": 570, "stats": 3},
    8: {"exp": 730, "stats": 3},
    9: {"exp": 910, "stats": 3},
    10: {"exp": 1200, "stats": 4},
}

num_hab = 50 # ejemplo de habitaciones

# --- Selección de arma inicial ---
menu = {}
i = 1
for nombre_arma, datos in objetos["armas"].items():
    if datos["tier"] == 1:
        menu[i] = nombre_arma
        i += 1

while True:
    for num, arma in menu.items():
        print(f"{num}. {arma}")
    personaje_arma_inicial = input("¿Qué arma quieres? ")
    if not personaje_arma_inicial.isdigit() or int(personaje_arma_inicial) not in menu:
        print("Debes elegir un número válido")
        continue
    personaje_arma_inicial = int(personaje_arma_inicial)
    personaje_arma = menu[personaje_arma_inicial]
    print("Has elegido " + personaje_arma)
    break

# --- Inicialización del personaje ---
jugador = Personaje(personaje, personaje_arma, stat_base)
print(f"{jugador.nombre} tiene {jugador.hp} puntos de vida")
print(f"Arma equipada: {jugador.arma}")