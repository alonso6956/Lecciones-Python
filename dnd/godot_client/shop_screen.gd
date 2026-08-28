class_name ShopScreen
extends VBoxContainer

signal purchase_requested(category: String, item_name: String)
signal continue_requested

@onready var title_label: Label = $TitleLabel
@onready var gold_label: Label = $GoldLabel
@onready var items_container: GridContainer = $ItemsScroll/ItemsContainer
@onready var continue_button: Button = $ContinueButton

var _last_state: Dictionary = {}


func _ready() -> void:
	continue_button.pressed.connect(_on_continue_pressed)


func _on_continue_pressed() -> void:
	set_request_pending(true)
	continue_requested.emit()


func _on_item_pressed(category: String, item_name: String) -> void:
	set_request_pending(true)
	purchase_requested.emit(category, item_name)


func render_state(state: Dictionary) -> void:
	_last_state = state
	var player: Dictionary = state.get("jugador", {})
	var gold := int(player.get("oro", 0))
	title_label.text = "Tienda"
	gold_label.text = "Oro: %s" % gold
	continue_button.disabled = false
	_render_items(state.get("tienda", {}), gold)


func set_request_pending(pending: bool) -> void:
	continue_button.disabled = pending
	for card in items_container.get_children():
		for child in card.get_children():
			if child is Button:
				child.disabled = pending
	if not pending and not _last_state.is_empty():
		render_state(_last_state)


func _render_items(catalog: Dictionary, gold: int) -> void:
	_clear_items()
	for category in catalog:
		var products: Dictionary = catalog.get(category, {})
		for item_name in products:
			var item: Dictionary = products[item_name]
			_create_item_button(str(category), str(item_name), item, gold)


func _create_item_button(
	category: String,
	item_name: String,
	item: Dictionary,
	gold: int,
) -> void:
	var price := int(item.get("precio", 0))
	var card := VBoxContainer.new()
	var button := Button.new()
	var item_id := str(item.get("id", ""))
	var item_texture := VisualCatalog.item_texture(item_id)
	if item_texture != null:
		button.custom_minimum_size = Vector2(160, 152)
		button.icon = item_texture
		button.expand_icon = true
		button.add_theme_constant_override("icon_max_width", 128)
	else:
		button.text = item_name
	button.tooltip_text = _item_details(category, item)
	button.disabled = gold < price
	button.pressed.connect(_on_item_pressed.bind(category, item_name))
	card.add_child(button)

	var item_label := Label.new()
	item_label.text = "%s\n%s oro" % [item_name, price]
	item_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	card.add_child(item_label)
	items_container.add_child(card)


func _item_details(category: String, item: Dictionary) -> String:
	if category == "armas":
		var attack = item.get("ataque", [0, 0])
		var hands := "2 manos" if item.get("dos_manos", false) else "1 mano"
		return "Daño: %s-%s · %s · Tier %s" % [
			attack[0], attack[1], hands, item.get("tier", 1)
		]
	if category == "armaduras":
		return "Armadura: %s · Peso: %s" % [
			item.get("defensa", 0), item.get("peso", 0)
		]
	if category == "secundarios":
		return "Bloqueo: %s%% · Daño bloqueado: %s%% · Peso: %s" % [
			round(float(item.get("probabilidad_bloqueo", 0)) * 100),
			round(float(item.get("porcentaje_dano_bloqueado", 0)) * 100),
			item.get("peso", 0),
		]
	if category == "pociones":
		return "Recupera %s HP" % item.get("salud", 0)
	return str(item.get("descripcion", ""))


func _clear_items() -> void:
	for child in items_container.get_children():
		items_container.remove_child(child)
		child.queue_free()
