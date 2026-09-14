"""Precios de fabricación y reventa derivados del catálogo actual."""

from math import ceil

from item import Arma, Armadura, Secundario
from item_factory import item_factory


def valor_fabricacion(base_id, tier):
    base = item_factory.crear(base_id)
    def comparable(item):
        if type(item) is not type(base):
            return False
        if isinstance(base, Arma):
            return item.tipo_arma == base.tipo_arma and not item.inicial
        if isinstance(base, Armadura):
            return item.slot == base.slot
        return isinstance(base, Secundario) and item.tipo_secundario == base.tipo_secundario

    candidatos = [i for i in item_factory.todos() if comparable(i) and i.tier <= tier]
    referencia = max(candidatos, key=lambda i: (i.tier, i.precio))
    # El salto actual de armas I -> II es 50 -> 70: prolonga esa curva
    # cuando aún no existe una pieza de ese tier en la tienda.
    niveles = tier - referencia.tier
    return ceil(referencia.precio * 7 ** niveles / 5 ** niveles)


def coste_fabricacion(valor):
    return (valor * 3 + 1) // 2


def precio_venta(item):
    if item.id.startswith("craft_"):
        return max(0, item.precio // 2)
    # El arma gratuita de cada personaje no puede convertirse en oro
    # transfiriéndola a través de la bóveda y creando personajes nuevos.
    if getattr(item, "inicial", False) or not item_factory.permite_vault(item.id):
        return 0
    return max(0, item.precio // 2)
