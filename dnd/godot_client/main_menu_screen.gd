class_name MainMenuScreen
extends VBoxContainer

signal new_game_requested
signal load_game_requested
signal exit_requested

@onready var new_game_button: Button = $NewGameButton
@onready var load_game_button: Button = $LoadGameButton
@onready var exit_button: Button = $ExitButton
@onready var tactical_button: Button = $TacticalButton
@onready var message_label: Label = $MessageLabel
var _can_load := false
var _can_tactical := false


func _ready() -> void:
	new_game_button.pressed.connect(_on_new_game_pressed)
	load_game_button.pressed.connect(_on_load_game_pressed)
	exit_button.pressed.connect(_on_exit_pressed)
	tactical_button.pressed.connect(func(): OS.shell_open("http://127.0.0.1:8000/tactical.html"))
	$WorkshopButton.pressed.connect(func(): OS.shell_open("http://127.0.0.1:8000/workshop.html"))
	$ShopButton.pressed.connect(func(): OS.shell_open("http://127.0.0.1:8000/shop.html"))


func _on_new_game_pressed() -> void:
	set_request_pending(true)
	new_game_requested.emit()


func _on_load_game_pressed() -> void:
	set_request_pending(true)
	load_game_requested.emit()


func _on_exit_pressed() -> void:
	set_request_pending(true)
	exit_requested.emit()


func render_state(state: Dictionary) -> void:
	_can_load = state.get("guardado_disponible", false)
	_can_tactical = state.get("tactico_disponible", false)
	message_label.text = str(state.get("mensaje_bloqueo_tactico", ""))
	for event in state.get("registro", []):
		message_label.text += "\n" + str(event)
	set_request_pending(false)


func set_request_pending(pending: bool) -> void:
	new_game_button.disabled = pending
	load_game_button.disabled = pending or not _can_load
	tactical_button.disabled = pending or not _can_tactical
	exit_button.disabled = pending
