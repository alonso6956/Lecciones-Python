class_name TransitionScreen
extends VBoxContainer

signal continue_requested

@onready var title_label: Label = $TitleLabel
@onready var continue_button: Button = $ContinueButton


func _ready() -> void:
	continue_button.pressed.connect(_on_continue_pressed)


func _on_continue_pressed() -> void:
	continue_button.disabled = true
	continue_requested.emit()


func render_state(state: Dictionary) -> void:
	var room := int(state.get("habitacion", 0))
	title_label.text = "Habitación %s completada" % room
	continue_button.disabled = false


func set_request_pending(pending: bool) -> void:
	continue_button.disabled = pending
