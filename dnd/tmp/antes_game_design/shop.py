"""Tienda del menú: compras y ventas sobre el personaje guardado."""

from threading import RLock
from dataclasses import asdict

from character_roster import deserializar_personaje
from item import Arma, Armadura, Secundario
from item_factory import item_factory
from items import objetos
from economy import precio_venta


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
        ventas = []
        for entrada in personaje.inventario.entradas() if personaje else []:
            item = item_factory.crear(entrada["item_id"])
            precio = precio_venta(item)
            ventas.append({**entrada, "detalles": asdict(item), "precio_venta": precio,
                           "vendible": not entrada["equipado"] and precio > 0,
                           "motivo": "Desequipa el objeto antes de venderlo." if entrada["equipado"] else
                                     ("Este objeto no tiene valor de reventa." if not precio else "")})
        return {"personajes": [{"id": p["id"], "nombre": p["nombre"]} for p in self.roster.personajes],
                "personaje_id": personaje_id, "oro": personaje.oro if personaje else 0,
                "productos": productos,
                "ventas": ventas,
                "inventario": personaje.inventario.estado(personaje) if personaje else []}

    def vender(self, personaje_id, instance_id, cantidad=1):
        if not isinstance(personaje_id, str) or not personaje_id or not isinstance(instance_id, str):
            raise ValueError("Selecciona un personaje y un objeto para vender.")
        if type(cantidad) is not int or not 1 <= cantidad <= 999:
            raise ValueError("La cantidad debe ser un entero entre 1 y 999.")
        with self.roster.transfer_lock:
            personaje = deserializar_personaje(self.roster.obtener(personaje_id))
            entrada = next((e for e in personaje.inventario.entradas() if e["instance_id"] == instance_id), None)
            if entrada is None:
                raise ValueError("El objeto ya no está en el inventario del personaje.")
            if entrada["equipado"]:
                raise ValueError("Desequipa el objeto antes de venderlo. Para el arma principal, equipa otra primero.")
            item = item_factory.crear(entrada["item_id"])
            precio = precio_venta(item)
            if not precio:
                raise ValueError("Este objeto no tiene valor de reventa.")
            personaje.inventario.extraer(instance_id, cantidad)
            ingreso = precio * cantidad
            personaje.oro += ingreso
            self.roster.save_to_disk(personaje)
            return {**self.estado(personaje_id), "mensaje": f"Vendes {item.nombre} ×{cantidad} por {ingreso} oro. Venta guardada."}

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
