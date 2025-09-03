import random
import math

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
    2: {"exp": 70, "stats": 2},
    3: {"exp": 130, "stats": 3},
    4: {"exp": 210, "stats": 4},
    5: {"exp": 310, "stats": 5},
    6: {"exp": 430, "stats": 6},
    7: {"exp": 570, "stats": 7},
    8: {"exp": 730, "stats": 8},
    9: {"exp": 910, "stats": 9},
    10: {"exp": 1200, "stats": 10},
}
num_hab = 20
objetos = {
    "armas": {
        "Espada y escudo de hierro": {"tier": 1, "ataque": (3, 5), "defensa": 3},
        "Hacha de hierro": {"tier": 1, "ataque": (4, 8), "defensa": 2},
        "Maza de hierro": {"tier": 1, "ataque": (3, 9), "defensa": 1},
        "Espada y escudo de acero": {"tier": 2, "ataque": (4, 6), "defensa": 4},
        "Hacha de acero": {"tier": 2, "ataque": (6, 12), "defensa": 2},
        "Maza de acero": {"tier": 2, "ataque": (5, 15), "defensa": 1},
        "Espada y escudode platino": {"tier": 3, "ataque": (5, 7), "defensa": 5},
        "Hacha de platino": {"tier": 3, "ataque": (8, 16), "defensa": 2},
        "Maza de platino": {"tier": 3, "ataque": (7, 21), "defensa": 1},
        "Espada y escudo de diamante": {"tier": 4, "ataque": (6, 8), "defensa": 6},
        "Hacha de diamante": {"tier": 4, "ataque": (10, 20), "defensa": 2},
        "Maza de diamante": {"tier": 4, "ataque": (9, 27), "defensa": 1},
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
    "Orco": {"hp": 30, "oro": (10, 15), "exp": 20, "ataque": (6, 12)},
    "Goblin": {"hp": 15, "oro": (3, 5), "exp": 10, "ataque": (2, 4)},
    "Troll": {"hp": 40, "oro": (10, 20), "exp": 30, "ataque": (8, 16)},
    "Dragón": {"hp": 50, "oro": (20, 30), "exp": 50, "ataque": (12, 24)},
}
menu = {}
i = 1
for nombre_arma, datos in objetos["armas"].items():
    if datos["tier"] == 1:
        menu[i] = nombre_arma
        i += 1
while True:
    #Mostrar menú
    for num, arma in menu.items():
        print(f"{num}. {arma}")
    personaje_arma_inicial = input("¿Qué arma quieres? ")
    #Validar si es número
    if not personaje_arma_inicial.isdigit():
        print("Debes elegir un número")
        continue
    if int(personaje_arma_inicial) not in menu:
        print("Debes elegir un número")
        continue
    personaje_arma_inicial = int(personaje_arma_inicial)
    print("Has elegido " + menu[personaje_arma_inicial])
    break

personaje_arma = menu[personaje_arma_inicial]
personaje_fuerza = stat_base["fuerza"]
personaje_destreza = stat_base["destreza"]
personaje_constitucion = stat_base["Constitución"]
personaje_hp = 20 * personaje_constitucion
salud_maxima = 20 * personaje_constitucion
personaje_level = 1
personaje_oro = 0
personaje_exp = 0


print("Te encuentras en un calabozo con muchas habitaciones, debes encontrar la salida")
print("Caminando por los pasillos encuentras la primera habitación...")
while True:
    if num_hab == 0:
        print("Has ganado")
        break
    elif personaje_hp <= 0:
        print("Has muerto")
        break
    
    else:
        habitacion = random.randint(1, 3)
        if habitacion == 1:
            enemigo = random.choices(list(enemigos.keys()), weights=[0.35, 0.15, 0.4, 0.1, 0.05], k=1)[0]
            stats = enemigos[enemigo]

            enemigo_hp = stats["hp"]
            enemigo_ataque = stats["ataque"]
            enemigo_oro = stats["oro"]
            enemigo_exp = stats["exp"]
            print("Encontraste un " + enemigo)
            while enemigo_hp > 0 and personaje_hp > 0:
                enemigo_dano = random.randint(enemigo_ataque[0], enemigo_ataque[1])
                dano_reduc = (objetos["armas"][personaje_arma]["defensa"] + personaje_destreza) / 10
                dano_total = enemigo_dano * dano_reduc
                if dano_total < 1:
                    dano_total = 1
                else: dano_total = math.ceil(dano_total)
                personaje_hp -= int(dano_total)
                print("El " + enemigo + " te ha atacado y te ha restado " + str(dano_total) + " puntos de vida")
                print("Los puntos de vida de " + personaje + " son " + str(personaje_hp))
                min_dano, max_dano = objetos["armas"][personaje_arma]["ataque"]
                dano = random.randint(min_dano, max_dano) + personaje_fuerza
                enemigo_hp -= dano
                print(f"Atacaste al {enemigo} y le has restado " + str(dano))
                print("Sus puntos de vida son " + str(enemigo_hp))
                if personaje_hp <= 0:
                    break
                elif enemigo_hp <= 0:
                    print("Has derrotado al " + enemigo)
                    personaje_exp += enemigo_exp
                    oro_final = random.randint(enemigo_oro[0], enemigo_oro[1])
                    personaje_oro +=  oro_final
                    print("Has ganado " + str(oro_final) + " oro" )
                    print("Has ganado " + str(enemigo_exp) + " exp" )
                    num_hab -= 1
                    print("Quedan " + str(num_hab) + " habitaciones")
                    print("Caminando por el pasillo encuentras la siguiente habitación...")
                    break
        elif habitacion == 2:
            print("Encuentras un cofre, te acercas para abrirlo...")
            objeto = random.choices(list(objetos.keys()), weights=[0.5, 0.5], k=1)[0]
            if objeto == "armas":
                nombres = list(objetos["armas"].keys())
                tiers = [objetos["armas"][arma]["tier"] for arma in nombres]
                peso = [1 / t for t in tiers]
                arma = random.choices(nombres, weights=peso, k=1)[0]
                print("Has encontrado la " + arma)
                respuesta = input("¿Deseas conservar el arma o descartarla? (s/n) ")
                if respuesta == "s":
                    personaje_arma = arma
                    min_dano, max_dano = objetos["armas"][arma]["ataque"]
                    defensa = objetos["armas"][arma]["defensa"]
                    print("Has equipado " + arma)
                else:
                    print("Has descartado " + arma)
            else:
                pocion = random.choices(list(objetos["pociones"].keys()), weights=[0.5, 0.25, 0.1, 0.05], k=1)[0]
                print("Has encontrado " + pocion)
                salud = objetos["pociones"][pocion]["salud"]
                min_salud, max_salud = salud
                if personaje_hp + random.randint(min_salud, max_salud) <= salud_maxima:
                    personaje_hp += random.randint(min_salud, max_salud)
                    print("Has recuperado " + str(random.randint(min_salud, max_salud)) + " puntos de vida")
                else:
                    personaje_hp = salud_maxima
                    print("Ya tienes la vida máxima")
            num_hab -= 1
            print("Quedan " + str(num_hab) + " habitaciones")
            print("Caminando por el pasillo encuentras la siguiente habitación...")

        elif personaje_exp >= exp_level[personaje_level]["exp"]:
            while (personaje_level + 1) in exp_level and personaje_exp >= exp_level[personaje_level + 1]["exp"]:
                print("Has subido de nivel")
                personaje_level += 1
                personaje_fuerza += exp_level[personaje_level]["stats"]
                personaje_destreza += exp_level[personaje_level]["stats"]
                personaje_constitucion += exp_level[personaje_level]["stats"]
                print(" Tus stats son: Fuerza " + str(personaje_fuerza) + " Destreza " + str(personaje_destreza) + " Constitución " + str(personaje_constitucion))
                print(" Tus puntos de vida son: " + str(personaje_hp))
                print("Tu nivel ahora es: " + str(personaje_level))

        else:
            print("No has encontrado nada")	
            num_hab -= 1
            print("Quedan " + str(num_hab) + " habitaciones")
            print("Caminando por el pasillo encuentras la siguiente habitación...")
    
