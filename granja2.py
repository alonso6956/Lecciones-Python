from operator import add, sub
import random
import math



GRANJA_ASCII_ART = """
    _._._._._._._._._._
   /   GRANJA PYTHON   \\
  /._._._._._._._._._._\\
      |     |     |
  ----+-----+-----+----
    __| ___ | ___ |__
   (__|[-|-]|[-|-]|__)
      |     |     |
"""

time = 0
dinero = 100
precios_venta = {"maiz": (5, 10), "trigo": (10, 15), "tomate": (15, 20)}
precios_compras = {"maiz": 8, "trigo": 13, "tomate": 17}
semillas = {"maiz": 30, "trigo": 20, "tomate": 10}	
cultivos = {"maiz": 0, "trigo": 0, "tomate": 0}
cosechas = {"maiz": 0, "trigo": 0, "tomate": 0}

def mostrar_menu_generico(opciones):
    """
    Función genérica para mostrar menús
    opciones: diccionario o lista con las opciones a mostrar
    titulo: texto a mostrar antes de las opciones
    """
    print(GRANJA_ASCII_ART)
    
    if isinstance(opciones, dict):
        items = opciones.keys()
    else:
        items = opciones
        
    for i, item in enumerate(items, start=1):
        print(f"{i}.{item}")
    
    try:
        opcion = int(input("Selecciona una opción: "))
        if 1 <= opcion <= len(items):
            return opcion
        else:
            print("Opción no válida")
            return None
    except ValueError:
        print("Por favor ingresa un número válido")
        return None

# Reemplazar las funciones de menú existentes
def menu_comprar_semilla():
    return mostrar_menu_generico(semillas)

def menu_sembrar():
    return mostrar_menu_generico(cultivos)

def menu_cosechar():
    return mostrar_menu_generico(cultivos)

def menu_vender():
    return mostrar_menu_generico(cultivos)

def mostrar_menu():
    return mostrar_menu_generico(acciones)

def salir():
    print("Gracias por jugar")
    exit()

#Lista de funciones para cada acción, separadas por tipo de cosecha
def comprar_semillas(dinero, semillas):
    opcion = menu_comprar_semilla()
    if opcion == 1:
        comprar_semillas_maiz(dinero, semillas)
    elif opcion == 2:
        comprar_semillas_trigo(dinero, semillas)
    elif opcion == 3:
        comprar_semillas_tomate(dinero, semillas)
    else:
        print("Opcion no valida")
    return dinero, semillas

def comprar_semillas_maiz(dinero, semillas):
    if dinero < precios_compras["maiz"]:
        print("No tienes suficiente dinero")
    else:
        dinero -= precios_compras["maiz"]
        semillas["maiz"] += 10
        print("Has comprado 10 semillas de maiz por " + str(precios_compras["maiz"]) + " dinero")
    return dinero, semillas

def comprar_semillas_trigo(dinero, semillas):
    if dinero < precios_compras["trigo"]:
        print("No tienes suficiente dinero")
    else:
        dinero -= precios_compras["trigo"]
        semillas["trigo"] += 10
        print("Has comprado 10 semillas de trigo por " + str(precios_compras["trigo"]) + " dinero")
    return dinero, semillas

def comprar_semillas_tomate(dinero, semillas):
    if dinero < precios_compras["tomate"]:
        print("No tienes suficiente dinero")
    else:
        dinero -= precios_compras["tomate"]
        semillas["tomate"] += 10
        print("Has comprado 10 semillas de tomate por " + str(precios_compras["tomate"]) + " dinero")
    return dinero, semillas
        
def sembrar():
    opcion = menu_sembrar()
    if opcion == 1:
        sembrar_maiz(semillas, cultivos)
    elif opcion == 2:
        sembrar_trigo(semillas, cultivos)
    elif opcion == 3:
        sembrar_tomate(semillas, cultivos)
    else:
        print("Opcion no valida")
        
def sembrar_maiz(semillas, cultivos):
    if semillas["maiz"] < 1:
        print("No tienes suficientes semillas de maiz")
    else:
        semillas["maiz"] -= 1
        cultivos["maiz"] += 1
        print("Has sembrado 1 semilla de maiz")
    return semillas, cultivos
        
def sembrar_trigo(semillas, cultivos):
    if semillas["trigo"] < 1:
        print("No tienes suficientes semillas de trigo")
    else:
        semillas["trigo"] -= 1
        cultivos["trigo"] += 1
        print("Has sembrado 1 semilla de trigo")
    return semillas, cultivos
        
def sembrar_tomate(semillas, cultivos):
    if semillas["tomate"] < 1:
        print("No tienes suficientes semillas de tomate")
    else:
        semillas["tomate"] -= 1
        cultivos["tomate"] += 1
        print("Has sembrado 1 semilla de tomate")
    return semillas, cultivos
        
def cosechar():
    opcion = menu_cosechar()
    if opcion == 1:
        cosechar_maiz(cultivos, cosechas)
    elif opcion == 2:
        cosechar_trigo(cultivos, cosechas)
    elif opcion == 3:
        cosechar_tomate(cultivos, cosechas)
    else:
        print("Opcion no valida")
        
def cosechar_maiz(cultivos, cosechas):
    if cultivos["maiz"] < 1:
        print("No tienes cultivos de maiz para cosechar")
    else:
        cultivos["maiz"] -= 1
        cosechas["maiz"] += 1
        print("Has cosechado 1 cultivo de maiz")
    return cultivos, cosechas
        
def cosechar_trigo(cultivos, cosechas):
    if cultivos["trigo"] < 1:
        print("No tienes cultivos de trigo para cosechar")
    else:
        cultivos["trigo"] -= 1
        cosechas["trigo"] += 1
        print("Has cosechado 1 cultivo de trigo")
    return cultivos, cosechas
        
def cosechar_tomate(cultivos, cosechas):
    if cultivos["tomate"] < 1:
        print("No tienes cultivos de tomate para cosechar")
    else:
        cultivos["tomate"] -= 1
        cosechas["tomate"] += 1
        print("Has cosechado 1 cultivo de tomate")
    return cultivos, cosechas

def vender():
    opcion = menu_vender()
    if opcion == 1:
        vender_maiz(dinero, cosechas)
    elif opcion == 2:
        vender_trigo(dinero, cosechas)
    elif opcion == 3:
        vender_tomate(dinero, cosechas)
    else:
        print("Opcion no valida")

def vender_maiz(dinero, cosechas):
    if cosechas["maiz"] < 1:
        print("No tienes cosechas de maiz para vender")
    else:
        precio_venta = random.randint(precios_venta["maiz"][0], precios_venta["maiz"][1])
        dinero += precio_venta
        cosechas["maiz"] -= 1
        print(f"Has vendido 1 cosecha de maiz por {precio_venta} dinero")
    return dinero, cosechas

def vender_trigo(dinero, cosechas):
    if cosechas["trigo"] < 1:
        print("No tienes cosechas de trigo para vender")
    else:
        precio_venta = random.randint(precios_venta["trigo"][0], precios_venta["trigo"][1])
        dinero += precio_venta
        cosechas["trigo"] -= 1
        print(f"Has vendido 1 cosecha de trigo por {precio_venta} dinero")
    return dinero, cosechas
        
def vender_tomate(dinero, cosechas):
    if cosechas["tomate"] < 1:
        print("No tienes cosechas de tomate para vender")
    else:
        precio_venta = random.randint(precios_venta["tomate"][0], precios_venta["tomate"][1])
        dinero += precio_venta
        cosechas["tomate"] -= 1
        print(f"Has vendido 1 cosecha de tomate por {precio_venta} dinero")
    return dinero, cosechas


acciones = {"comprar": comprar_semillas, "sembrar": sembrar, "cosechar": cosechar, "vender": vender, "salir": salir}


while True:
    opcion = mostrar_menu()
    if opcion is None:  # mostrar_menu() ya valida el número
        continue
    claves = list(acciones.keys())
    accion = claves[opcion - 1]
    dinero, cosechas = acciones[accion](dinero, cosechas)
        
    print(f"Meses: {time}, Dinero: {dinero}")
    
        


    
    
    

