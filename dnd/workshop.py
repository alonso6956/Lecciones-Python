"""Operaciones de taller sobre copias; publicación tras confirmar el guardado."""

from copy import deepcopy
from dataclasses import asdict
from threading import RLock

from character_roster import deserializar_personaje
from crafting import crafting_data, fabricar, previsualizar_arma, progreso_crafteo
from item_container import SharedVault
from item_factory import item_factory


class Workshop:
    def __init__(self, roster):
        self.roster = roster
        if not hasattr(roster, "transfer_lock"):
            roster.transfer_lock = RLock()

    @staticmethod
    def _entradas(contenedor):
        entradas = contenedor.entradas()
        for entrada in entradas:
            entrada["detalles"] = asdict(item_factory.crear(entrada["item_id"]))
            entrada["transferible"] = (not entrada["equipado"]
                and entrada["item_id"] not in crafting_data()["vault"]["bloqueados"]
                and item_factory.permite_vault(entrada["item_id"]))
        return entradas

    def previsualizar(self, personaje_id, tipo, material, componente=None):
        personaje = deserializar_personaje(self.roster.obtener(personaje_id))
        return previsualizar_arma(personaje, tipo, material, componente)

    def estado(self, personaje_id=None):
        datos = crafting_data()
        personaje = deserializar_personaje(self.roster.obtener(personaje_id)) if personaje_id else None
        return {"personajes": [{"id": p["id"], "nombre": p["nombre"]} for p in self.roster.personajes],
                "personaje_id": personaje_id, "inventario": self._entradas(personaje.inventario) if personaje else [],
                "crafting_tier": personaje.crafting_tier if personaje else 1,
                "crafting_exp": personaje.crafting_exp if personaje else 0,
                "progreso": progreso_crafteo(personaje.crafting_exp if personaje else 0),
                "vault": {**self.roster.vault.estado(), "items": self._entradas(self.roster.vault)},
                "catalogo": {"tipos": {k: {"nombre": v["nombre"]} for k, v in datos["tipos"].items()},
                             "materiales": {k: {"nombre": v["nombre"]} for k, v in datos["materiales"].items()},
                             "afijos": {k: {"nombre": v["nombre"], "efecto": v["id"]} for k, v in datos["afijos"].items()}},
                "coste_material": (personaje.crafting_tier if personaje else 1) * datos["coste_material_por_tier"]}

    def ejecutar(self, accion, personaje_id, **datos):
        with self.roster.transfer_lock:
            personaje = deserializar_personaje(self.roster.obtener(personaje_id))
            vault = SharedVault(self.roster.vault.serializar())
            resultado = None
            transferidos = 0
            if accion in {"depositar_materiales", "depositar_todo"}:
                entradas = [e for e in self._entradas(personaje.inventario) if e["transferible"]
                            and (accion == "depositar_todo" or e["categoria"] == "material")]
                if not entradas:
                    raise ValueError("No hay objetos transferibles para depositar.")
                for entrada in entradas:
                    if not vault.can_accept(entrada["item_id"], entrada["cantidad"]):
                        raise ValueError("El vault no tiene espacio para todo el depósito. No se movió ningún objeto.")
                    vault.insertar(personaje.inventario.extraer(entrada["instance_id"], entrada["cantidad"]))
                    transferidos += entrada["cantidad"]
            elif accion in {"depositar", "retirar"}:
                origen, destino = (personaje.inventario, vault) if accion == "depositar" else (vault, personaje.inventario)
                instance_id = datos.get("instance_id")
                if not isinstance(instance_id, str):
                    raise ValueError("Selecciona un objeto válido.")
                entrada = next((e for e in origen.entradas() if e["instance_id"] == instance_id), None)
                if entrada is None:
                    raise ValueError("El objeto no está en el origen.")
                if entrada["equipado"]:
                    raise ValueError("Desequipa el objeto antes de depositarlo.")
                item_id = entrada["item_id"]
                if item_id in crafting_data()["vault"]["bloqueados"] or not item_factory.permite_vault(item_id):
                    raise ValueError("Este objeto no puede transferirse al vault.")
                cantidad = datos.get("cantidad", 1)
                if not destino.can_accept(item_id, cantidad):
                    raise ValueError("El destino no tiene capacidad para esos objetos.")
                movido = origen.extraer(instance_id, cantidad)
                destino.insertar(movido)
            elif accion == "fabricar":
                resultado = fabricar(personaje, datos.get("tipo"), datos.get("material"), datos.get("componente"))
            elif accion == "nombrar":
                item_id, nombre = datos.get("item_id"), datos.get("nombre")
                if not isinstance(item_id, str) or item_id not in personaje.inventario._custom:
                    raise ValueError("Selecciona un arma fabricada de este personaje.")
                if not isinstance(nombre, str) or not 1 <= len(nombre.strip()) <= 60 or any(ord(c) < 32 for c in nombre):
                    raise ValueError("El nombre debe contener de 1 a 60 caracteres sin controles.")
                nuevo = deepcopy(personaje.inventario._custom[item_id])
                nuevo["nombre"] = nombre.strip()
                personaje.inventario._custom[item_id] = nuevo
                item_factory.registrar_instancia(nuevo)
            elif accion == "equipar":
                personaje.inventario.equipar(datos.get("item_id"), personaje)
                personaje.recalcular_por_equipo()
            elif accion == "desequipar":
                personaje.inventario.desequipar(datos.get("slot"))
                personaje.recalcular_por_equipo()
            else:
                raise ValueError("Operación de taller no válida.")
            try:
                self.roster.save_to_disk(personaje, vault)
            except Exception:
                # Revierte también la caché de nombres ante un fallo de disco.
                for p in self.roster.personajes:
                    for custom in p.get("custom", {}).values():
                        item_factory.registrar_instancia(custom)
                raise
            estado = self.estado(personaje_id)
            estado["arma_creada"] = resultado
            estado["transferidos"] = transferidos
            return estado
