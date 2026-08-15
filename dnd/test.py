import random
from items import objetos
from enemies import enemigos
from character import Personaje
from level_system import SistemaNiveles

ATURDIMIENTO_POR_TIER = 0.10
ATURDIMIENTO_POR_FUERZA = 0.05
ATURDIMIENTO_MAXIMO = 0.80

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


def elegir_habitacion(habitacion_anterior):
    """Elige una habitación que resulte útil para el estado del jugador."""
    habitaciones_disponibles = [1]  # Combate
    precios = [
        datos["precio"]
        for categoria in objetos.values()
        for datos in categoria.values()
    ]
    precio_minimo = min(precios)

    # La tienda solo aparece si se puede comprar algo y no fue la sala anterior.
    if jugador.oro >= precio_minimo and habitacion_anterior != 2:
        habitaciones_disponibles.append(2)

    return random.choice(habitaciones_disponibles)


def elegir_enemigo(enemigo_anterior):
    enemigos_fuertes = {"Orco", "Troll"}
    candidatos = list(enemigos)

    # Después de un enemigo fuerte solo pueden aparecer enemigos normales.
    if enemigo_anterior in enemigos_fuertes:
        candidatos = [nombre for nombre in candidatos if nombre not in enemigos_fuertes]

    pesos = [enemigos[nombre]["peso"] for nombre in candidatos]
    return random.choices(candidatos, weights=pesos, k=1)[0]


def describir_intencion(ataque, dano):
    minimo, maximo = ataque
    tercio = (maximo - minimo) / 3

    if dano <= minimo + tercio:
        return "un ataque rápido"
    if dano >= maximo - tercio:
        return "un ataque poderoso"
    return "un ataque normal"


def elegir_accion(energia, tecnica, descripcion_tecnica):
    while True:
        print("1. Atacar")
        print("2. Defender (+1 de energía)")
        print(f"3. {tecnica} (-2 de energía): {descripcion_tecnica}")
        eleccion = input("> ")

        if eleccion in ("1", "2"):
            return eleccion
        if eleccion == "3" and energia >= 2:
            return eleccion
        if eleccion == "3":
            print("No tienes suficiente energía para usar la técnica.")
        else:
            print("Debes elegir una acción válida.")

# --- Bucle principal del juego ---
print("Te encuentras en un calabozo con muchas habitaciones, debes encontrar la salida")
print("Caminando por los pasillos encuentras la primera habitación...")

habitacion_anterior = None
enemigo_anterior = None

while True:
    if num_hab == 0:
        print("¡Has ganado!")
        break
    elif jugador.hp <= 0:
        print("Has muerto")
        break
    
    habitacion = elegir_habitacion(habitacion_anterior)
    habitacion_anterior = habitacion
    if habitacion == 1:  # Combate
        enemigo = elegir_enemigo(enemigo_anterior)
        enemigo_anterior = enemigo
        stats = enemigos[enemigo]
        
        enemigo_hp = stats["hp"]
        enemigo_ataque = stats["ataque"]
        enemigo_oro = stats["oro"]
        enemigo_exp = stats["exp"]
        print("Encontraste un " + enemigo)

        energia = 3
        while enemigo_hp > 0 and jugador.hp > 0:
            enemigo_dano = random.randint(enemigo_ataque[0], enemigo_ataque[1])
            intencion = describir_intencion(enemigo_ataque, enemigo_dano)
            datos_arma = objetos["armas"][jugador.arma]
            tecnica = datos_arma["tecnica"]
            descripcion_tecnica = datos_arma["descripcion_tecnica"]

            print(f"\nEl {enemigo} prepara {intencion}.")
            print(f"Vida: {jugador.hp}/{jugador.salud_maxima} | Energía: {energia}/3")
            print(f"Vida del {enemigo}: {max(0, enemigo_hp)}")
            accion = elegir_accion(energia, tecnica, descripcion_tecnica)

            min_dano, max_dano = datos_arma["ataque"]
            dano = 0
            defensa_extra = 0
            esquivar = False
            aturdir = False

            if accion == "1":
                dano = random.randint(min_dano, max_dano) + jugador.fuerza
                print(f"Atacaste al {enemigo} y le has restado {dano} puntos de vida")

            elif accion == "2":
                energia = min(3, energia + 1)
                defensa_extra = datos_arma["defensa"] + jugador.destreza
                print("Adoptas una postura defensiva.")

            else:
                energia -= 2
                tipo_tecnica = datos_arma["tipo_tecnica"]

                if tipo_tecnica == "constitucion":
                    dano = random.randint(min_dano, max_dano) + jugador.constitucion
                    defensa_extra = jugador.constitucion + 2
                    print("Levantas el escudo y preparas un contraataque.")
                    print(f"Atacaste al {enemigo} y le has restado {dano} puntos de vida")
                elif tipo_tecnica == "destreza":
                    dano = random.randint(min_dano, max_dano) + jugador.destreza * 2
                    probabilidad_esquivar = min(0.75, 0.20 + jugador.destreza * 0.05)
                    esquivar = random.random() < probabilidad_esquivar
                    print("Buscas un punto débil con un golpe preciso.")
                    print(f"Atacaste al {enemigo} y le has restado {dano} puntos de vida")
                else:
                    dano = random.randint(min_dano, max_dano) + jugador.fuerza * 2
                    probabilidad_aturdir = min(
                        ATURDIMIENTO_MAXIMO,
                        datos_arma["tier"] * ATURDIMIENTO_POR_TIER
                        + jugador.fuerza * ATURDIMIENTO_POR_FUERZA,
                    )
                    aturdir = random.random() < probabilidad_aturdir
                    print("Descargas toda tu fuerza con un golpe aplastante.")
                    print(f"Atacaste al {enemigo} y le has restado {dano} puntos de vida")
                    print(f"Probabilidad de aturdir: {probabilidad_aturdir:.0%}")

            enemigo_hp -= dano
            if dano > 0:
                print(f"Los puntos de vida del enemigo son {max(0, enemigo_hp)}")

            if enemigo_hp <= 0:
                print(f"Has derrotado al {enemigo}")
                jugador.ganar_exp(enemigo_exp)
                oro_ganado = random.randint(enemigo_oro[0], enemigo_oro[1])
                jugador.oro += oro_ganado
                print(f"Has ganado {oro_ganado} oro y {enemigo_exp} exp")
                procesar_subidas_de_nivel()
                input("Presiona enter para continuar")
                break

            if esquivar:
                print(f"Esquivaste el ataque del {enemigo}.")
                continue

            if aturdir:
                print(f"El {enemigo} queda aturdido y pierde su ataque.")
                continue

            defensa_total = (
                datos_arma["defensa"]
                + jugador.destreza
                + defensa_extra
            )
            dano_total = max(1, enemigo_dano - defensa_total)
            jugador.hp -= dano_total
            print(f"El {enemigo} te ha atacado y te ha restado {dano_total} puntos de vida")
            print(f"Tus puntos de vida son {jugador.hp}")
                
    elif habitacion == 2:  # Tienda
        enemigo_anterior = None
        print("Encuentras una tienda, el mercader te ofrece sus productos...")
        while True:
            print(f"\nOro disponible: {jugador.oro}")
            print("1. Pociones")
            print("2. Armas")
            print("3. Salir de la tienda")
            eleccion_tienda = input("> ")

            if eleccion_tienda == "1":
                menu_pociones = {
                    str(numero): nombre
                    for numero, nombre in enumerate(objetos["pociones"], start=1)
                }

                while True:
                    print("Pociones disponibles:")
                    for numero, nombre_pocion in menu_pociones.items():
                        precio = objetos["pociones"][nombre_pocion]["precio"]
                        print(f"{numero}. {nombre_pocion}: {precio} oro")

                    eleccion = input("¿Qué poción deseas comprar? ")
                    if eleccion not in menu_pociones:
                        print("Poción no disponible. Elige un número válido.")
                        continue

                    pocion_elegida = menu_pociones[eleccion]
                    precio = objetos["pociones"][pocion_elegida]["precio"]
                    if jugador.oro >= precio:
                        jugador.oro -= precio
                        min_salud, max_salud = objetos["pociones"][pocion_elegida]["salud"]
                        cantidad_curar = random.randint(min_salud, max_salud)
                        salud_recuperada = jugador.curar(cantidad_curar)
                        print(f"Has comprado {pocion_elegida} y recuperado {salud_recuperada} puntos de vida")
                        print(f"Tu salud actual es {jugador.hp}/{jugador.salud_maxima}")
                    else:
                        print("No tienes suficiente oro para comprar esa poción.")
                    break

            elif eleccion_tienda == "2":
                menu_armas = {
                    str(numero): nombre
                    for numero, nombre in enumerate(objetos["armas"], start=1)
                }

                while True:
                    print("Armas disponibles:")
                    for numero, nombre_arma in menu_armas.items():
                        precio = objetos["armas"][nombre_arma]["precio"]
                        print(f"{numero}. {nombre_arma}: {precio} oro")

                    eleccion = input("¿Qué arma deseas comprar? ")
                    if eleccion not in menu_armas:
                        print("Arma no disponible. Elige un número válido.")
                        continue

                    arma_elegida = menu_armas[eleccion]
                    precio = objetos["armas"][arma_elegida]["precio"]
                    if jugador.oro >= precio:
                        jugador.oro -= precio
                        jugador.arma = arma_elegida
                        print(f"Has comprado y equipado {arma_elegida}")
                    else:
                        print("No tienes suficiente oro para comprar esa arma.")
                    break

            elif eleccion_tienda == "3":
                print("Sales de la tienda.")
                break

            else:
                print("Opción no válida.")
    
    num_hab -= 1
    if num_hab > 0 and jugador.hp > 0:
        print(f"\nQuedan {num_hab} habitaciones")
        print("Caminando por el pasillo encuentras la siguiente habitación...")
