import inventario
import errores

def mostrar_menu():
    print("\n--- Forja de armas ---")
    print("1. Forjar un arma aleatoria")
    print("2. Mejorar un arma")
    print("3. Vender un arma")
    print("4. Ver inventario")
    print("5. Salir de la forja")
    do = input("Selecciona una opción: ")
    return do

while True:
    do = mostrar_menu()
    if do == "1":
        inventario.dinero = inventario.forjar_arma(inventario.armas, inventario.dinero)
        print(f"Dinero restante: {inventario.dinero} monedas")
    elif do == "2":
        inventario.dinero = inventario.mejorar_arma(inventario.dinero)
        print(f"Dinero restante: {inventario.dinero} monedas")
    elif do == "3":
        inventario.dinero = inventario.vender_arma(inventario.dinero)
        print(f"Dinero restante: {inventario.dinero} monedas")
    elif do == "4":
        inventario.mostrar_inventario()
    elif do == "5":
        print("\nSaliendo de la forja...")
        break
    else:
       errores.opcion_invalida()