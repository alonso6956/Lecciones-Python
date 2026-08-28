class_name CombatScreen
extends VBoxContainer

signal action_requested(action: String, skill_id: String, action_name: String)
signal refresh_requested

@onready var phase_label: Label = $PhaseLabel
@onready var room_label: Label = $RoomLabel
@onready var player_view: CombatantView = \
	$Battlefield/CombatantsContainer/PlayerView
@onready var enemy_view: CombatantView = \
	$Battlefield/CombatantsContainer/EnemyView
@onready var player_name: Label = $PlayerPanel/PlayerName
@onready var player_health: ProgressBar = $PlayerPanel/PlayerHealth
@onready var player_health_text: Label = $PlayerPanel/PlayerHealthText
@onready var player_energy: Label = $PlayerPanel/PlayerEnergy
@onready var enemy_panel: VBoxContainer = $EnemyPanel
@onready var enemy_name: Label = $EnemyPanel/EnemyName
@onready var enemy_health: ProgressBar = $EnemyPanel/EnemyHealth
@onready var enemy_health_text: Label = $EnemyPanel/EnemyHealthText
@onready var enemy_intent: Label = $EnemyPanel/EnemyIntent
@onready var combat_log: RichTextLabel = $CombatLog
@onready var actions_container: GridContainer = $ActionsContainer
@onready var refresh_button: Button = $RefreshButton

var _last_state: Dictionary = {}


func _ready() -> void:
	refresh_button.pressed.connect(_on_refresh_pressed)


func _on_refresh_pressed() -> void:
	refresh_requested.emit()


func _on_basic_attack_pressed() -> void:
	action_requested.emit("atacar", "", "ataque")


func _on_defend_pressed() -> void:
	action_requested.emit("defender", "", "defensa")


func _on_skill_pressed(skill_id: String, skill_name: String) -> void:
	action_requested.emit("habilidad", skill_id, skill_name)


func set_request_pending(pending: bool) -> void:
	refresh_button.disabled = pending
	if pending:
		for button in actions_container.get_children():
			button.disabled = true
	elif not _last_state.is_empty():
		_render_actions_from_state(_last_state)


func render_state(state: Dictionary) -> void:
	_last_state = state
	refresh_button.disabled = false
	phase_label.text = "Fase: " + str(state.get("fase", ""))
	room_label.text = "Habitación: " + str(state.get("habitacion", 0))

	var player = state.get("jugador")
	if player == null:
		player_name.text = "No hay una partida activa."
		player_health.value = 0
		player_view.clear_combatant()
		enemy_view.clear_combatant()
		enemy_panel.visible = false
		_clear_actions()
		_render_log(state)
		return

	_render_player(player)
	_render_enemy(state.get("enemigo"))
	_render_actions(player, state)
	_render_log(state)


func _render_player(player: Dictionary) -> void:
	player_view.render_combatant(player)
	player_name.text = str(player.get("nombre", "Personaje"))
	player_health.max_value = float(player.get("salud_maxima", 1))
	player_health.value = float(player.get("hp", 0))
	player_health_text.text = "%s / %s HP" % [
		player.get("hp", 0),
		player.get("salud_maxima", 0),
	]
	player_energy.text = "Energía: %s / %s" % [
		player.get("energia", 0),
		player.get("energia_maxima", 0),
	]


func _render_enemy(enemy) -> void:
	if enemy == null:
		enemy_view.clear_combatant()
		enemy_panel.visible = false
		return

	enemy_view.render_combatant(enemy)
	enemy_panel.visible = true
	enemy_name.text = str(enemy.get("nombre", "Enemigo"))
	var maximum_health := float(enemy.get("hp_maxima", 1))
	enemy_health.max_value = maximum_health
	enemy_health.value = float(enemy.get("hp", 0))
	enemy_health_text.text = "%s / %s HP" % [
		enemy.get("hp", 0),
		maximum_health,
	]
	enemy_intent.text = "Intención: " + str(
		enemy.get("intencion", "Desconocida")
	)


func _render_log(state: Dictionary) -> void:
	var lines: Array = state.get("registro", [])
	combat_log.text = "\n".join(lines)


func _render_actions_from_state(state: Dictionary) -> void:
	var player = state.get("jugador")
	if player == null:
		_clear_actions()
		return
	_render_actions(player, state)


func _render_actions(player: Dictionary, state: Dictionary) -> void:
	_clear_actions()
	if state.get("fase", "") != "combate":
		return
	var enemy = state.get("enemigo")
	if enemy == null:
		return
	if float(player.get("hp", 0)) <= 0 or float(enemy.get("hp", 0)) <= 0:
		return

	_create_action_button("Ataque básico", _on_basic_attack_pressed)
	_create_action_button("Defender", _on_defend_pressed)

	var current_energy := int(player.get("energia", 0))
	for skill in player.get("habilidades", []):
		if not skill.get("desbloqueada", false):
			continue
		if not skill.get("cumple_requisito", false):
			continue
		if not skill.get("cumple_tipo_equipo", false):
			continue
		_create_skill_button(skill, current_energy)


func _create_skill_button(skill: Dictionary, current_energy: int) -> void:
	var skill_id := str(skill.get("id", ""))
	var skill_name := str(skill.get("nombre", "Habilidad"))
	var description := str(skill.get("descripcion", ""))
	var energy_cost := int(skill.get("costo_energia", 0))
	var cooldown := int(skill.get("cooldown", 0))
	var is_active := bool(skill.get("activa", false))
	var unavailable := false
	var button_text := "%s · %s EN" % [skill_name, energy_cost]

	if cooldown > 0:
		button_text += " · CD: %s" % cooldown
		description += "\nDisponible en %s turno(s)." % cooldown
		unavailable = true
	elif is_active:
		button_text += " · ACTIVA"
		description += "\nSu efecto ya está activo."
		unavailable = true
	elif energy_cost > current_energy:
		button_text += " · SIN ENERGÍA"
		description += "\nNo tienes suficiente energía."
		unavailable = true

	_create_action_button(
		button_text,
		_on_skill_pressed.bind(skill_id, skill_name),
		description,
		unavailable,
	)


func _create_action_button(
	button_text: String,
	callback: Callable,
	tooltip := "",
	disabled := false,
) -> void:
	var button := Button.new()
	button.text = button_text
	button.tooltip_text = tooltip
	button.disabled = disabled
	button.pressed.connect(callback)
	actions_container.add_child(button)


func _clear_actions() -> void:
	for child in actions_container.get_children():
		actions_container.remove_child(child)
		child.queue_free()
