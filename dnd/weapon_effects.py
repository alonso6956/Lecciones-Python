"""Propiedades procedurales interpretadas igual por ambos combates."""

from item_factory import item_factory


def armadura_tras_penetracion(modelo, armadura):
    return max(0, armadura - item_factory.crear(modelo.arma).penetracion)


def modificar_golpe(modelo, objetivo, dano, rng):
    arma = item_factory.crear(modelo.arma)
    critico = arma.critico > 0 and rng.random() < arma.critico
    if critico:
        dano *= 1.5
    if getattr(objetivo, "raza", None) in {"Esqueleto", "Guardián"}:
        dano *= 1 + arma.bonus_sobrenatural
    return dano, critico


def activar_afijo(modelo, objetivo, rng):
    afijo = item_factory.crear(modelo.arma).afijo
    if not afijo or objetivo.hp <= 0 or rng.random() >= afijo["probabilidad"]:
        return None
    # El mismo efecto se renueva, no se acumula sin límite por golpes múltiples.
    objetivo.efectos_arma[afijo["id"]] = {"dano": afijo["dano"], "turnos": afijo["turnos"]}
    return afijo["id"]


def ticks_afijos(modelo):
    for efecto, estado in list(modelo.efectos_arma.items()):
        dano = min(max(0, modelo.hp), estado["dano"])
        modelo.hp -= dano
        estado["turnos"] -= 1
        if estado["turnos"] <= 0:
            del modelo.efectos_arma[efecto]
        if dano:
            yield efecto, dano
