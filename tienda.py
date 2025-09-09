dinero = 100
tienda = [
    {"nombre": "Espada", "precio.c": 50, "cantidad": 10,},
    {"nombre": "Escudo", "precio.c": 30, "cantidad": 5,},
    {"nombre": "Poción", "precio.c": 10, "cantidad": 20},
]
inventario = [
    {"nombre": "Espada", "precio.v": 25, "cantidad": 0,},
    {"nombre": "Escudo", "precio.v": 15, "cantidad": 0,},
    {"nombre": "Poción", "precio.v": 5, "cantidad": 0,},
]

def menu_principal():
    print("1. Comprar")
    print("2. Vender")
    print("3. Salir")
    do = input("¿Qué te gustaría hacer? ")
    return do

def comprar(dinero):
    print("Bienvenido a la tienda!")
    print("Artículos disponibles:")
    for i, item in enumerate(tienda, start=1):
        print(f"{i}.{item['nombre']} - Precio: {item['precio.c']} monedas - Cantidad: {item['cantidad']}")
    opcion = input("¿Qué te gustaría comprar? ")
    opcion = int(opcion) - 1
    if opcion < 0 or opcion >= len(tienda):
        print("Opción inválida. Inténtalo de nuevo.")
    else:
        item = tienda[opcion]
        if item['cantidad'] <= 0:
            print("Lo siento, este artículo está agotado.")
        elif dinero < item['precio.c']:
            print("No tienes suficiente dinero para comprar este artículo.")
        else:
            item['cantidad'] -= 1
            inventario[opcion]['cantidad'] += 1
            dinero -= item['precio.c']
            print(f"Has comprado un {item['nombre']} por {item['precio.c']} monedas.")
    return dinero
     
def vender(dinero):
    print("Artículos en tu inventario:")
    for i, item in enumerate(inventario, start=1):
        print(f"{i}.{item['nombre']} - Precio: {item['precio.v']} monedas - Cantidad: {item['cantidad']}")
    opcion = input("¿Qué te gustaría vender? ")
    opcion = int(opcion) - 1
    if opcion <= 0 or opcion >= len(inventario):
        print("Opción inválida. Inténtalo de nuevo.")
    else:
        item = inventario[opcion]
        if item['cantidad'] <= 0:
            print("No tienes este articulo.")
        else:
            item['cantidad'] -= 1
            tienda[opcion]['cantidad'] += 1
            dinero += item['precio.v']
            print(f"Has vendido un {item['nombre']} por {item['precio.v']} monedas.")
    return dinero
        
while True: 
    print("\nEstás en la tienda del juego. Gasta tu dinero sabiamente. ")
    print(f"Tienes {dinero} monedas.")
    do = menu_principal()
    if do == "1":
        dinero = comprar(dinero)
    elif do == "2":
        dinero = vender(dinero)
    elif do == "3":
        print("¡Gracias por visitar la tienda! ¡Hasta luego!")
        break
    else:
        print("Opción inválida. Inténtalo de nuevo.")
        continue
    print(f"Te quedan {dinero} monedas.")
    if dinero <= 0:
        print("Te has quedado sin dinero. ¡Adiós!")
        break
    else:
        continue # Vuelve al inicio del bucle
        
    
    
    