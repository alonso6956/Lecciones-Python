"""Fachada del catálogo JSON para combate, tienda y código existente."""

from item import Arma, Armadura, Consumible, Secundario
from item_factory import item_factory


def _construir_catalogo_compatible():
    catalogo = {
        "armas": {},
        "secundarios": {},
        "armaduras": {},
        "pociones": {},
        "materiales": {},
    }
    for item in item_factory.todos():
        if isinstance(item, Arma):
            catalogo["armas"][item.nombre] = {
                "id": item.id,
                "tipo": item.tipo_arma,
                "tier": item.tier,
                "inicial": item.inicial,
                "ataque": item.ataque,
                "defensa": item.defensa,
                "dos_manos": item.dos_manos,
                "precio": item.precio,
                "requisitos": dict(item.requisitos),
            }
        elif isinstance(item, Secundario):
            catalogo["secundarios"][item.nombre] = {
                "id": item.id,
                "tipo": item.tipo_secundario,
                "slot": "mano_secundaria",
                "defensa": item.defensa,
                "precio": item.precio,
                "requisitos": dict(item.requisitos),
                "bonificaciones": dict(item.bonificaciones),
            }
        elif isinstance(item, Armadura):
            catalogo["armaduras"][item.nombre] = {
                "id": item.id,
                "slot": item.slot,
                "defensa": item.defensa,
                "precio": item.precio,
                "requisitos": dict(item.requisitos),
                "bonificaciones": dict(item.bonificaciones),
            }
        elif isinstance(item, Consumible):
            catalogo["pociones"][item.nombre] = {
                "id": item.id,
                "salud": item.valor,
                "precio": item.precio,
            }
        else:
            catalogo["materiales"][item.nombre] = {
                "id": item.id,
                "precio": item.precio,
            }
    return catalogo


objetos = _construir_catalogo_compatible()


def obtener_arma(nombre_arma):
    arma = item_factory.crear(nombre_arma)
    if not isinstance(arma, Arma):
        raise ValueError(f"{nombre_arma!r} no es un arma.")
    return arma


def calcular_factor_arma(nombre_arma, fuerza, destreza):
    return obtener_arma(nombre_arma).factor_escalado(fuerza, destreza)


def obtener_dano_arma(nombre_arma, rng):
    return rng.randint(*obtener_arma(nombre_arma).ataque)


def obtener_defensa_arma(nombre_arma):
    return obtener_arma(nombre_arma).defensa


def obtener_defensa_item(identificador):
    item = item_factory.crear(identificador)
    if not isinstance(item, (Arma, Secundario, Armadura)):
        return 0
    return item.defensa
