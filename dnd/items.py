"""Fachada del catálogo JSON para combate, tienda y código existente."""

from combat_formulas import calcular_mitigacion_armadura
from item import Arma, Armadura, Consumible, Secundario
from item_factory import item_factory
from pasiva_factory import pasiva_factory


def datos_pasiva_arma(arma):
    pasiva = pasiva_factory.para_arma(arma)
    if not pasiva:
        return None
    return {
        "nombre": pasiva.nombre,
        "descripcion": pasiva.descripcion,
        "efecto": pasiva.efecto,
        "valor": pasiva.valor,
        "probabilidad": pasiva.probabilidad,
        "dano_sangrado": pasiva.dano_sangrado,
        "numero_ataques": pasiva.numero_ataques,
    }


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
                "dos_manos": item.dos_manos,
                "estadistica_escalado": item.estadistica_escalado,
                "crecimiento_por_punto": item.crecimiento_por_punto,
                "pasiva": datos_pasiva_arma(item),
                "precio": item.precio,
                "requisitos": dict(item.requisitos),
            }
        elif isinstance(item, Secundario):
            catalogo["secundarios"][item.nombre] = {
                "id": item.id,
                "tipo": item.tipo_secundario,
                "slot": "mano_secundaria",
                "tier": item.tier,
                "probabilidad_bloqueo": item.probabilidad_bloqueo,
                "porcentaje_dano_bloqueado": item.porcentaje_dano_bloqueado,
                "peso": item.peso,
                "durabilidad": item.durabilidad,
                "precio": item.precio,
                "requisitos": dict(item.requisitos),
                "bonificaciones": dict(item.bonificaciones),
            }
        elif isinstance(item, Armadura):
            catalogo["armaduras"][item.nombre] = {
                "id": item.id,
                "slot": item.slot,
                "defensa": item.defensa,
                "mitigacion": calcular_mitigacion_armadura(item.defensa),
                "peso": item.peso,
                "durabilidad": item.durabilidad,
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
                "descripcion": item.descripcion,
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
    """Compatibilidad legacy: las armas ya no conceden armadura."""
    obtener_arma(nombre_arma)
    return 0


def obtener_defensa_item(identificador):
    item = item_factory.crear(identificador)
    if not isinstance(item, Armadura):
        return 0
    return item.defensa
