class_name CharacterCreationScreen
extends VBoxContainer

signal start_requested(character_name: String, weapon_name: String)

@onready var name_input: LineEdit = $NameInput
@onready var weapons_container: GridContainer = $WeaponsContainer
@onready var start_button: Button = $StartButton

var _selected_weapon := ""


func _ready() -> void:
	name_input.text_changed.connect(_on_name_changed)
	start_button.pressed.connect(_on_start_pressed)


func render_state(state: Dictionary) -> void:
	_render_weapons(state.get("armas_iniciales", []))
	set_request_pending(false)
	_update_start_button()


func set_request_pending(pending: bool) -> void:
	name_input.editable = not pending
	for button in weapons_container.get_children():
		button.disabled = pending
	start_button.disabled = pending or not _can_start()


func _render_weapons(weapons: Array) -> void:
	_clear_weapons()
	var group := ButtonGroup.new()
	group.allow_unpress = false

	for weapon in weapons:
		var weapon_name := str(weapon.get("nombre", "Arma"))
		var weapon_id := str(weapon.get("id", ""))
		var attack = weapon.get("ataque", [0, 0])
		var button := Button.new()
		button.toggle_mode = true
		button.button_group = group
		button.text = "%s\nDaño %s-%s" % [
			weapon_name, attack[0], attack[1]
		]
		var texture := VisualCatalog.item_texture(weapon_id)
		if texture != null:
			button.icon = texture
			button.expand_icon = true
			button.add_theme_constant_override("icon_max_width", 96)
		button.tooltip_text = _weapon_details(weapon)
		button.button_pressed = weapon_name == _selected_weapon
		button.pressed.connect(_on_weapon_pressed.bind(weapon_name))
		weapons_container.add_child(button)


func _weapon_details(weapon: Dictionary) -> String:
	var hands := "2 manos" if weapon.get("dos_manos", false) else "1 mano"
	var passive = weapon.get("pasiva")
	var details := "%s · Tier %s" % [hands, weapon.get("tier", 1)]
	if passive != null:
		details += "\nPasiva: %s" % passive.get("nombre", "")
	return details


func _on_name_changed(_new_text: String) -> void:
	_update_start_button()


func _on_weapon_pressed(weapon_name: String) -> void:
	_selected_weapon = weapon_name
	_update_start_button()


func _on_start_pressed() -> void:
	if not _can_start():
		return
	set_request_pending(true)
	start_requested.emit(name_input.text.strip_edges(), _selected_weapon)


func _can_start() -> bool:
	return not name_input.text.strip_edges().is_empty() and not _selected_weapon.is_empty()


func _update_start_button() -> void:
	start_button.disabled = not _can_start()


func _clear_weapons() -> void:
	for child in weapons_container.get_children():
		weapons_container.remove_child(child)
		child.queue_free()
