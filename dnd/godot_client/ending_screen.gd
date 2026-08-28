class_name EndingScreen
extends VBoxContainer

signal main_menu_requested
signal exit_requested

@onready var title_label: Label = $TitleLabel
@onready var result_label: Label = $ResultLabel
@onready var main_menu_button: Button = $MainMenuButton
@onready var exit_button: Button = $ExitButton


func _ready() -> void:
	main_menu_button.pressed.connect(_on_main_menu_pressed)
	exit_button.pressed.connect(_on_exit_pressed)


func render_state(state: Dictionary) -> void:
	var result := str(state.get("resultado", ""))
	if result == "victoria":
		title_label.text = "Victoria"
		result_label.text = "Encontraste la salida del calabozo."
	else:
		title_label.text = "Fin de la expedición"
		result_label.text = "La expedición ha terminado."
	set_request_pending(false)


func set_request_pending(pending: bool) -> void:
	main_menu_button.disabled = pending
	exit_button.disabled = pending


func _on_main_menu_pressed() -> void:
	set_request_pending(true)
	main_menu_requested.emit()


func _on_exit_pressed() -> void:
	set_request_pending(true)
	exit_requested.emit()
