"""Inventario y equipamiento serializables por slot de guardado."""

from item import Arma, Armadura, Consumible, Secundario
from item_factory import ALIASES_LEGACY, item_factory


SLOTS_EQUIPO = (
    "mano_principal",
    "mano_secundaria",
    "casco",
    "pecho",
    "brazos",
    "piernas",
)


class Inventario:
    def __init__(self, items=None, arma_equipada=None, equipamiento=None):
        self._cantidades = {}
        for item_id, cantidad in (items or {}).items():
            item_id = ALIASES_LEGACY.get(item_id, item_id)
            self.recolectar(item_id, cantidad)

        self._equipamiento = {slot: None for slot in SLOTS_EQUIPO}
        if equipamiento:
            for slot, item_id in equipamiento.items():
                if slot in self._equipamiento and item_id:
                    self._equipamiento[slot] = ALIASES_LEGACY.get(item_id, item_id)
        elif arma_equipada:
            self._equipamiento["mano_principal"] = ALIASES_LEGACY.get(
                arma_equipada, arma_equipada
            )
        self._validar_equipamiento()

    @property
    def arma_equipada(self):
        item_id = self._equipamiento["mano_principal"]
        return item_factory.crear(item_id) if item_id else None

    @property
    def secundario_equipado(self):
        item_id = self._equipamiento["mano_secundaria"]
        return item_factory.crear(item_id) if item_id else None

    @property
    def equipamiento(self):
        return dict(self._equipamiento)

    def _validar_equipamiento(self):
        for slot, item_id in self._equipamiento.items():
            if not item_id:
                continue
            item = item_factory.crear(item_id)
            if self._cantidades.get(item.id, 0) < 1:
                raise ValueError(f"El objeto equipado en {slot} no está en el inventario.")
            if self._slot_de(item) != slot:
                raise ValueError(f"El objeto {item.nombre} no corresponde al slot {slot}.")

    @staticmethod
    def _slot_de(item):
        if isinstance(item, Arma):
            return "mano_principal"
        if isinstance(item, Secundario):
            return "mano_secundaria"
        if isinstance(item, Armadura):
            return item.slot
        raise ValueError("Ese ítem no se puede equipar.")

    def cantidad(self, identificador):
        item = item_factory.crear(identificador)
        return self._cantidades.get(item.id, 0)

    def recolectar(self, identificador, cantidad=1):
        item = item_factory.crear(identificador)
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad < 1:
            raise ValueError("La cantidad debe ser un entero positivo.")
        self._cantidades[item.id] = self._cantidades.get(item.id, 0) + cantidad
        return item

    def equipar(self, identificador, personaje):
        item = item_factory.crear(identificador)
        slot = self._slot_de(item)
        if self.cantidad(item.id) < 1:
            raise ValueError("El objeto no está en el inventario.")
        if not item.cumple_requisitos(personaje):
            raise ValueError("No cumples los requisitos para equipar ese objeto.")
        if isinstance(item, Secundario):
            principal = self.arma_equipada
            if principal and principal.dos_manos:
                raise ValueError("Un arma de dos manos no permite usar mano secundaria.")
        if isinstance(item, Arma) and item.dos_manos:
            self._equipamiento["mano_secundaria"] = None
        self._equipamiento[slot] = item.id
        return item

    def desequipar(self, slot):
        if slot not in SLOTS_EQUIPO:
            raise ValueError("El slot de equipamiento no existe.")
        if slot == "mano_principal":
            raise ValueError("Debes mantener un arma en la mano principal.")
        item_id = self._equipamiento[slot]
        if not item_id:
            raise ValueError("Ese slot ya está vacío.")
        self._equipamiento[slot] = None
        return item_factory.crear(item_id)

    def item_en_slot(self, slot):
        if slot not in SLOTS_EQUIPO:
            raise ValueError("El slot de equipamiento no existe.")
        item_id = self._equipamiento[slot]
        return item_factory.crear(item_id) if item_id else None

    def cumple_tipo_equipo(self, tipo_requerido):
        arma = self.arma_equipada
        secundario = self.secundario_equipado
        return bool(
            (arma and arma.tipo_arma == tipo_requerido)
            or (secundario and secundario.tipo_secundario == tipo_requerido)
        )

    def defensa_equipo(self):
        total = 0
        for item_id in self._equipamiento.values():
            if not item_id:
                continue
            item = item_factory.crear(item_id)
            total += getattr(item, "defensa", 0)
        return total

    def bonificaciones_atributos(self):
        total = {"fuerza": 0, "destreza": 0, "constitucion": 0}
        for item_id in self._equipamiento.values():
            if not item_id:
                continue
            item = item_factory.crear(item_id)
            for estadistica, valor in getattr(item, "bonificaciones", {}).items():
                total[estadistica] = total.get(estadistica, 0) + valor
        return total

    def usar(self, identificador, personaje):
        item = item_factory.crear(identificador)
        if not isinstance(item, Consumible):
            raise ValueError("Ese ítem no es consumible.")
        if self.cantidad(item.id) < 1:
            raise ValueError("No tienes ese consumible.")
        if item.efecto != "curacion":
            raise ValueError("El efecto del consumible no está soportado.")
        recuperado = personaje.curar(item.valor)
        self._cantidades[item.id] -= 1
        if self._cantidades[item.id] == 0:
            del self._cantidades[item.id]
        return item, recuperado

    def serializar(self):
        return {
            "items": dict(self._cantidades),
            "equipamiento": dict(self._equipamiento),
            "arma_equipada": self._equipamiento["mano_principal"],
        }

    @classmethod
    def deserializar(cls, datos):
        if not isinstance(datos, dict) or not isinstance(datos.get("items"), dict):
            raise ValueError("Los datos del inventario no son válidos.")
        return cls(
            datos["items"],
            datos.get("arma_equipada"),
            datos.get("equipamiento"),
        )

    def estado_equipamiento(self):
        resultado = {}
        for slot, item_id in self._equipamiento.items():
            item = item_factory.crear(item_id) if item_id else None
            resultado[slot] = (
                {
                    "id": item.id,
                    "nombre": item.nombre,
                    "clase": item.__class__.__name__.lower(),
                    "defensa": getattr(item, "defensa", 0),
                    "bonificaciones": dict(getattr(item, "bonificaciones", {})),
                }
                if item
                else None
            )
        return resultado

    def estado(self, personaje=None):
        equipados = {item_id for item_id in self._equipamiento.values() if item_id}
        resultado = []
        for item_id, cantidad in self._cantidades.items():
            item = item_factory.crear(item_id)
            datos = {
                "id": item.id,
                "nombre": item.nombre,
                "clase": item.__class__.__name__.lower(),
                "cantidad": cantidad,
                "equipado": item_id in equipados,
            }
            if isinstance(item, (Arma, Secundario, Armadura)):
                datos.update(
                    slot=self._slot_de(item),
                    defensa=item.defensa,
                    requisitos=dict(item.requisitos),
                    puede_equipar=not personaje or item.cumple_requisitos(personaje),
                )
            if isinstance(item, Arma):
                datos.update(
                    tipo_arma=item.tipo_arma,
                    ataque=list(item.ataque),
                    dos_manos=item.dos_manos,
                )
            elif isinstance(item, Secundario):
                datos.update(tipo_secundario=item.tipo_secundario)
            elif isinstance(item, Armadura):
                datos.update(bonificaciones=dict(item.bonificaciones))
            resultado.append(datos)
        return resultado
