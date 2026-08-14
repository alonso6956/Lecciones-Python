import random
from items import objetos
from enemies import enemigos
from character import Personaje
from level_system import SistemaNiveles

# --- Inicialización ---
personaje = input("¿Cómo te llamas? ")

stat_base = {
    "fuerza": 1,
    "destreza": 1,
    "Constitución": 1,
    "Inteligencia": 1,
    "Carisma": 1,
}

sistema_niveles = SistemaNiveles(exp_por_nivel=30, nivel_maximo=10)

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


def elegir_estadistica():
    opciones = {
        "1": "fuerza",
        "2": "destreza",
        "3": "constitucion",
    }

    while True:
        print("Elige una estadística para aumentar:")
        print("1. Fuerza")
        print("2. Destreza")
        print("3. Constitución (+10 de salud máxima)")
        eleccion = input("> ")

        if eleccion in opciones:
            return opciones[eleccion]

        print("Debes elegir un número válido")


def procesar_subidas_de_nivel():
    while sistema_niveles.puede_subir(jugador):
        estadistica = elegir_estadistica()
        jugador.subir_nivel(estadistica)

        print(f"\n¡Has subido al nivel {jugador.nivel}!")
        print(f"Has aumentado tu {estadistica} en 1 punto")
        print(
            f"Tus stats son: Fuerza {jugador.fuerza}, "
            f"Destreza {jugador.destreza}, "
            f"Constitución {jugador.constitucion}"
        )
        print(f"Tu salud actual es {jugador.hp}/{jugador.salud_maxima}")

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
            defensa_total = (
                objetos["armas"][jugador.arma]["defensa"]
                + jugador.destreza
            )
            dano_total = max(1, enemigo_dano - defensa_total)
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
                jugador.ganar_exp(enemigo_exp)
                oro_ganado = random.randint(enemigo_oro[0], enemigo_oro[1])
                jugador.oro += oro_ganado
                print(f"Has ganado {oro_ganado} oro y {enemigo_exp} exp")
                procesar_subidas_de_nivel()
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
            print(f"Tu salud actual es {jugador.hp}/{jugador.salud_maxima}")
        else:  # 30% probabilidad de arma
            nueva_arma = random.choice(list(objetos["armas"].keys()))
            print(f"Has encontrado {nueva_arma}")
            if input("¿Deseas conservar el arma? (s/n) ").lower() == 's':
                jugador.arma = nueva_arma
                print(f"Has equipado {nueva_arma}")
            else:
                print(f"Has descartado {nueva_arma}")
                input("Presiona enter para continuar")
    
    num_hab -= 1
    if num_hab > 0 and jugador.hp > 0:
        print(f"\nQuedan {num_hab} habitaciones")
        print("Caminando por el pasillo encuentras la siguiente habitación...")
