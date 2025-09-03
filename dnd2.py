import random
import math

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

objetos = {
    "armas": {
        "Espada y escudo de hierro": {"tier": 1, "ataque": (3, 5), "defensa": 3},
        "Hacha de hierro": {"tier": 1, "ataque": (4, 8), "defensa": 2},
        "Maza de hierro": {"tier": 1, "ataque": (3, 9), "defensa": 1},
    },
    "pociones": {
        "Pocion pequeña": {"salud": (1, 4)},
        "Pocion mediana": {"salud": (2, 8)},
        "Pocion grande": {"salud": (3, 12)},
        "Pocion extra grande": {"salud": (4, 16)},
    }
}

enemigos = {
    "Esqueleto": {"hp": 20, "oro": (5, 10), "exp": 15, "ataque": (3, 6)},
    "Orco": {"hp": 30, "oro": (10, 15), "exp": 30, "ataque": (6, 12)},
    "Goblin": {"hp": 15, "oro": (3, 5), "exp": 10, "ataque": (2, 4)},
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
personaje_fuerza = stat_base["fuerza"]
personaje_destreza = stat_base["destreza"]
personaje_constitucion = stat_base["Constitución"]
personaje_hp = 50 * personaje_constitucion
salud_maxima = 50 * personaje_constitucion
personaje_level = 1
personaje_oro = 0
personaje_exp = 0

# --- Bucle principal del juego ---
print("Te encuentras en un calabozo con muchas habitaciones, debes encontrar la salida")
print("Caminando por los pasillos encuentras la primera habitación...")

while True:
    if num_hab == 0:
        print("¡Has ganado!")
        break
    elif personaje_hp <= 0:
        print("Has muerto")
        break
    
    habitacion = random.randint(1, 3)
    if habitacion == 1:  # Combate
        enemigo = random.choice(list(enemigos.keys()))
        stats = enemigos[enemigo]
        
        enemigo_hp = stats["hp"]
        enemigo_ataque = stats["ataque"]
        enemigo_oro = stats["oro"]
        enemigo_exp = stats["exp"]
        print("Encontraste un " + enemigo)
        
        while enemigo_hp > 0 and personaje_hp > 0:
            # Ataque del enemigo
            enemigo_dano = random.randint(enemigo_ataque[0], enemigo_ataque[1])
            dano_reduc = (objetos["armas"][personaje_arma]["defensa"] + personaje_destreza) / 10
            dano_total = math.ceil(max(1, enemigo_dano * (1 - dano_reduc)))
            personaje_hp -= dano_total
            print(f"El {enemigo} te ha atacado y te ha restado {dano_total} puntos de vida")
            print(f"Tus puntos de vida son {personaje_hp}")
            
            if personaje_hp <= 0:
                break
                
            # Ataque del jugador
            min_dano, max_dano = objetos["armas"][personaje_arma]["ataque"]
            dano = random.randint(min_dano, max_dano) + personaje_fuerza
            enemigo_hp -= dano
            print(f"Atacaste al {enemigo} y le has restado {dano} puntos de vida")
            print(f"Los puntos de vida del enemigo son {enemigo_hp}")
            
            if enemigo_hp <= 0:
                print(f"Has derrotado al {enemigo}")
                personaje_exp += enemigo_exp
                oro_ganado = random.randint(enemigo_oro[0], enemigo_oro[1])
                personaje_oro += oro_ganado
                print(f"Has ganado {oro_ganado} oro y {enemigo_exp} exp")
                input("Presiona enter para continuar")
                
    elif habitacion == 2:  # Cofre
        print("Encuentras un cofre, te acercas para abrirlo...")
        if random.random() < 0.7:  # 70% probabilidad de poción
            pocion = random.choice(list(objetos["pociones"].keys()))
            print(f"Has encontrado una {pocion}")
            min_salud, max_salud = objetos["pociones"][pocion]["salud"]
            salud_recuperada = random.randint(min_salud, max_salud)
            personaje_hp = min(salud_maxima, personaje_hp + salud_recuperada)
            print(f"Has recuperado {salud_recuperada} puntos de vida")
        else:  # 30% probabilidad de arma
            nueva_arma = random.choice(list(objetos["armas"].keys()))
            print(f"Has encontrado {nueva_arma}")
            if input("¿Deseas conservar el arma? (s/n) ").lower() == 's':
                personaje_arma = nueva_arma
                print(f"Has equipado {nueva_arma}")
            else:
                print(f"Has descartado {nueva_arma}")
                input("Presiona enter para continuar")
    
    # Subida de nivel
    while (personaje_level + 1) in exp_level and personaje_exp >= exp_level[personaje_level]["exp"]:
        personaje_level += 1
        stats_ganados = exp_level[personaje_level]["stats"]
        personaje_fuerza += stats_ganados
        personaje_destreza += stats_ganados
        personaje_constitucion += stats_ganados
        personaje_hp = personaje_hp + ((1 + stats_ganados) * personaje_constitucion)
        salud_maxima = salud_maxima + ((1 + stats_ganados) * personaje_constitucion)
        print(f"\n¡Has subido al nivel {personaje_level}!")
        print(f"Tus stats son: Fuerza {personaje_fuerza}, Destreza {personaje_destreza}, Constitución {personaje_constitucion}")
        print(f"Tu salud actual es {personaje_hp}")
        input("Presiona enter para continuar")
    
    num_hab -= 1
    if num_hab > 0 and personaje_hp > 0:
        print(f"\nQuedan {num_hab} habitaciones")
        print("Caminando por el pasillo encuentras la siguiente habitación...")
