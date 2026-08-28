class_name LevelUpScreen
extends VBoxContainer

signal stat_requested(stat_name: String)
signal skill_requested(skill_id: String)

const STATS := {
	"fuerza": "Fuerza",
	"destreza": "Destreza",
	"constitucion": "Constitución",
}

@onready var title_label: Label = $TitleLabel
@onready var stats_container: HBoxContainer = $StatsContainer
@onready var skills_container: GridContainer = $SkillsContainer


func render_state(state: Dictionary) -> void:
	var player: Dictionary = state.get("jugador", {})
	title_label.text = "Nivel %s · Elige tus mejoras" % player.get("nivel", 1)
	_render_stats(player)
	_render_skills(player)


func set_request_pending(pending: bool) -> void:
	for button in stats_container.get_children():
		button.disabled = pending
	for button in skills_container.get_children():
		button.disabled = pending


func _render_stats(player: Dictionary) -> void:
	_clear_container(stats_container)
	var base_stats: Dictionary = player.get("stats_base", {})
	var available_points := int(player.get("puntos_estadistica", 0))
	for stat_name in STATS:
		var current_value := int(base_stats.get(stat_name, 0))
		var button := Button.new()
		button.text = "%s\n%s → %s" % [
			STATS[stat_name], current_value, current_value + 1
		]
		button.disabled = available_points <= 0
		button.pressed.connect(_on_stat_pressed.bind(stat_name))
		stats_container.add_child(button)


func _render_skills(player: Dictionary) -> void:
	_clear_container(skills_container)
	var available_points := int(player.get("puntos_habilidad", 0))
	for skill in player.get("habilidades", []):
		if not skill.get("cumple_tipo_equipo", false):
			continue
		var skill_id := str(skill.get("id", ""))
		var skill_name := str(skill.get("nombre", "Habilidad"))
		var level := int(skill.get("nivel", 0))
		var maximum_level := int(skill.get("nivel_maximo", 1))
		var button := Button.new()
		button.text = "%s\nNivel %s → %s" % [
			skill_name, level, min(level + 1, maximum_level)
		]
		button.tooltip_text = str(skill.get("descripcion", ""))
		button.disabled = available_points <= 0 or level >= maximum_level
		button.pressed.connect(_on_skill_pressed.bind(skill_id))
		skills_container.add_child(button)


func _on_stat_pressed(stat_name: String) -> void:
	set_request_pending(true)
	stat_requested.emit(stat_name)


func _on_skill_pressed(skill_id: String) -> void:
	set_request_pending(true)
	skill_requested.emit(skill_id)


func _clear_container(container: Container) -> void:
	for child in container.get_children():
		container.remove_child(child)
		child.queue_free()
