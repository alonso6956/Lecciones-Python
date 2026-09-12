"""Generación procedural con presupuesto constante y tablas externas."""

import json
import random
from copy import deepcopy
from dataclasses import asdict
from functools import lru_cache
from uuid import uuid4

from item_factory import _ruta_recurso, item_factory
from economy import coste_fabricacion, valor_fabricacion


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
    if not isinstance(tipo, str) or not isinstance(material, str) or tipo not in datos["tipos"] or material not in datos["materiales"]:
        raise ValueError("Tipo o material de fabricación inválido.")
    if componente is not None and (not isinstance(componente, str) or componente not in datos["afijos"]):
        raise ValueError("Componente de fabricación inválido.")
    presupuesto = datos["tiers"][str(tier)]
    plantilla, metal = datos["tipos"][tipo], datos["materiales"][material]
    if plantilla.get("categoria") in {"armadura", "secundario"}:
        if componente:
            raise ValueError("Los componentes ofensivos solo pueden usarse en armas.")
        return _disenar_proteccion(tier, plantilla, material, perfil)
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
                precio=valor_fabricacion(plantilla["base"], tier), tipo_arma=tipo, tier=tier, inicial=False, requisitos={},
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


def _disenar_proteccion(tier, plantilla, material, perfil):
    """Mejora los modelos existentes; más protección implica más peso."""
    datos = crafting_data()
    metal = datos["materiales"][material]
    pieza = asdict(item_factory.crear(plantilla["base"]))
    balance = datos["protecciones"]
    variacion = balance["perfiles"][perfil]
    factor_metal = balance["materiales"][material]
    poder = datos["tiers"][str(tier)] / datos["tiers"]["1"] * balance["mejora_base"] * factor_metal * variacion
    pieza.update(id="", nombre=f"{plantilla['nombre']} de {metal['nombre']} sin nombre",
                 precio=valor_fabricacion(plantilla["base"], tier), tier=tier,
                 material=material, perfil=perfil,
                 peso=round(pieza["peso"] * metal["peso"] / 5 * variacion, 2),
                 durabilidad=round(metal["durabilidad"] * variacion))
    if plantilla["categoria"] == "armadura":
        pieza["defensa"] = max(pieza["defensa"] + 1, round(pieza["defensa"] * poder))
    else:
        pieza["probabilidad_bloqueo"] = round(min(balance["bloqueo_maximo"], pieza["probabilidad_bloqueo"] * poder), 4)
        pieza["porcentaje_dano_bloqueado"] = round(min(balance["reduccion_maxima"], pieza["porcentaje_dano_bloqueado"] * poder), 4)
    return pieza


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


def previsualizar_arma(personaje, tipo, material, componente=None, vault=None):
    datos = crafting_data()
    variantes = [_disenar_arma(personaje.crafting_tier, tipo, material, componente, perfil)
                 for perfil in datos["perfiles"]]
    arma = variantes[0]
    coste = personaje.crafting_tier * datos["coste_material_por_tier"]
    recursos = [{"item_id": "material_" + material, "nombre": datos["materiales"][material]["nombre"], "necesario": coste}]
    if componente:
        recursos.append({"item_id": componente, "nombre": datos["afijos"][componente]["nombre"], "necesario": 1})
    for recurso in recursos:
        recurso["inventario"] = personaje.inventario.cantidad(recurso["item_id"])
        recurso["vault"] = vault.cantidad(recurso["item_id"]) if vault is not None else 0
        recurso["disponible"] = recurso["inventario"] + recurso["vault"]
    suficientes = all(r["disponible"] >= r["necesario"] for r in recursos)
    # Los stacks consumidos por completo liberan un espacio antes de crear el arma.
    capacidad = personaje.inventario.capacidad
    espacios = personaje.inventario.slots_ocupados - sum(0 < r["inventario"] <= r["necesario"] for r in recursos) + 1
    cabe = capacidad is None or espacios <= capacidad
    coste_oro = coste_fabricacion(arma["precio"])
    resultado = {"nombre": f"{datos['tipos'][tipo]['nombre']} de {datos['materiales'][material]['nombre']}",
            "categoria": datos["tipos"][tipo].get("categoria", "arma"),
            "material": material, "tier": arma["tier"],
            "rangos": {k: [min(a[k] for a in variantes), max(a[k] for a in variantes)]
                       for k in ("velocidad", "critico", "penetracion", "defensa", "probabilidad_bloqueo", "porcentaje_dano_bloqueado", "peso", "durabilidad") if k in arma},
            "durabilidad": arma["durabilidad"], "peso": arma["peso"],
            "requisitos": arma["requisitos"], "afijo": arma.get("afijo", {}), "recursos": recursos,
            "valor_mercado": arma["precio"], "precio_venta": arma["precio"] // 2,
            "coste_oro": coste_oro, "oro_disponible": personaje.oro,
            "puede_fabricar": suficientes and cabe and personaje.oro >= coste_oro, "espacio_disponible": cabe}
    if "ataque" in arma:
        resultado.update(tipo_arma=tipo, alcance=arma["alcance"],
            ataque={"minimo": [min(a["ataque"][0] for a in variantes), max(a["ataque"][0] for a in variantes)],
                       "maximo": [min(a["ataque"][1] for a in variantes), max(a["ataque"][1] for a in variantes)]},
        )
    return resultado


def fabricar(personaje, tipo, material, componente=None, rng=None, vault=None):
    datos = crafting_data()
    # Se valida la selección antes de consultar o consumir recursos.
    if not isinstance(tipo, str) or not isinstance(material, str) or (componente is not None and not isinstance(componente, str)):
        raise ValueError("Selección de crafteo inválida.")
    if tipo not in datos["tipos"] or material not in datos["materiales"] or (componente is not None and componente not in datos["afijos"]):
        raise ValueError("Selección de crafteo inválida.")
    preview = previsualizar_arma(personaje, tipo, material, componente, vault)
    if any(r["disponible"] < r["necesario"] for r in preview["recursos"]):
        raise ValueError("No hay suficientes materiales o componentes entre el inventario y el vault.")
    if personaje.oro < preview["coste_oro"]:
        raise ValueError("No tienes oro suficiente para fabricar este objeto.")
    if not preview["espacio_disponible"]:
        raise ValueError("No hay espacio para el objeto en el inventario del personaje.")
    from inventario import Inventario
    from item_container import SharedVault
    nuevo = Inventario.deserializar(personaje.inventario.serializar())
    nuevo_vault = SharedVault(vault.serializar()) if vault is not None else None
    for recurso in preview["recursos"]:
        local = min(recurso["inventario"], recurso["necesario"])
        if local:
            nuevo.extraer(recurso["item_id"], local)
        restante = recurso["necesario"] - local
        if restante:
            nuevo_vault.extraer(recurso["item_id"], restante)
    arma = generar_arma(personaje, tipo, material, componente, rng)
    item_factory.registrar_instancia(arma)
    nuevo.recolectar(arma["id"])
    personaje.inventario = nuevo
    if vault is not None:
        vault._cantidades = nuevo_vault._cantidades
        vault._instancias = nuevo_vault._instancias
        vault._custom = nuevo_vault._custom
    personaje.oro -= preview["coste_oro"]
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
