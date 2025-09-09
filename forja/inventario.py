import random
from errores import NoHayDinero, CustomValueError

dinero = 10000
armas = [
    {"nombre": "Espada Llameante", "precio": 2500, "ataque": 25, "defensa": 5},
    {"nombre": "Arco de los Cielos", "precio": 3200, "ataque": 30, "defensa": 0},
    {"nombre": "Martillo de la Tormenta", "precio": 2800, "ataque": 28, "defensa": 10},
    {"nombre": "Daga de la Sombra", "precio": 1800, "ataque": 20, "defensa": 0},
    {"nombre": "Cetro del Hechicero", "precio": 4500, "ataque": 15, "defensa": 15},
    {"nombre": "Hacha del Minotauro", "precio": 2100, "ataque": 26, "defensa": 0},
    {"nombre": "Lanza de la Sirena", "precio": 1950, "ataque": 22, "defensa": 8},
    {"nombre": "Guanteletes de Poder", "precio": 2700, "ataque": 23, "defensa": 12},
    {"nombre": "Escudo del Dragón", "precio": 3500, "ataque": 10, "defensa": 35},
    {"nombre": "Vorpal Sword", "precio": 6000, "ataque": 40, "defensa": 10},
    {"nombre": "Bastón de los Magos", "precio": 5500, "ataque": 20, "defensa": 20},
    {"nombre": "Espada de la Aventura", "precio": 3000, "ataque": 28, "defensa": 8},
    {"nombre": "Arco del Guardián", "precio": 3300, "ataque": 32, "defensa": 5},
    {"nombre": "Maza de la Fe", "precio": 2400, "ataque": 25, "defensa": 15},
    {"nombre": "Cetro del Rey", "precio": 4800, "ataque": 18, "defensa": 22},
    {"nombre": "Hacha de Batalla", "precio": 2600, "ataque": 29, "defensa": 0},
    {"nombre": "Lanza de la Serpiente", "precio": 2000, "ataque": 24, "defensa": 10},
    {"nombre": "Puñal del Asesino", "precio": 2200, "ataque": 26, "defensa": 0},
    {"nombre": "Escudo Sagrado", "precio": 3800, "ataque": 12, "defensa": 30},
    {"nombre": "Espada de la Noche", "precio": 4000, "ataque": 35, "defensa": 5},
]

inventario_jugador = [
    
]

def forjar_arma(armas, dinero):
    if not armas:
        print("\nNo hay más armas disponibles para forjar.")
        return dinero
    nueva_arma = random.choice(armas)
    try: 
        if nueva_arma["precio"] > dinero:
            raise NoHayDinero
    except NoHayDinero:
        print("No tienes suficiente dinero para forjar esta arma.")
    else:
        inventario_jugador.append(nueva_arma)
        armas.pop(armas.index(nueva_arma))
        dinero -= nueva_arma["precio"]
        print(f"\nHas forjado una nuevo arma: {nueva_arma['nombre']} (Ataque: {nueva_arma['ataque']}, Defensa: {nueva_arma['defensa']})")
    return dinero
        
def mejorar_arma(dinero):
    if not inventario_jugador:
        print("\nNo tienes armas en tu inventario para mejorar.")
        return dinero
    for i, arma in enumerate(inventario_jugador):
        print(f"\n{i + 1}. {arma['nombre']} (Ataque: {arma['ataque']}, Defensa: {arma['defensa']})")
    while True:
        try:
            eleccion = int(input("Selecciona el número del arma que quieres mejorar: ")) - 1
            if eleccion < 0 or eleccion >= len(inventario_jugador):
                raise ValueError
        except ValueError:
            print("Entrada inválida. Por favor, ingresa un número.")
            continue
        else:
            break
    print(f"\n¿Qué deseas mejorar? ")
    print("1. Ataque (+5 por 500 monedas)")
    print("2. Defensa (+5 por 500 monedas)")
    while True:
        try:
            mejora = int(input("Selecciona una opción: "))
            if mejora not in [1, 2]:
                raise ValueError
        except ValueError:
            print("Entrada inválida. Por favor, ingresa 1 o 2.")
        else:
            break
    if mejora == 1:
        costo = 500
        if dinero >= costo:
            ataque_anterior = inventario_jugador[eleccion]["ataque"]
            inventario_jugador[eleccion]["ataque"] += 5
            inventario_jugador[eleccion]["precio"] += 500
            dinero -= costo
            print(f"\nAtaque mejorado. Ataque anterior: {ataque_anterior} Nuevo ataque: {inventario_jugador[eleccion]['ataque']}")
        else:
            print("No tienes suficiente dinero para mejorar el ataque.")
    elif mejora == 2:
        costo = 500
        if dinero >= costo:
            defensa_anterior = inventario_jugador[eleccion]["defensa"]
            inventario_jugador[eleccion]["defensa"] += 5
            inventario_jugador[eleccion]["precio"] += 500
            dinero -= costo
            print(f"\nDefensa mejorada. Defensa anterior: {defensa_anterior} Nueva defensa: {inventario_jugador[eleccion]['defensa']}")
        else:
            print("No tienes suficiente dinero para mejorar la defensa.")
    return dinero
    
def vender_arma(dinero):
    if not inventario_jugador:
        print("\nNo tienes armas en tu inventario para vender.")
        return dinero
    print("\n")
    for i, arma in enumerate(inventario_jugador):
        print(f"{i + 1}. {arma['nombre']} (Precio de venta: {arma['precio'] // 2} monedas)")
    while True:
        try:
            eleccion = int(input("Selecciona el número del arma que quieres vender: ")) - 1
            if eleccion < 0 or eleccion >= len(inventario_jugador):
                raise ValueError
        except ValueError:
            print("Entrada inválida. Por favor, ingresa un número.")
            continue
        else:
            break
    valor_venta = inventario_jugador[eleccion]["precio"] // 2
    item = inventario_jugador[eleccion]
    dinero += valor_venta
    inventario_jugador.pop(eleccion)
    print(f"\nHas vendido {item['nombre']} por {valor_venta} monedas.")
    return dinero

def mostrar_inventario():
    if not inventario_jugador:
        print("\nTu inventario está vacío.")
        return
    print("\n--- Inventario ---")
    for arma in inventario_jugador:
        print(f"{arma['nombre']} (Ataque: {arma['ataque']}, Defensa: {arma['defensa']})")