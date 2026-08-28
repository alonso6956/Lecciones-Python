"""Presentación del estado público consumido por las interfaces."""

from combat_formulas import calcular_mitigacion_armadura
from habilidades import habilidad_factory
from items import objetos


def estados_activos_jugador(motor):
    """Construye los buffs y debuffs visibles del jugador."""
    if not motor.jugador:
        return []
    estados = []
    if motor.is_defending:
        estados.append(
            {
                "id": "defender",
                "nombre": "Defendiendo",
                "tipo": "buff",
                "descripcion": "Armadura duplicada.",
                "duracion": "Hasta tu próxima acción",
            }
        )
    for habilidad_id in ("paso_veloz", "mitigar_dano"):
        turnos = motor.efectos_habilidades.get(habilidad_id, 0)
        if turnos <= 0:
            continue
        habilidad = habilidad_factory.crear(habilidad_id)
        nivel = motor.jugador.nivel_habilidad(habilidad_id)
        efecto = habilidad.calcular_efecto(
            nivel,
            motor.jugador.estadistica_total(habilidad.atributo_escalado),
            motor.jugador.inventario.secundario_equipado,
        )
        if habilidad_id == "paso_veloz":
            descripcion = f"Evasión elevada al {round(efecto * 100)}%."
            duracion = "Hasta finalizar el turno enemigo"
        else:
            descripcion = f"Daño recibido reducido un {round(efecto * 100)}%."
            duracion = f"{turnos} turno(s)"
        estados.append(
            {
                "id": habilidad_id,
                "nombre": habilidad.nombre,
                "tipo": "buff",
                "descripcion": descripcion,
                "duracion": duracion,
            }
        )
    if motor.aturdimiento_jugador > 0:
        estados.append(
            {
                "id": "aturdimiento",
                "nombre": "Aturdimiento",
                "tipo": "debuff",
                "descripcion": "Perderás tu próxima acción.",
                "duracion": f"{motor.aturdimiento_jugador} acción(es)",
            }
        )
    penalizaciones = motor.jugador.penalizaciones_peso
    if penalizaciones["evasion"] or penalizaciones["velocidad"]:
        estados.append(
            {
                "id": "sobrecarga",
                "nombre": "Carga pesada",
                "tipo": "debuff",
                "descripcion": (
                    f"Evasión -{round(penalizaciones['evasion'] * 100)}%; "
                    f"Velocidad -{penalizaciones['velocidad']}."
                ),
                "duracion": "Mientras mantengas este peso",
            }
        )
    return estados


def estados_activos_enemigo(motor):
    """Construye los buffs y debuffs visibles del enemigo actual."""
    enemigo = motor.enemigo_actual
    if not enemigo:
        return []
    estados = []
    for habilidad_id, turnos in enemigo.efectos_habilidad.items():
        if turnos <= 0:
            continue
        habilidad = habilidad_factory.crear(habilidad_id)
        estados.append(
            {
                "id": habilidad_id,
                "nombre": habilidad.nombre,
                "tipo": "buff",
                "descripcion": habilidad.descripcion,
                "duracion": f"{turnos} turno(s)",
            }
        )
    if enemigo.sangrado_turnos > 0:
        estados.append(
            {
                "id": "sangrado",
                "nombre": "Sangrado",
                "tipo": "debuff",
                "descripcion": (
                    f"Recibirá {enemigo.sangrado_dano} de daño sin mitigación."
                ),
                "duracion": f"{enemigo.sangrado_turnos} turno(s)",
            }
        )
    return estados


def construir_estado(motor):
    """Devuelve el contrato público compartido por las interfaces."""
    armas_iniciales = [
        {"nombre": nombre, **datos}
        for nombre, datos in objetos["armas"].items()
        if datos.get("inicial", False)
    ]
    datos = {
        "fase": motor.fase,
        "resultado": motor.resultado,
        "habitacion": motor.numero_habitacion,
        "habitaciones_totales": motor.HABITACIONES_TOTALES,
        "registro": motor.registro,
        "eventos": motor.eventos,
        "armas_iniciales": armas_iniciales,
        "jugador": None,
        "enemigo": None,
        "tienda": objetos if motor.fase == "tienda" else None,
    }
    if motor.jugador:
        jugador = motor.jugador
        dano_base = jugador.calcular_dano_base()
        ataque_arma = objetos["armas"][jugador.arma]["ataque"]
        datos["jugador"] = {
            "nombre": jugador.nombre,
            "visual_id": "player_default",
            "arma": jugador.arma,
            "inventario": jugador.inventario.estado(jugador),
            "equipamiento": jugador.inventario.estado_equipamiento(),
            "hp": max(0, jugador.hp),
            "salud_maxima": jugador.salud_maxima,
            "energia": motor.energia,
            "energia_maxima": motor.ENERGIA_MAXIMA,
            "nivel": jugador.nivel,
            "nivel_maximo": motor.sistema_niveles.nivel_maximo,
            "exp": jugador.exp,
            "exp_siguiente_nivel": (
                motor.sistema_niveles.experiencia_siguiente_nivel(jugador)
            ),
            "oro": jugador.oro,
            "fuerza": jugador.fuerza_total,
            "destreza": jugador.destreza_total,
            "constitucion": jugador.constitucion_total,
            "stats_base": {
                "fuerza": jugador.fuerza,
                "destreza": jugador.destreza,
                "constitucion": jugador.constitucion,
            },
            "bonus_equipo": jugador.inventario.bonificaciones_atributos(),
            "puntos_estadistica": jugador.puntos_estadistica,
            "puntos_habilidad": jugador.puntos_habilidad,
            "dano_base": dano_base,
            "ataque_minimo": dano_base + ataque_arma[0],
            "ataque_maximo": dano_base + ataque_arma[1],
            "armadura": motor._defensa_total_jugador(),
            "mitigacion_armadura": calcular_mitigacion_armadura(
                motor._defensa_total_jugador()
            ),
            "armadura_equipo": jugador.inventario.armadura_equipo(),
            "mitigacion_armadura_equipo": calcular_mitigacion_armadura(
                jugador.inventario.armadura_equipo()
            ),
            "velocidad": jugador.velocidad,
            "evasion": motor._evasion_total_jugador(),
            "peso_equipado": jugador.peso_equipado,
            "capacidad_peso": jugador.capacidad_peso,
            "penalizacion_evasion_peso": jugador.penalizaciones_peso["evasion"],
            "penalizacion_velocidad_peso": jugador.penalizaciones_peso["velocidad"],
            "defendiendo": motor.is_defending,
            "mitigar_dano_activo": jugador.mitigar_dano_activo,
            "mitigar_dano_turnos": jugador.mitigar_dano_turnos,
            "estados_activos": motor._estados_activos_jugador(),
            "ataque_arma": ataque_arma,
            "habilidades": [
                {
                    "id": habilidad.id,
                    "nombre": habilidad.nombre,
                    "descripcion": habilidad.descripcion_interfaz(
                        max(1, jugador.nivel_habilidad(habilidad.id)),
                        jugador.estadistica_total(habilidad.atributo_escalado),
                        jugador.inventario.secundario_equipado,
                    ),
                    "nivel": jugador.nivel_habilidad(habilidad.id),
                    "nivel_maximo": habilidad.nivel_maximo,
                    "atributo": habilidad.atributo_escalado,
                    "arma_requerida": habilidad.tipo_arma_requerida,
                    "desbloqueada": jugador.nivel_habilidad(habilidad.id) > 0,
                    "cumple_requisito": jugador.cumple_requisitos_habilidad(
                        habilidad.id
                    ),
                    "cumple_tipo_equipo": jugador.inventario.cumple_tipo_equipo(
                        habilidad.tipo_arma_requerida
                    ),
                    "mano_secundaria_libre": (
                        jugador.inventario.secundario_equipado is None
                    ),
                    "costo_energia": habilidad.costo_energia,
                    "cooldown_turnos": habilidad.cooldown_turnos,
                    "cooldown": motor.cooldowns_habilidades.get(habilidad.id, 0),
                    "bonus_dano": habilidad.bonus_dano_por_nivel
                    * jugador.nivel_habilidad(habilidad.id),
                    "efecto": habilidad.calcular_efecto(
                        max(1, jugador.nivel_habilidad(habilidad.id)),
                        jugador.estadistica_total(habilidad.atributo_escalado),
                        jugador.inventario.secundario_equipado,
                    ),
                    "tipo_efecto": habilidad.tipo_efecto,
                    "numero_golpes": habilidad.numero_golpes,
                    "dano_total_por_golpe": habilidad.multiplicador_base,
                    "requiere_mano_secundaria_libre": (
                        habilidad.requiere_mano_secundaria_libre
                    ),
                    "causa_dano": habilidad.causa_dano,
                    "duracion": habilidad.duracion_turnos,
                    "turnos_activos": motor.efectos_habilidades.get(
                        habilidad.id,
                        0,
                    ),
                    "activa": (
                        jugador.mitigar_dano_activo
                        if habilidad.id == "mitigar_dano"
                        else motor.efectos_habilidades.get(habilidad.id, 0) > 0
                    ),
                }
                for habilidad in habilidad_factory.todas()
            ],
        }
    if motor.enemigo_actual and motor.fase in {
        "combate",
        "nivel",
        "transicion",
        "muerte",
    }:
        enemigo = motor.enemigo_actual
        datos["enemigo"] = {
            "nombre": enemigo.nombre,
            "visual_id": "enemy_default",
            "raza": enemigo.raza,
            "arquetipo": enemigo.arquetipo,
            "hp": max(0, enemigo.hp),
            "hp_maxima": enemigo.salud_maxima,
            "fuerza": enemigo.fuerza,
            "destreza": enemigo.destreza,
            "constitucion": enemigo.constitucion,
            "velocidad": enemigo.velocidad,
            "evasion": enemigo.evasion,
            "arma": enemigo.arma,
            "secundario": enemigo.secundario,
            "estados_activos": motor._estados_activos_enemigo(),
            "habilidades": [
                {
                    "id": habilidad_id,
                    "nombre": habilidad_factory.crear(habilidad_id).nombre,
                    "nivel": nivel,
                    "cooldown": enemigo.cooldowns_habilidad.get(habilidad_id, 0),
                    "turnos_activos": enemigo.efectos_habilidad.get(
                        habilidad_id,
                        0,
                    ),
                    "activa": enemigo.habilidad_activa(habilidad_id),
                }
                for habilidad_id, nivel in enemigo.habilidades.items()
            ],
            "intencion": motor.intencion if motor.fase == "combate" else None,
        }
    return datos
