from operator import add, sub
import random

dinero = 100
precios_venta = {"maiz": (5, 10), "trigo": (10, 15), "tomate": (15, 20)}
precios_compras = {"maiz": 8, "trigo": 13, "tomate": 17}
semillas = {"maiz": 30, "trigo": 20, "tomate": 10}	
cultivos = {"maiz": 0, "trigo": 0, "tomate": 0}
cosechas = {"maiz": 0, "trigo": 0, "tomate": 0}


# función para mostrar el menú
def mostrar_menu():
    for i, accion in enumerate(acciones, start=1):
        print(f"{i}.{accion}")
    opcion = int(input("Elige una opcion: "))
    return opcion

def menu_comprar_semilla():
    for i, semilla in enumerate(semillas, start=1):
        print(f"{i}.{semilla}")
    opcion = int(input("Elige una opcion: "))
    return opcion

def menu_sembrar():
    for i, cultivo in enumerate(cultivos, start=1):
        print(f"{i}.{cultivo}")
    opcion = int(input("Elige una opcion: "))
    return opcion

def menu_cosechar():
    for i, cultivo in enumerate(cultivos, start=1):
        print(f"{i}.{cultivo}")
    opcion = int(input("Elige una opcion: "))
    return opcion

def menu_vender():
    for i, cultivo in enumerate(cultivos, start=1):
        print(f"{i}.{cultivo}")
    opcion = int(input("Elige una opcion: "))
    return opcion

def salir():
    print("Gracias por jugar")
    exit()

def comprar_semillas():
    opcion = menu_comprar_semilla()
    if opcion == 1:
        comprar_semillas_maiz()
    elif opcion == 2:
        comprar_semillas_trigo()
    elif opcion == 3:
        comprar_semillas_tomate()
    else:
        print("Opcion no valida")

def comprar_semillas_maiz():
    global dinero
    global semillas
    if dinero < precios_compras["maiz"]:
        print("No tienes suficiente dinero")
    else:
        dinero -= precios_compras["maiz"]
        semillas["maiz"] += 10
        print("Has comprado 10 semillas de maiz por " + str(precios_compras["maiz"]) + " dinero")

def comprar_semillas_trigo():
    global dinero
    global semillas
    if dinero < precios_compras["trigo"]:
        print("No tienes suficiente dinero")
    else:
        dinero -= precios_compras["trigo"]
        semillas["trigo"] += 10
        print("Has comprado 10 semillas de trigo por " + str(precios_compras["trigo"]) + " dinero")

def comprar_semillas_tomate():
    global dinero
    global semillas
    if dinero < precios_compras["tomate"]:
        print("No tienes suficiente dinero")
    else:
        dinero -= precios_compras["tomate"]
        semillas["tomate"] += 10
        print("Has comprado 10 semillas de tomate por " + str(precios_compras["tomate"]) + " dinero")


acciones = {"comprar": comprar_semillas, "sembrar": "sembrar", "cosechar": "cosechar", "vender": "vender", "salir": "salir"}
while True:
    opcion = mostrar_menu()
    claves = list(acciones.keys())
    accion = claves[opcion - 1]
    acciones[accion]()

