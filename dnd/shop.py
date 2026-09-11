"""Tienda del menú: compra sobre el checkpoint del personaje seleccionado."""

from threading import RLock

from character_roster import deserializar_personaje
from item import Arma, Armadura, Secundario
from item_factory import item_factory
from items import objetos


class Shop:
    def __init__(self, roster):
        self.roster = roster
        if not hasattr(roster, "transfer_lock"):
            roster.transfer_lock = RLock()

    def estado(self, personaje_id=None):
        personaje = deserializar_personaje(self.roster.obtener(personaje_id)) if personaje_id else None
        productos = []
        for categoria in ("armas", "secundarios", "armaduras", "pociones"):
            for nombre, datos in objetos[categoria].items():
                item = item_factory.crear(datos["id"])
                productos.append({**datos, "nombre": nombre, "categoria": categoria,
                                  "cumple_requisitos": not hasattr(item, "cumple_requisitos") or
                                  (personaje is not None and item.cumple_requisitos(personaje)),
                                  "cantidad": personaje.inventario.cantidad(item.id) if personaje else 0})
        return {"personajes": [{"id": p["id"], "nombre": p["nombre"]} for p in self.roster.personajes],
                "personaje_id": personaje_id, "oro": personaje.oro if personaje else 0,
                "productos": productos,
                "inventario": personaje.inventario.estado(personaje) if personaje else []}

    def comprar(self, personaje_id, categoria, nombre, cantidad=1):
        if not isinstance(personaje_id, str) or not personaje_id:
            raise ValueError("Selecciona el personaje que realizará la compra.")
        if (not isinstance(categoria, str) or not isinstance(nombre, str)
                or categoria not in {"armas", "secundarios", "armaduras", "pociones"}
                or nombre not in objetos[categoria]):
            raise ValueError("Ese producto no existe.")
        if type(cantidad) is not int or not 1 <= cantidad <= 999:
            raise ValueError("La cantidad debe ser un entero entre 1 y 999.")
        with self.roster.transfer_lock:
            personaje = deserializar_personaje(self.roster.obtener(personaje_id))
            producto = objetos[categoria][nombre]
            coste = producto["precio"] * cantidad
            if personaje.oro < coste:
                raise ValueError("No tienes oro suficiente.")
            # Toda la operación ocurre sobre una copia; no se publica si falla.
            item = personaje.inventario.recolectar(producto["id"], cantidad)
            personaje.oro -= coste
            equipado = False
            if isinstance(item, (Arma, Armadura, Secundario)) and item.cumple_requisitos(personaje):
                compatible = not isinstance(item, Secundario) or not personaje.inventario.arma_equipada.dos_manos
                if compatible:
                    personaje.inventario.equipar(item.id, personaje)
                    personaje.recalcular_por_equipo()
                    equipado = True
            self.roster.save_to_disk(personaje)
            return {**self.estado(personaje_id),
                    "mensaje": f"Compras {nombre} ×{cantidad} por {coste} oro. " +
                    ("Equipo equipado y compra guardada." if equipado else "Compra guardada en el inventario.")}
