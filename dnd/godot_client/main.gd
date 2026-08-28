extends Control

const SERVER_URL := "http://127.0.0.1:8000"
const INVENTORY_BLOCKED_PHASES := ["menu", "inicio", "fin", "muerte"]

@onready var http_request: HTTPRequest = $HTTPRequest
@onready var connection_status: Label = $ConnectionStatus
@onready var combat_screen: CombatScreen = \
	$ScreenContainer/CombatScreen
@onready var transition_screen: TransitionScreen = \
	$ScreenContainer/TransitionScreen
@onready var shop_screen: ShopScreen = $ScreenContainer/ShopScreen
@onready var level_up_screen: LevelUpScreen = \
	$ScreenContainer/LevelUpScreen
@onready var death_screen: DeathScreen = $ScreenContainer/DeathScreen
@onready var main_menu_screen: MainMenuScreen = \
	$ScreenContainer/MainMenuScreen
@onready var character_creation_screen: CharacterCreationScreen = \
	$ScreenContainer/CharacterCreationScreen
@onready var inventory_screen: InventoryScreen = \
	$ScreenContainer/InventoryScreen
@onready var inventory_button: Button = $InventoryButton
@onready var save_slots_screen: SaveSlotsScreen = \
	$ScreenContainer/SaveSlotsScreen
@onready var save_button: Button = $SaveButton
@onready var ending_screen: EndingScreen = $ScreenContainer/EndingScreen

var _exit_after_response := false
var _inventory_open := false
var _current_state: Dictionary = {}
var _slots_open := false
var _slots_mode := "load"
var _return_to_inventory := false
var _slot_operation := ""


func _ready() -> void:
	http_request.request_completed.connect(_on_request_completed)
	combat_screen.action_requested.connect(_on_action_requested)
	combat_screen.refresh_requested.connect(request_state)
	transition_screen.continue_requested.connect(_on_continue_requested)
	shop_screen.purchase_requested.connect(_on_purchase_requested)
	shop_screen.continue_requested.connect(_on_shop_continue_requested)
	level_up_screen.stat_requested.connect(_on_stat_requested)
	level_up_screen.skill_requested.connect(_on_skill_requested)
	death_screen.respawn_requested.connect(_on_respawn_requested)
	death_screen.exit_requested.connect(_on_exit_requested)
	main_menu_screen.new_game_requested.connect(_on_new_game_requested)
	main_menu_screen.load_game_requested.connect(_on_load_game_requested)
	main_menu_screen.exit_requested.connect(_on_menu_exit_requested)
	character_creation_screen.start_requested.connect(_on_start_requested)
	inventory_button.pressed.connect(_on_inventory_pressed)
	inventory_screen.close_requested.connect(_on_inventory_closed)
	inventory_screen.equip_requested.connect(_on_equip_requested)
	inventory_screen.unequip_requested.connect(_on_unequip_requested)
	inventory_screen.use_requested.connect(_on_use_item_requested)
	save_button.pressed.connect(_on_save_pressed)
	save_slots_screen.slot_selected.connect(_on_slot_selected)
	save_slots_screen.back_requested.connect(_on_slots_back_requested)
	ending_screen.main_menu_requested.connect(_on_ending_main_menu_requested)
	ending_screen.exit_requested.connect(_on_ending_exit_requested)
	request_state()


func request_state() -> void:
	combat_screen.set_request_pending(true)
	connection_status.text = "Consultando el motor Python..."
	var error := http_request.request(SERVER_URL + "/api/estado")
	if error != OK:
		combat_screen.set_request_pending(false)
		connection_status.text = "No se pudo iniciar la solicitud."


func _on_action_requested(
	action: String,
	skill_id: String,
	action_name: String,
) -> void:
	combat_screen.set_request_pending(true)
	connection_status.text = "Resolviendo %s..." % action_name
	var payload := {"accion": action}
	if not skill_id.is_empty():
		payload["habilidad"] = skill_id

	var error := http_request.request(
		SERVER_URL + "/api/accion",
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		JSON.stringify(payload),
	)
	if error != OK:
		combat_screen.set_request_pending(false)
		connection_status.text = "No se pudo enviar la acción."


func _on_continue_requested() -> void:
	transition_screen.set_request_pending(true)
	connection_status.text = "Avanzando a la siguiente habitación..."
	_request_continue()


func _on_shop_continue_requested() -> void:
	shop_screen.set_request_pending(true)
	connection_status.text = "Saliendo de la tienda..."
	_request_continue()


func _request_continue() -> void:
	var error := http_request.request(
		SERVER_URL + "/api/continuar",
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		"{}",
	)
	if error != OK:
		transition_screen.set_request_pending(false)
		shop_screen.set_request_pending(false)
		connection_status.text = "No se pudo avanzar."


func _on_purchase_requested(category: String, item_name: String) -> void:
	shop_screen.set_request_pending(true)
	connection_status.text = "Comprando %s..." % item_name
	var body := JSON.stringify({
		"categoria": category,
		"nombre": item_name,
	})
	var error := http_request.request(
		SERVER_URL + "/api/comprar",
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		body,
	)
	if error != OK:
		shop_screen.set_request_pending(false)
		connection_status.text = "No se pudo realizar la compra."


func _on_stat_requested(stat_name: String) -> void:
	level_up_screen.set_request_pending(true)
	connection_status.text = "Mejorando %s..." % stat_name
	var error := http_request.request(
		SERVER_URL + "/api/nivel",
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		JSON.stringify({"estadistica": stat_name}),
	)
	if error != OK:
		level_up_screen.set_request_pending(false)
		connection_status.text = "No se pudo mejorar la estadística."


func _on_skill_requested(skill_id: String) -> void:
	level_up_screen.set_request_pending(true)
	connection_status.text = "Mejorando habilidad..."
	var error := http_request.request(
		SERVER_URL + "/api/mejorar-habilidad",
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		JSON.stringify({"habilidad": skill_id}),
	)
	if error != OK:
		level_up_screen.set_request_pending(false)
		connection_status.text = "No se pudo mejorar la habilidad."


func _on_respawn_requested() -> void:
	death_screen.set_request_pending(true)
	connection_status.text = "Regresando al inicio del calabozo..."
	var error := http_request.request(
		SERVER_URL + "/api/respawn",
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		"{}",
	)
	if error != OK:
		death_screen.set_request_pending(false)
		connection_status.text = "No se pudo renacer."


func _on_new_game_requested() -> void:
	main_menu_screen.set_request_pending(true)
	connection_status.text = "Preparando una nueva partida..."
	var error := http_request.request(
		SERVER_URL + "/api/nueva",
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		"{}",
	)
	if error != OK:
		main_menu_screen.set_request_pending(false)
		connection_status.text = "No se pudo crear la partida."


func _on_load_game_requested() -> void:
	_open_slots("load")


func _on_save_pressed() -> void:
	_open_slots("save")


func _open_slots(mode: String) -> void:
	_slots_mode = mode
	_slots_open = true
	_return_to_inventory = _inventory_open
	_render_state(_current_state)


func _on_slots_back_requested() -> void:
	_slots_open = false
	_inventory_open = _return_to_inventory
	main_menu_screen.set_request_pending(false)
	_render_state(_current_state)


func _on_slot_selected(mode: String, slot: int) -> void:
	_slot_operation = mode
	connection_status.text = (
		"Guardando partida..." if mode == "save" else "Cargando partida..."
	)
	var endpoint := "/api/guardar" if mode == "save" else "/api/cargar"
	var error := http_request.request(
		SERVER_URL + endpoint,
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		JSON.stringify({"slot": slot}),
	)
	if error != OK:
		_slot_operation = ""
		save_slots_screen.set_request_pending(false)
		connection_status.text = "No se pudo acceder al guardado."


func _on_start_requested(character_name: String, weapon_name: String) -> void:
	character_creation_screen.set_request_pending(true)
	connection_status.text = "Entrando al calabozo..."
	var body := JSON.stringify({
		"nombre": character_name,
		"arma": weapon_name,
	})
	var error := http_request.request(
		SERVER_URL + "/api/iniciar",
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		body,
	)
	if error != OK:
		character_creation_screen.set_request_pending(false)
		connection_status.text = "No se pudo iniciar la aventura."


func _on_exit_requested() -> void:
	death_screen.set_request_pending(true)
	_request_exit()


func _on_menu_exit_requested() -> void:
	main_menu_screen.set_request_pending(true)
	_request_exit()


func _on_ending_exit_requested() -> void:
	ending_screen.set_request_pending(true)
	_request_exit()


func _on_ending_main_menu_requested() -> void:
	ending_screen.set_request_pending(true)
	connection_status.text = "Volviendo al menú..."
	var error := http_request.request(
		SERVER_URL + "/api/reiniciar",
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		"{}",
	)
	if error != OK:
		ending_screen.set_request_pending(false)
		connection_status.text = "No se pudo volver al menú."


func _request_exit() -> void:
	connection_status.text = "Cerrando..."
	_exit_after_response = true
	var error := http_request.request(
		SERVER_URL + "/api/salir",
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		"{}",
	)
	if error != OK:
		_exit_after_response = false
		death_screen.set_request_pending(false)
		main_menu_screen.set_request_pending(false)
		ending_screen.set_request_pending(false)
		connection_status.text = "No se pudo cerrar el servidor."


func _on_inventory_pressed() -> void:
	if _current_state.get("jugador") == null:
		return
	_inventory_open = true
	_render_state(_current_state)


func _on_inventory_closed() -> void:
	_inventory_open = false
	_render_state(_current_state)


func _on_equip_requested(item_id: String) -> void:
	_send_inventory_request(
		"/api/equipar",
		{"item": item_id},
		"Equipando objeto...",
	)


func _on_unequip_requested(slot: String) -> void:
	_send_inventory_request(
		"/api/desequipar",
		{"slot": slot},
		"Desequipando objeto...",
	)


func _on_use_item_requested(item_id: String) -> void:
	_send_inventory_request(
		"/api/usar-item",
		{"item": item_id},
		"Usando objeto...",
	)


func _send_inventory_request(
	endpoint: String,
	payload: Dictionary,
	status_text: String,
) -> void:
	inventory_screen.set_request_pending(true)
	connection_status.text = status_text
	var error := http_request.request(
		SERVER_URL + endpoint,
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		JSON.stringify(payload),
	)
	if error != OK:
		inventory_screen.set_request_pending(false)
		connection_status.text = "No se pudo modificar el inventario."


func _on_request_completed(
	result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray,
) -> void:
	if _exit_after_response:
		_exit_after_response = false
		if result == HTTPRequest.RESULT_SUCCESS and response_code == 200:
			get_tree().quit()
			return
		death_screen.set_request_pending(false)
		main_menu_screen.set_request_pending(false)
		ending_screen.set_request_pending(false)
		connection_status.text = "No se pudo cerrar el servidor."
		return

	if result != HTTPRequest.RESULT_SUCCESS:
		_slot_operation = ""
		combat_screen.set_request_pending(false)
		transition_screen.set_request_pending(false)
		shop_screen.set_request_pending(false)
		level_up_screen.set_request_pending(false)
		death_screen.set_request_pending(false)
		main_menu_screen.set_request_pending(false)
		character_creation_screen.set_request_pending(false)
		inventory_screen.set_request_pending(false)
		save_slots_screen.set_request_pending(false)
		ending_screen.set_request_pending(false)
		connection_status.text = "Python no está disponible."
		return

	var state = JSON.parse_string(body.get_string_from_utf8())
	if typeof(state) != TYPE_DICTIONARY:
		_slot_operation = ""
		combat_screen.set_request_pending(false)
		transition_screen.set_request_pending(false)
		shop_screen.set_request_pending(false)
		level_up_screen.set_request_pending(false)
		death_screen.set_request_pending(false)
		main_menu_screen.set_request_pending(false)
		character_creation_screen.set_request_pending(false)
		inventory_screen.set_request_pending(false)
		save_slots_screen.set_request_pending(false)
		ending_screen.set_request_pending(false)
		connection_status.text = "Python devolvió datos inválidos."
		return

	if response_code != 200:
		_slot_operation = ""
		connection_status.text = str(
			state.get("error", "La acción falló.")
		)
		var error_state = state.get("estado")
		if typeof(error_state) == TYPE_DICTIONARY:
			_render_state(error_state)
		else:
			combat_screen.set_request_pending(false)
			transition_screen.set_request_pending(false)
			shop_screen.set_request_pending(false)
			level_up_screen.set_request_pending(false)
			death_screen.set_request_pending(false)
			main_menu_screen.set_request_pending(false)
			character_creation_screen.set_request_pending(false)
			inventory_screen.set_request_pending(false)
			save_slots_screen.set_request_pending(false)
			ending_screen.set_request_pending(false)
		return

	if not _slot_operation.is_empty():
		var completed_operation := _slot_operation
		_slot_operation = ""
		_slots_open = false
		if completed_operation == "load":
			_inventory_open = false
		else:
			_inventory_open = _return_to_inventory

	connection_status.text = "Conectado con el motor Python."
	_render_state(state)


func _render_state(state: Dictionary) -> void:
	_current_state = state
	var phase := str(state.get("fase", ""))
	var is_transition := phase == "transicion"
	var is_shop := phase == "tienda"
	var is_level_up := phase == "nivel"
	var is_death := phase == "muerte"
	var is_menu := phase == "menu"
	var is_creation := phase == "inicio"
	var is_ending := phase == "fin"
	if phase in INVENTORY_BLOCKED_PHASES:
		_inventory_open = false
	if phase not in ["menu"] and _slots_mode == "load":
		main_menu_screen.set_request_pending(false)

	if _slots_open:
		_hide_phase_screens()
		inventory_screen.visible = false
		save_slots_screen.visible = true
		inventory_button.visible = false
		save_button.visible = false
		save_slots_screen.show_slots(_slots_mode, state)
		return

	if _inventory_open:
		_hide_phase_screens()
		inventory_screen.visible = true
		save_slots_screen.visible = false
		inventory_button.visible = false
		save_button.visible = true
		inventory_screen.render_state(state)
		return

	combat_screen.visible = (
		not is_transition
		and not is_shop
		and not is_level_up
		and not is_death
		and not is_menu
		and not is_creation
		and not is_ending
	)
	transition_screen.visible = is_transition
	shop_screen.visible = is_shop
	level_up_screen.visible = is_level_up
	death_screen.visible = is_death
	main_menu_screen.visible = is_menu
	character_creation_screen.visible = is_creation
	ending_screen.visible = is_ending
	inventory_screen.visible = false
	save_slots_screen.visible = false
	inventory_button.visible = (
		state.get("jugador") != null
		and phase not in INVENTORY_BLOCKED_PHASES
	)
	save_button.visible = inventory_button.visible

	if is_menu:
		main_menu_screen.render_state(state)
	elif is_creation:
		character_creation_screen.render_state(state)
	elif is_ending:
		ending_screen.render_state(state)
	elif is_transition:
		transition_screen.render_state(state)
	elif is_shop:
		shop_screen.render_state(state)
	elif is_level_up:
		level_up_screen.render_state(state)
	elif is_death:
		death_screen.render_state(state)
	else:
		combat_screen.render_state(state)


func _hide_phase_screens() -> void:
	combat_screen.visible = false
	transition_screen.visible = false
	shop_screen.visible = false
	level_up_screen.visible = false
	death_screen.visible = false
	main_menu_screen.visible = false
	character_creation_screen.visible = false
	save_slots_screen.visible = false
	ending_screen.visible = false
