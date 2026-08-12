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

# --- Bucle principal del juego ---
print("Te encuentras en un calabozo con muchas habitaciones, debes encontrar la salida")
print("Caminando por los pasillos encuentras la primera habitación...")

while True:
    if num_hab == 0:
        print("¡Has ganado!")
        break
    elif jugador.hp <= 0:
        print("Has muerto")
        break
    
    habitacion = random.randint(1, 2)
    if habitacion == 1:  # Combate
        enemigo = random.choice(list(enemigos.keys()))
        stats = enemigos[enemigo]
        
        enemigo_hp = stats["hp"]
        enemigo_ataque = stats["ataque"]
        enemigo_oro = stats["oro"]
        enemigo_exp = stats["exp"]
        print("Encontraste un " + enemigo)
        
        while enemigo_hp > 0 and jugador.hp > 0:
            # Ataque del enemigo
            enemigo_dano = random.randint(enemigo_ataque[0], enemigo_ataque[1])
            dano_reduc = (objetos["armas"][jugador.arma]["defensa"] + jugador.destreza) / 10
            dano_total = math.ceil(max(1, enemigo_dano * (1 - dano_reduc)))
            jugador.hp -= dano_total
            print(f"El {enemigo} te ha atacado y te ha restado {dano_total} puntos de vida")
            print(f"Tus puntos de vida son {jugador.hp}")
            
            if jugador.hp <= 0:
                break
                
            # Ataque del jugador
            min_dano, max_dano = objetos["armas"][jugador.arma]["ataque"]
            dano = random.randint(min_dano, max_dano) + jugador.fuerza
            enemigo_hp -= dano
            print(f"Atacaste al {enemigo} y le has restado {dano} puntos de vida")
            print(f"Los puntos de vida del enemigo son {enemigo_hp}")
            
            if enemigo_hp <= 0:
                print(f"Has derrotado al {enemigo}")
                jugador.exp += enemigo_exp
                oro_ganado = random.randint(enemigo_oro[0], enemigo_oro[1])
                jugador.oro += oro_ganado
                print(f"Has ganado {oro_ganado} oro y {enemigo_exp} exp")
                input("Presiona enter para continuar")
                
    elif habitacion == 2:  # Cofre
        print("Encuentras un cofre, te acercas para abrirlo...")
        if random.random() < 0.7:  # 70% probabilidad de poción
            pocion = random.choice(list(objetos["pociones"].keys()))
            print(f"Has encontrado una {pocion}")
            min_salud, max_salud = objetos["pociones"][pocion]["salud"]
            cantidad_curar = random.randint(min_salud, max_salud)
            salud_recuperada = jugador.curar(cantidad_curar)
            print(f"Has recuperado {salud_recuperada} puntos de vida")
        else:  # 30% probabilidad de arma
            nueva_arma = random.choice(list(objetos["armas"].keys()))
            print(f"Has encontrado {nueva_arma}")
            if input("¿Deseas conservar el arma? (s/n) ").lower() == 's':
                jugador.arma = nueva_arma
                print(f"Has equipado {nueva_arma}")
            else:
                print(f"Has descartado {nueva_arma}")
                input("Presiona enter para continuar")
    
    # Subida de nivel
    while (jugador.nivel + 1) in exp_level and jugador.exp >= exp_level[jugador.nivel]["exp"]:
        jugador.nivel += 1
        stats_ganados = exp_level[jugador.nivel]["stats"]
        jugador.fuerza += stats_ganados
        jugador.destreza += stats_ganados
        jugador.constitucion += stats_ganados
        jugador.hp = jugador.hp + ((1 + stats_ganados) * jugador.constitucion)
        jugador.salud_maxima = jugador.salud_maxima + ((1 + stats_ganados) * jugador.constitucion)
        print(f"\n¡Has subido al nivel {jugador.nivel}!")
        print(f"Tus stats son: Fuerza {jugador.fuerza}, Destreza {jugador.destreza}, Constitución {jugador.constitucion}")
        print(f"Tu salud actual es {jugador.hp}")
        input("Presiona enter para continuar")
    
    num_hab -= 1
    if num_hab > 0 and jugador.hp > 0:
        print(f"\nQuedan {num_hab} habitaciones")
        print("Caminando por el pasillo encuentras la siguiente habitación...")