class_name MainMenuScreen
extends VBoxContainer

signal new_game_requested
signal load_game_requested
signal exit_requested

@onready var new_game_button: Button = $NewGameButton
@onready var load_game_button: Button = $LoadGameButton
@onready var exit_button: Button = $ExitButton


func _ready() -> void:
	new_game_button.pressed.connect(_on_new_game_pressed)
	load_game_button.pressed.connect(_on_load_game_pressed)
	exit_button.pressed.connect(_on_exit_pressed)


func _on_new_game_pressed() -> void:
	set_request_pending(true)
	new_game_requested.emit()


func _on_load_game_pressed() -> void:
	set_request_pending(true)
	load_game_requested.emit()


func _on_exit_pressed() -> void:
	set_request_pending(true)
	exit_requested.emit()


func render_state(_state: Dictionary) -> void:
	set_request_pending(false)


func set_request_pending(pending: bool) -> void:
	new_game_button.disabled = pending
	load_game_button.disabled = pending
	exit_button.disabled = pending
