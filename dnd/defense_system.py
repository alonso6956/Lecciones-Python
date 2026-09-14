"""Defensa previa a la armadura; el desgaste pertenece a cada copia de equipo."""

from item import Secundario
from item_factory import item_factory
from derived_stats import arma_de, probabilidad_estado


def escudo_de(modelo):
    inventario = getattr(modelo, "inventario", None)
    item = (inventario.secundario_equipado if inventario else
            item_factory.crear(modelo.secundario) if getattr(modelo, "secundario", None) else None)
    return item if isinstance(item, Secundario) and item.tipo_secundario == "escudo" else None


def identidad_equipada(inventario, slot):
    item_id = inventario.equipamiento.get(slot)
    ids = [k for k, v in inventario._instancias.items() if v == item_id]
    indice = int(slot == "mano_secundaria" and inventario.equipamiento.get("mano_principal") == item_id)
    return ids[indice] if len(ids) > indice else None


def durabilidad_escudo(modelo):
    escudo = escudo_de(modelo)
    if not escudo:
        return 0
    inventario = getattr(modelo, "inventario", None)
    if inventario:
        return inventario.estado_durabilidad(identidad_equipada(inventario, "mano_secundaria"))["durabilidad_actual"]
    return getattr(modelo, "durabilidades", {}).get(escudo.id, escudo.durabilidad)


def resolver_defensa(atacante, defensor, dano, *, defendiendo=False, rapido=False,
                     ataque=None, arma=None, ignora=False, rng=None, poderoso=False):
    """No tira azar salvo Ruptura. Parada compara el daño medio sin escalado."""
    escudo = escudo_de(defensor)
    actual = durabilidad_escudo(defensor)
    bandera = lambda nombre: bool(ataque.get(nombre, False) if isinstance(ataque, dict) else getattr(ataque, nombre, False))
    rapido = rapido or bandera("rapido")
    poderoso = poderoso or bandera("poderoso")
    ruptura = False
    if bandera("rompe_guardia") and (defendiendo or actual > 0) and rng:
        base = ataque.get("probabilidad_ruptura", .5) if isinstance(ataque, dict) else getattr(ataque, "probabilidad_ruptura", .5)
        ruptura = rng.random() < probabilidad_estado(base, atacante.impacto, defensor.estabilidad)
    activa = defendiendo and not (rapido or ruptura or ignora or bandera("imparable") or bandera("inbloqueable"))
    bloqueable = not (ignora or bandera("inbloqueable"))
    resultado = {"dano": max(0, dano), "absorbido": 0, "parada": None,
                 "bloqueo_activo": False, "pierde_accion": False, "ruptura": ruptura}
    if escudo and actual > 0 and bloqueable:
        porcentaje = escudo.bloqueo_activo if activa else escudo.absorcion_pasiva
        absorbido = min(actual, max(0, dano) * porcentaje)
        inventario = getattr(defensor, "inventario", None)
        if inventario:
            inventario.establecer_durabilidad(identidad_equipada(inventario, "mano_secundaria"), actual - absorbido)
        else:
            defensor.durabilidades[escudo.id] = actual - absorbido
        resultado.update(dano=max(0, dano - absorbido), absorbido=absorbido,
                         bloqueo_activo=activa and absorbido > 0, pierde_accion=activa and absorbido > 0)
    elif activa and not escudo and not bandera("ignora_parada"):
        principal = arma_de(defensor)
        arma = arma or arma_de(atacante)
        inventario = getattr(defensor, "inventario", None)
        funcional = not inventario or not inventario.estado_durabilidad(identidad_equipada(inventario, "mano_principal"))["roto"]
        if principal and funcional:
            poder = sum(principal.ataque) / 2
            presion = sum(arma.ataque) / 2 * (1.25 if poderoso else 1)
            # Comparaciones directas preservan las fronteras incluso sin presión.
            completa = poder >= presion
            parcial = poder >= .60 * presion
            resultado.update(dano=dano * (.50 if completa else .75 if parcial else .90),
                             parada="completa" if completa else "parcial" if parcial else "debil",
                             poder_parada=poder, presion_ataque=presion, pierde_accion=completa)
    return resultado
