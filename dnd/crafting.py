"""Generación procedural con presupuesto constante y tablas externas."""

import json
import random
from copy import deepcopy
from dataclasses import asdict
from functools import lru_cache
from uuid import uuid4

from item_factory import _ruta_recurso, item_factory


@lru_cache(maxsize=1)
def crafting_data():
    with _ruta_recurso("crafting.json").open(encoding="utf-8") as archivo:
        return json.load(archivo)


def generar_arma(personaje, tipo, material, componente=None, rng=None):
    rng = rng or random.SystemRandom()
    arma = _disenar_arma(personaje.crafting_tier, tipo, material, componente,
                         rng.choice(list(crafting_data()["perfiles"])))
    arma["id"] = "craft_" + uuid4().hex
    return arma


def _disenar_arma(tier, tipo, material, componente, perfil):
    """Cálculo compartido por fabricación y preview; no crea instancias."""
    datos = crafting_data()
    if tipo not in datos["tipos"] or material not in datos["materiales"]:
        raise ValueError("Tipo o material de fabricación inválido.")
    if componente is not None and componente not in datos["afijos"]:
        raise ValueError("Componente de fabricación inválido.")
    presupuesto = datos["tiers"][str(tier)]
    plantilla, metal = datos["tipos"][tipo], datos["materiales"][material]
    base = [p + m for p, m in zip(plantilla["distribucion"], metal["cambios"])]
    # Transfiere poder entre estadísticas. Cada desviación relativa es <=10%.
    cambios = datos["perfiles"][perfil]
    aumentos = sum(b * max(0, c) for b, c in zip(base, cambios))
    reducciones = sum(b * max(0, -c) for b, c in zip(base, cambios))
    transferencia = min(aumentos, reducciones)
    distribucion = [b + (b*c*transferencia/(aumentos if c > 0 else reducciones) if c and transferencia else 0)
                    for b, c in zip(base, cambios)]
    afijo = deepcopy(datos["afijos"][componente]) if componente else {}
    reserva = afijo.get("coste", 0) + (0.03 if metal.get("bonus_sobrenatural") else 0)
    puntos = [p * presupuesto / 100 * (1 - reserva) for p in distribucion]
    dano, velocidad, critico, penetracion = puntos
    arma = asdict(item_factory.crear(plantilla["base"]))
    arma.update(id="", nombre=f"{plantilla['nombre']} de {metal['nombre']} sin nombre",
                precio=0, tipo_arma=tipo, tier=tier, inicial=False, requisitos={},
                ataque=[max(1, round(dano / 10 * 0.8)), max(2, round(dano / 10 * 1.2))],
                dos_manos=tipo in {"maza", "lanza"},
                peso=metal["peso"], durabilidad=metal["durabilidad"],
                velocidad=round(0.7 + velocidad / 100, 4), critico=round(critico / 200, 4),
                penetracion=round(penetracion / 2, 4), alcance=plantilla["alcance"],
                material=material, perfil=perfil, afijo=afijo, presupuesto=presupuesto,
                distribucion=puntos, bonus_sobrenatural=metal.get("bonus_sobrenatural", 0))
    if afijo:
        arma["afijo"]["dano"] *= tier
    return arma


def progreso_crafteo(experiencia):
    datos = crafting_data()
    umbrales = datos["experiencia_por_tier"]
    tier = sum(experiencia >= minimo for minimo in umbrales)
    siguiente = umbrales[tier] if tier < len(umbrales) else None
    actual = experiencia - umbrales[tier - 1]
    objetivo = siguiente - umbrales[tier - 1] if siguiente is not None else None
    return {"tier": tier, "actual": actual, "objetivo": objetivo,
            "porcentaje": round(100 * actual / objetivo, 1) if objetivo else 100,
            "siguiente_tier": tier + 1 if siguiente is not None else None,
            "siguiente_coste": (tier + 1) * datos["coste_material_por_tier"] if siguiente is not None else None}


def previsualizar_arma(personaje, tipo, material, componente=None):
    datos = crafting_data()
    variantes = [_disenar_arma(personaje.crafting_tier, tipo, material, componente, perfil)
                 for perfil in datos["perfiles"]]
    arma = variantes[0]
    coste = personaje.crafting_tier * datos["coste_material_por_tier"]
    recursos = [{"item_id": "material_" + material, "nombre": datos["materiales"][material]["nombre"], "necesario": coste}]
    if componente:
        recursos.append({"item_id": componente, "nombre": datos["afijos"][componente]["nombre"], "necesario": 1})
    for recurso in recursos:
        recurso["disponible"] = personaje.inventario.cantidad(recurso["item_id"])
    suficientes = all(r["disponible"] >= r["necesario"] for r in recursos)
    # Los stacks consumidos por completo liberan un espacio antes de crear el arma.
    capacidad = personaje.inventario.capacidad
    espacios = personaje.inventario.slots_ocupados - sum(r["disponible"] == r["necesario"] for r in recursos) + 1
    cabe = capacidad is None or espacios <= capacidad
    return {"nombre": f"{datos['tipos'][tipo]['nombre']} de {datos['materiales'][material]['nombre']}",
            "tipo_arma": tipo, "material": material, "tier": arma["tier"],
            "ataque": {"minimo": [min(a["ataque"][0] for a in variantes), max(a["ataque"][0] for a in variantes)],
                       "maximo": [min(a["ataque"][1] for a in variantes), max(a["ataque"][1] for a in variantes)]},
            "rangos": {k: [min(a[k] for a in variantes), max(a[k] for a in variantes)]
                       for k in ("velocidad", "critico", "penetracion")},
            "durabilidad": arma["durabilidad"], "peso": arma["peso"], "alcance": arma["alcance"],
            "requisitos": arma["requisitos"], "afijo": arma["afijo"], "recursos": recursos,
            "puede_fabricar": suficientes and cabe, "espacio_disponible": cabe}


def fabricar(personaje, tipo, material, componente=None, rng=None):
    datos = crafting_data()
    # Se valida la selección antes de consultar o consumir recursos.
    if not isinstance(tipo, str) or not isinstance(material, str) or (componente is not None and not isinstance(componente, str)):
        raise ValueError("Selección de crafteo inválida.")
    if tipo not in datos["tipos"] or material not in datos["materiales"] or (componente is not None and componente not in datos["afijos"]):
        raise ValueError("Selección de crafteo inválida.")
    coste = personaje.crafting_tier * datos["coste_material_por_tier"]
    recurso = "material_" + material
    if personaje.inventario.cantidad(recurso) < coste or (componente and not personaje.inventario.cantidad(componente)):
        raise ValueError("No tienes suficientes materiales o componentes en el inventario.")
    from inventario import Inventario
    nuevo = Inventario.deserializar(personaje.inventario.serializar())
    nuevo.extraer(recurso, coste)
    if componente:
        nuevo.extraer(componente)
    arma = generar_arma(personaje, tipo, material, componente, rng)
    item_factory.registrar_instancia(arma)
    nuevo.recolectar(arma["id"])
    personaje.inventario = nuevo
    personaje.crafting_exp += 1
    return arma


def botin_crafteo(rng):
    datos = crafting_data()
    botin = []
    if rng.random() < datos["loot"]["probabilidad_material"]:
        botin.append(("material_" + rng.choice(list(datos["materiales"])), rng.randint(*datos["loot"]["cantidad_material"])))
    if rng.random() < datos["loot"]["probabilidad_componente"]:
        botin.append((rng.choice(list(datos["afijos"])), 1))
    return botin
