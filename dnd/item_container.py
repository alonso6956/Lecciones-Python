"""Contenedor común: stacks simples e identidad persistente del equipo."""

from copy import deepcopy
from uuid import uuid4

from item import Arma, Armadura, Secundario
from item_factory import item_factory


class ItemContainer:
    def _iniciar_contenedor(self, capacidad=None):
        if capacidad is not None and (type(capacidad) is not int or capacidad < 1):
            raise ValueError("Capacidad de inventario inválida.")
        self.capacidad = capacidad
        self._cantidades = {}
        self._instancias = {}
        self._custom = {}
        self._durabilidades = {}

    def estado_durabilidad(self, instance_id):
        item = item_factory.crear(self._instancias[instance_id])
        actual = self._durabilidades.get(instance_id, item.durabilidad)
        return {"durabilidad_actual": actual, "durabilidad_maxima": item.durabilidad,
                "roto": actual <= 0}

    def establecer_durabilidad(self, instance_id, valor):
        import math
        maxima = self.estado_durabilidad(instance_id)["durabilidad_maxima"]
        if type(valor) not in (int, float) or not math.isfinite(valor) or not 0 <= valor <= maxima:
            raise ValueError("Durabilidad inválida.")
        self._durabilidades[instance_id] = valor

    @staticmethod
    def _cantidad_valida(cantidad):
        if type(cantidad) is not int or cantidad < 1:
            raise ValueError("La cantidad debe ser un entero positivo.")

    @staticmethod
    def _unico(item):
        return isinstance(item, (Arma, Armadura, Secundario))

    def cantidad(self, identificador):
        return self._cantidades.get(item_factory.crear(identificador).id, 0)

    @property
    def slots_ocupados(self):
        return sum(cantidad if self._unico(item_factory.crear(clave)) else 1
                   for clave, cantidad in self._cantidades.items())

    def can_accept(self, identificador, cantidad=1):
        self._cantidad_valida(cantidad)
        item = item_factory.crear(identificador)
        if item_factory.datos_instancia(item.id) and (cantidad != 1 or self._cantidades.get(item.id)):
            return False
        extra = cantidad if self._unico(item) else int(item.id not in self._cantidades)
        return self.capacidad is None or self.slots_ocupados + extra <= self.capacidad

    def recolectar(self, identificador, cantidad=1):
        self._cantidad_valida(cantidad)
        item = item_factory.crear(identificador)
        if not self.can_accept(item.id, cantidad):
            raise ValueError("El contenedor no tiene espacio o ya contiene esa instancia única.")
        self._cantidades[item.id] = self._cantidades.get(item.id, 0) + cantidad
        if self._unico(item):
            custom = item_factory.datos_instancia(item.id)
            for _ in range(cantidad):
                self._instancias[item.id if custom else uuid4().hex] = item.id
            if custom:
                self._custom[item.id] = custom
        return item

    def extraer(self, instance_id, cantidad=1):
        self._cantidad_valida(cantidad)
        item_id = self._instancias.get(instance_id, instance_id)
        item = item_factory.crear(item_id)
        if self._unico(item) and (instance_id not in self._instancias or cantidad != 1):
            raise ValueError("Selecciona una instancia de equipo y cantidad 1.")
        if self._cantidades.get(item.id, 0) < cantidad:
            raise ValueError("No hay suficientes objetos en el origen.")
        movido = {"instance_id": instance_id, "item_id": item.id, "cantidad": cantidad,
                  "custom_data": deepcopy(self._custom.get(item.id))}
        if self._unico(item):
            movido.update(self.estado_durabilidad(instance_id))
        self._cantidades[item.id] -= cantidad
        if not self._cantidades[item.id]:
            del self._cantidades[item.id]
            self._custom.pop(item.id, None)
        self._instancias.pop(instance_id, None)
        self._durabilidades.pop(instance_id, None)
        return movido

    def insertar(self, entrada):
        item_id, cantidad = entrada["item_id"], entrada["cantidad"]
        if entrada.get("custom_data"):
            if entrada["custom_data"]["id"] != item_id or entrada["instance_id"] != item_id:
                raise ValueError("Identidad del equipo inconsistente.")
            item_factory.registrar_instancia(entrada["custom_data"])
        if entrada["instance_id"] in self._instancias:
            raise ValueError("La instancia ya está en el destino.")
        previos = set(self._instancias)
        item = self.recolectar(item_id, cantidad)
        if self._unico(item):
            for nuevo in set(self._instancias) - previos:
                del self._instancias[nuevo]
            self._instancias[entrada["instance_id"]] = item_id
            self.establecer_durabilidad(entrada["instance_id"], entrada.get("durabilidad_actual", item.durabilidad))

    def _serializar_contenedor(self):
        return {"items": dict(self._cantidades), "instancias": dict(self._instancias),
                "custom": deepcopy(self._custom), "capacidad": self.capacidad,
                "durabilidades": dict(self._durabilidades)}

    def _restaurar_identidades(self, datos):
        if "instancias" in datos:
            instancias = datos["instancias"]
            if not isinstance(instancias, dict) or any(not isinstance(k, str) or not k for k in instancias):
                raise ValueError("Instancias inválidas.")
            esperadas = {k: v for k, v in self._cantidades.items() if self._unico(item_factory.crear(k))}
            reales = {}
            for instance_id, item_id in instancias.items():
                reales[item_id] = reales.get(item_id, 0) + 1
                if item_id in self._custom and instance_id != item_id:
                    raise ValueError("ID de instancia procedural inconsistente.")
            if reales != esperadas:
                raise ValueError("Las instancias no coinciden con el inventario.")
            self._instancias = dict(instancias)
        durabilidades = datos.get("durabilidades", {})
        if not isinstance(durabilidades, dict) or any(k not in self._instancias for k in durabilidades):
            raise ValueError("Identidades de durabilidad inválidas.")
        for clave, valor in durabilidades.items():
            self.establecer_durabilidad(clave, valor)

    def entradas(self):
        filas = []
        for item_id, cantidad in self._cantidades.items():
            item = item_factory.crear(item_id)
            ids = [k for k, v in self._instancias.items() if v == item_id] if self._unico(item) else [item_id]
            for instance_id in ids:
                filas.append({"instance_id": instance_id, "item_id": item_id,
                    **(self.estado_durabilidad(instance_id) if self._unico(item) else {}),
                    "nombre": item.nombre, "categoria": type(item).__name__.lower(),
                    "cantidad": 1 if self._unico(item) else cantidad,
                    "custom_data": deepcopy(self._custom.get(item_id)),
                    "equipado": instance_id == ids[0] and item_id in getattr(self, "_equipamiento", {}).values(),
                    "slot": next((k for k, v in getattr(self, "_equipamiento", {}).items() if v == item_id), None)})
        return filas


class SharedVault(ItemContainer):
    def __init__(self, datos=None, capacidad=None):
        if capacidad is None:
            from crafting import crafting_data
            capacidad = crafting_data()["vault"]["capacidad"]
        self._iniciar_contenedor(capacidad)
        if datos:
            if type(datos.get("capacidad")) is not int or datos["capacidad"] < 1:
                raise ValueError("Capacidad del vault inválida.")
            self.capacidad = datos["capacidad"]
            for custom in datos.get("custom", {}).values():
                item_factory.registrar_instancia(custom)
            for item_id, cantidad in datos["items"].items():
                self.recolectar(item_id, cantidad)
            self._restaurar_identidades(datos)

    def serializar(self):
        return self._serializar_contenedor()

    def estado(self):
        return {"items": self.entradas(), "capacidad": self.capacidad, "ocupados": self.slots_ocupados}
