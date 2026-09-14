"""Presentación del estado público consumido por las interfaces."""

from combat_stats import estadisticas_combate
from habilidades import habilidad_factory
from items import objetos
from progression import CLASES, NIVEL_DESBLOQUEO_CHISPA, habilidades_de_clase


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
                    f"Movimiento {penalizaciones['movimiento']:+d}."
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
    datos = {
        "fase": motor.fase,
        "resultado": motor.resultado,
        "habitacion": motor.numero_habitacion,
        "habitaciones_totales": motor.HABITACIONES_TOTALES,
        "registro": motor.registro,
        "eventos": motor.eventos,
        "clases": CLASES,
        "jugador": None,
        "enemigo": None,
        "tienda": None,
    }
    if motor.jugador:
        jugador = motor.jugador
        datos["jugador"] = {
            **estadisticas_combate(jugador),
            "id": jugador.id,
            "nombre": jugador.nombre,
            "clase": jugador.clase,
            "clase_nombre": CLASES.get(jugador.clase, {}).get("nombre", "Sin clase"),
            "chispa": jugador.chispa,
            "chispa_nivel_desbloqueo": NIVEL_DESBLOQUEO_CHISPA,
            "clase_pendiente": jugador.nivel >= 10 and jugador.clase is None,
            "visual_id": "player_default",
            "inventario": jugador.inventario.estado(jugador),
            "equipamiento": jugador.inventario.estado_equipamiento(),
            "hp": max(0, jugador.hp),
            "energia": motor.energia,
            "energia_maxima": motor.energia_maxima,
            "nivel": jugador.nivel,
            "nivel_maximo": motor.sistema_niveles.nivel_maximo,
            "exp": jugador.exp,
            "exp_siguiente_nivel": (
                motor.sistema_niveles.experiencia_siguiente_nivel(jugador)
            ),
            "oro": jugador.oro,
            "stats_base": {
                "fuerza": jugador.fuerza,
                "destreza": jugador.destreza,
                "constitucion": jugador.constitucion,
            },
            "bonus_equipo": jugador.inventario.bonificaciones_atributos(),
            "puntos_estadistica": jugador.puntos_estadistica,
            "puntos_habilidad": jugador.puntos_habilidad,
            "evasion": motor._evasion_total_jugador(),
            "defendiendo": motor.is_defending,
            "mitigar_dano_activo": jugador.mitigar_dano_activo,
            "mitigar_dano_turnos": jugador.mitigar_dano_turnos,
            "estados_activos": motor._estados_activos_jugador(),
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
                    "clase_requerida": jugador.clase,
                    "desbloqueada": jugador.nivel_habilidad(habilidad.id) > 0,
                    "cumple_requisito": jugador.cumple_requisitos_habilidad(
                        habilidad.id
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
                for habilidad in (habilidad_factory.crear(h) for h in habilidades_de_clase(jugador.clase))
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
            **estadisticas_combate(enemigo),
            "nombre": enemigo.nombre,
            "visual_id": "enemy_default",
            "raza": enemigo.raza,
            "arquetipo": enemigo.arquetipo,
            "hp": max(0, enemigo.hp),
            "hp_maxima": enemigo.salud_maxima,
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
