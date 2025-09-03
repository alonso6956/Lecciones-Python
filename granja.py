from operator import add, sub
import random


dinero = 100
precios_venta = {"maiz": (5, 10), "trigo": (10, 15), "tomate": (15, 20)}
precios_compras = {"maiz": 8, "trigo": 13, "tomate": 17}
semillas = {"maiz": 30, "trigo": 20, "tomate": 10}	
cultivos = {"maiz": 0, "trigo": 0, "tomate": 0}
cosechas = {"maiz": 0, "trigo": 0, "tomate": 0}

def mostrar_menu():
    print("1. Comprar semillas")
    print("2. Sembrar")
    print("3. Cosechar")
    print("4. Vender")
    print("5. Salir")

def comprar_semillas():
    print("1. Comprar 30 maiz por 8 dinero")
    print("2. Comprar 20 trigo por 13 dinero")
    print("3. Comprar 10 tomate por 17 dinero")

def comprar_semillas_maiz():
    global dinero
    if dinero < precios_compras["maiz"]:
        print("No tienes dinero suficiente")
    else:
        semillas["maiz"] += 30
        dinero -= precios_compras["maiz"]
        print("Has comprado 30 maiz por 8 dinero")

def comprar_semillas_trigo():
    global dinero
    if dinero < precios_compras["trigo"]:
        print("No tienes dinero suficiente")
    else:
        semillas["trigo"] += 20
        dinero -= precios_compras["trigo"]
        print("Has comprado 20 trigo por 13 dinero")

def comprar_semillas_tomate():
    global dinero
    if dinero < precios_compras["tomate"]:
        print("No tienes dinero suficiente")
    else:
        semillas["tomate"] += 10
        dinero -= precios_compras["tomate"]
        print("Has comprado 10 tomate por 17 dinero")

def sembrar_menu():
    print("1. Sembrar maiz")
    print("2. Sembrar trigo")
    print("3. Sembrar tomate")

def sembrar_maiz():
    if semillas["maiz"] < 10:
        print("No tienes semillas suficientes")
    else:
        semillas["maiz"] -= 10
        cultivos["maiz"] = add(10, cultivos["maiz"])
        print("Has sembrado 10 maiz")

def sembrar_trigo():
    if semillas["trigo"] < 10:
        print("No tienes semillas suficientes")
    else:
        semillas["trigo"] -= 10
        cultivos["trigo"] = add(10, cultivos["trigo"])
        print("Has sembrado 10 trigo")

def sembrar_tomate():
    if semillas["tomate"] < 10:
        print("No tienes semillas suficientes")
    else:
        semillas["tomate"] -= 10
        cultivos["tomate"] = add(10, cultivos["tomate"])
        print("Has sembrado 10 tomate")

def cosechar_menu():
    print("1. Cosechar maiz")
    print("2. Cosechar trigo")
    print("3. Cosechar tomate")

def cosechar_maiz():
    if cultivos["maiz"] == 0:
        print("No tienes maiz sembrado")
    else:
        cosechas["maiz"] = add(random.randint(1, 10), cosechas["maiz"])
        cultivos["maiz"] -= 10
        print("Has cosechado " + str(cosechas["maiz"]) + " maiz")

def cosechar_trigo():
    if cultivos["trigo"] == 0:
        print("No tienes trigo sembrado")
    else:
        cosechas["trigo"] = add(random.randint(1, 10), cosechas["trigo"])
        cultivos["trigo"] -= 10
        print("Has cosechado " + str(cosechas["trigo"]) + " trigo")

def cosechar_tomate():
    if cultivos["tomate"] == 0:
        print("No tienes tomate sembrado")
    else:
        cosechas["tomate"] = add(random.randint(1, 10), cosechas["tomate"])
        cultivos["tomate"] -= 10
        print("Has cosechado " + str(cosechas["tomate"]) + " tomate")

#funcion vender(cultivo, cantidad):
#    aumentar dinero segun precio del cultivo
#    disminuir cantidad en cultivos[cultivo]

def vender_menu():
    print("1. Vender maiz")
    print("2. Vender trigo")
    print("3. Vender tomate")

def vender_maiz():
    global dinero
    if cosechas["maiz"] < 10:
        print("No tienes suficiente maiz cosechado")
    else:
        precio_venta = random.randint(precios_venta["maiz"][0], precios_venta["maiz"][1])
        dinero += precio_venta
        cosechas["maiz"] -= 10
        print("Has vendido 10 maiz por " + str(precio_venta) + " dinero")

def vender_trigo():
    global dinero
    if cosechas["trigo"] < 10:
        print("No tienes trigo cosechado")
    else:
        precio_venta = random.randint(precios_venta["trigo"][0], precios_venta["trigo"][1])
        dinero += precio_venta
        cosechas["trigo"] -= 10
        print("Has vendido 10 trigo por " + str(precio_venta) + " dinero")

def vender_tomate():
    global dinero
    if cosechas["tomate"] < 10:
        print("No tienes tomate cosechado")
    else:
        precio_venta = random.randint(precios_venta["tomate"][0], precios_venta["tomate"][1])
        dinero += precio_venta
        cosechas["tomate"] -= 10
        print("Has vendido 10 tomate por " + str(precio_venta) + " dinero")

#bucle hasta que usuario salga:
#    mostrar menu
#    pedir opcion
#    ejecutar funcion correspondiente

while True:
    mostrar_menu()
    opcion = int(input("Elige una opcion: "))
    if opcion == 1:
        comprar_semillas()
        opcion = int(input("Elige una opción: "))
        if opcion == 1:
            comprar_semillas_maiz()
        elif opcion == 2:
            comprar_semillas_tomate()
        elif opcion == 3:
            comprar_semillas_trigo()
        else:
            print("Opcion no valida")
    elif opcion == 2:
        sembrar_menu()
        opcion = int(input("Elige una opcion: "))
        if opcion == 1:
            sembrar_maiz()
        elif opcion == 2:
            sembrar_trigo()
        elif opcion == 3:
            sembrar_tomate()
        else:
            print("Opcion no valida")
    elif opcion == 3:
        cosechar_menu()
        opcion = int(input("Elige una opcion: "))
        if opcion == 1:
            cosechar_maiz()
        elif opcion == 2:
            cosechar_trigo()
        elif opcion == 3:
            cosechar_tomate()
        else:
            print("Opcion no valida")
    elif opcion == 4:
        vender_menu()
        opcion = int(input("Elige una opcion: "))
        if opcion == 1:
            vender_maiz()
        elif opcion == 2:
            vender_trigo()
        elif opcion == 3:
            vender_tomate()
        else:
            print("Opcion no valida")
    elif opcion == 5:
        print("Has salido de la granja")
        break
    else:
        print("Opcion no valida")
