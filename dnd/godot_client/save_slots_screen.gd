class_name SaveSlotsScreen
extends VBoxContainer

signal slot_selected(mode: String, slot: int)
signal back_requested
signal discard_requested(character_id: String)

@onready var title_label: Label = $TitleLabel
@onready var slots_container: VBoxContainer = $SlotsContainer
@onready var back_button: Button = $BackButton

func _ready() -> void:
	back_button.pressed.connect(func(): back_requested.emit())

func show_slots(_mode: String, state: Dictionary) -> void:
	title_label.text = "Elegir personaje · Nueva expedición desde la habitación 1"
	for child in slots_container.get_children():
		slots_container.remove_child(child)
		child.queue_free()
	for slot_data in state.get("slots", []):
		var summary: Dictionary = slot_data.get("resumen", {})
		var button := Button.new()
		button.text = "%s · Nivel %s" % [summary.get("personaje", "Aventurero"), summary.get("nivel", 1)]
		button.pressed.connect(_on_selected.bind(int(slot_data["slot"])))
		slots_container.add_child(button)
		var discard_button := Button.new()
		discard_button.text = "Descartar a " + str(summary.get("personaje", "Aventurero"))
		discard_button.pressed.connect(_confirm_discard.bind(str(slot_data["id"]), str(summary.get("personaje", "Aventurero"))))
		slots_container.add_child(discard_button)
	if state.get("slots", []).is_empty():
		title_label.text = "No quedan personajes. Vuelve al menú para crear uno."
	set_request_pending(false)

func _confirm_discard(character_id: String, character_name: String) -> void:
	var dialog := ConfirmationDialog.new()
	dialog.dialog_text = "¿Descartar a %s? Se eliminará del roster con toda su experiencia, oro y equipo. Esta acción no se puede deshacer desde el juego." % character_name
	dialog.ok_button_text = "Descartar personaje"
	add_child(dialog)
	dialog.confirmed.connect(func():
		set_request_pending(true)
		discard_requested.emit(character_id)
		dialog.queue_free())
	dialog.canceled.connect(dialog.queue_free)
	dialog.popup_centered(Vector2i(620, 180))

func _on_selected(slot: int) -> void:
	set_request_pending(true)
	slot_selected.emit("load", slot)

func set_request_pending(pending: bool) -> void:
	back_button.disabled = pending
	for button in slots_container.get_children():
		button.disabled = pending
