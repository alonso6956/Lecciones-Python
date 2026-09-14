"""Reparación completa en taller sin regenerar las propiedades del objeto."""

import math
from item_factory import item_factory
from item import Armadura


def cotizar_reparacion(inventario, instance_id):
    if not isinstance(instance_id, str) or instance_id not in inventario._instancias:
        raise ValueError("Selecciona una instancia de equipo del inventario.")
    item = item_factory.crear(inventario._instancias[instance_id])
    estado = inventario.estado_durabilidad(instance_id)
    maxima, actual = estado["durabilidad_maxima"], estado["durabilidad_actual"]
    perdida = 1 - actual / maxima if maxima else 0
    material = item.material or "hierro"
    modificador = {"hierro": 1, "bronce": 1, "acero": 1.25, "plata": 1.5, "obsidiana": 2}.get(material, 1)
    calidad = {"defectuosa": .8, "comun": 1, "buena": 1.1, "excelente": 1.35, "maestra": 1.5}.get(item.calidad, 1)
    tipo = 1.25 if isinstance(item, Armadura) else 1
    coste = math.ceil(50 * item.tier * perdida * modificador * calidad * tipo)
    return {**estado, "coste_oro": coste, "material": "material_" + material,
            "cantidad_material": math.ceil(item.tier * perdida), "reparable": perdida > 0}


def reparar(personaje, instance_id, vault=None):
    inventario = personaje.inventario
    precio = cotizar_reparacion(inventario, instance_id)
    if not precio["reparable"]:
        raise ValueError("El objeto ya tiene toda su durabilidad.")
    material, cantidad = precio["material"], precio["cantidad_material"]
    propios = inventario.cantidad(material)
    if personaje.oro < precio["coste_oro"]:
        raise ValueError("No tienes suficiente oro para reparar.")
    if propios + (vault.cantidad(material) if vault else 0) < cantidad:
        raise ValueError("No hay suficientes materiales para reparar.")
    usados = min(propios, cantidad)
    if usados:
        inventario.extraer(material, usados)
    if usados < cantidad:
        vault.extraer(material, cantidad - usados)
    personaje.oro -= precio["coste_oro"]
    inventario.establecer_durabilidad(instance_id, precio["durabilidad_maxima"])
    personaje.recalcular_por_equipo()
    return precio
