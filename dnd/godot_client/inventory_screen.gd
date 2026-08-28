class_name InventoryScreen
extends VBoxContainer

signal equip_requested(item_id: String)
signal unequip_requested(slot: String)
signal use_requested(item_id: String)
signal close_requested

const SLOT_NAMES := {
	"mano_principal": "Mano principal",
	"mano_secundaria": "Mano secundaria",
	"casco": "Casco",
	"pecho": "Pecho",
	"brazos": "Brazos",
	"piernas": "Piernas",
}

@onready var equipment_slots: GridContainer = \
	$InventoryContent/EquipmentPanel/EquipmentSlots
@onready var items_grid: GridContainer = \
	$InventoryContent/ItemsPanel/ItemsScroll/ItemsGrid
@onready var close_button: Button = $CloseButton

var _last_state: Dictionary = {}


func _ready() -> void:
	close_button.pressed.connect(_on_close_pressed)


func render_state(state: Dictionary) -> void:
	_last_state = state
	var player: Dictionary = state.get("jugador", {})
	var in_combat: bool = str(state.get("fase", "")) == "combate"
	_render_equipment(player.get("equipamiento", {}), in_combat)
	_render_items(player.get("inventario", []), in_combat)
	close_button.disabled = false


func set_request_pending(pending: bool) -> void:
	close_button.disabled = pending
	_set_container_buttons_disabled(equipment_slots, pending)
	_set_container_buttons_disabled(items_grid, pending)
	if not pending and not _last_state.is_empty():
		render_state(_last_state)


func _render_equipment(equipment: Dictionary, in_combat: bool) -> void:
	_clear_container(equipment_slots)
	for slot in SLOT_NAMES:
		var item = equipment.get(slot)
		var slot_label := Label.new()
		slot_label.text = SLOT_NAMES[slot]
		equipment_slots.add_child(slot_label)

		var button := Button.new()
		if item == null:
			button.text = "Vacío"
			button.disabled = true
		else:
			button.text = str(item.get("nombre", "Objeto"))
			button.icon = VisualCatalog.item_texture(str(item.get("id", "")))
			button.tooltip_text = _item_details(item)
			button.disabled = in_combat
			button.pressed.connect(_on_unequip_pressed.bind(str(slot)))
		equipment_slots.add_child(button)


func _render_items(items: Array, in_combat: bool) -> void:
	_clear_container(items_grid)
	if items.is_empty():
		var empty_label := Label.new()
		empty_label.text = "El inventario está vacío."
		items_grid.add_child(empty_label)
		return

	for item in items:
		_create_item_card(item, in_combat)


func _create_item_card(item: Dictionary, in_combat: bool) -> void:
	var card := VBoxContainer.new()
	var item_id := str(item.get("id", ""))
	var item_name := str(item.get("nombre", "Objeto"))
	var quantity := int(item.get("cantidad", 1))
	var image_button := Button.new()
	image_button.custom_minimum_size = Vector2(128, 112)
	image_button.icon = VisualCatalog.item_texture(item_id)
	image_button.expand_icon = image_button.icon != null
	image_button.add_theme_constant_override("icon_max_width", 96)
	image_button.tooltip_text = _item_details(item)
	card.add_child(image_button)

	var item_label := Label.new()
	item_label.text = "%s ×%s" % [item_name, quantity]
	item_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	card.add_child(item_label)

	var action_button := Button.new()
	var item_class := str(item.get("clase", ""))
	if item_class == "consumible":
		action_button.text = "Usar"
		action_button.pressed.connect(_on_use_pressed.bind(item_id))
	elif item.get("equipado", false):
		action_button.text = "Equipado"
		action_button.disabled = true
	else:
		action_button.text = "Equipar"
		action_button.disabled = in_combat or not item.get("puede_equipar", false)
		action_button.pressed.connect(_on_equip_pressed.bind(item_id))
	card.add_child(action_button)
	items_grid.add_child(card)


func _item_details(item: Dictionary) -> String:
	var item_class := str(item.get("clase", ""))
	if item_class == "arma":
		var attack = item.get("ataque", [0, 0])
		var hands := "2 manos" if item.get("dos_manos", false) else "1 mano"
		return "Daño: %s-%s · %s · Tier %s" % [
			attack[0], attack[1], hands, item.get("tier", 1)
		]
	if item_class == "armadura":
		return "Armadura: %s · Peso: %s" % [
			item.get("defensa", 0), item.get("peso", 0)
		]
	if item_class == "secundario":
		return "Bloqueo: %s%% · Daño bloqueado: %s%% · Peso: %s" % [
			round(float(item.get("probabilidad_bloqueo", 0)) * 100),
			round(float(item.get("porcentaje_dano_bloqueado", 0)) * 100),
			item.get("peso", 0),
		]
	if item_class == "consumible":
		return "Recupera %s HP" % item.get("valor", 0)
	return str(item.get("descripcion", ""))


func _on_equip_pressed(item_id: String) -> void:
	set_request_pending(true)
	equip_requested.emit(item_id)


func _on_unequip_pressed(slot: String) -> void:
	set_request_pending(true)
	unequip_requested.emit(slot)


func _on_use_pressed(item_id: String) -> void:
	set_request_pending(true)
	use_requested.emit(item_id)


func _on_close_pressed() -> void:
	close_requested.emit()


func _set_container_buttons_disabled(container: Container, disabled: bool) -> void:
	for child in container.get_children():
		if child is Button:
			child.disabled = disabled
		elif child is Container:
			_set_container_buttons_disabled(child, disabled)


func _clear_container(container: Container) -> void:
	for child in container.get_children():
		container.remove_child(child)
		child.queue_free()
