class_name CharacterCreationScreen
extends VBoxContainer

signal start_requested(character_name: String)
signal back_requested

@onready var name_input: LineEdit = $NameInput
@onready var start_button: Button = $StartButton
@onready var back_button: Button = $BackButton

func _ready() -> void:
	name_input.text_changed.connect(func(_value): set_request_pending(false))
	start_button.pressed.connect(_on_start_pressed)
	back_button.pressed.connect(_on_back_pressed)

func render_state(_state: Dictionary) -> void:
	set_request_pending(false)

func set_request_pending(pending: bool) -> void:
	name_input.editable = not pending
	start_button.disabled = pending or name_input.text.strip_edges().is_empty()
	back_button.disabled = pending

func _on_back_pressed() -> void:
	set_request_pending(true)
	back_requested.emit()

func _on_start_pressed() -> void:
	if name_input.text.strip_edges().is_empty():
		return
	set_request_pending(true)
	start_requested.emit(name_input.text.strip_edges())
