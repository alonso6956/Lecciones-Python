class_name CombatantView
extends PanelContainer

@onready var character_image: TextureRect = \
	$VBoxContainer/CharacterImage
@onready var name_label: Label = $VBoxContainer/NameLabel
@onready var status_container: HBoxContainer = \
	$VBoxContainer/StatusContainer


func render_combatant(data: Dictionary) -> void:
	visible = true
	name_label.text = str(data.get("nombre", "Combatiente"))
	var visual_id := str(data.get("visual_id", ""))
	character_image.texture = VisualCatalog.combatant_texture(visual_id)


func clear_combatant() -> void:
	name_label.text = ""
	character_image.texture = null
	visible = false
