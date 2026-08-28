class_name DeathScreen
extends VBoxContainer

signal respawn_requested
signal exit_requested

@onready var title_label: Label = $TitleLabel
@onready var reborn_button: Button = $Reborn
@onready var exit_button: Button = $Salir


func _ready() -> void:
	reborn_button.pressed.connect(_on_reborn_pressed)
	exit_button.pressed.connect(_on_exit_pressed)


func _on_reborn_pressed() -> void:
	set_request_pending(true)
	respawn_requested.emit()


func _on_exit_pressed() -> void:
	set_request_pending(true)
	exit_requested.emit()


func render_state(_state: Dictionary) -> void:
	title_label.text = "Has muerto"
	set_request_pending(false)


func set_request_pending(pending: bool) -> void:
	reborn_button.disabled = pending
	exit_button.disabled = pending
