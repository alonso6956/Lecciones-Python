class_name SaveSlotsScreen
extends VBoxContainer

signal slot_selected(mode: String, slot: int)
signal back_requested

@onready var title_label: Label = $TitleLabel
@onready var slots_container: VBoxContainer = $SlotsContainer
@onready var back_button: Button = $BackButton
@onready var overwrite_dialog: ConfirmationDialog = $OverwriteDialog

var _mode := "load"
var _pending_overwrite_slot := 0


func _ready() -> void:
	back_button.pressed.connect(_on_back_pressed)
	overwrite_dialog.confirmed.connect(_on_overwrite_confirmed)


func show_slots(mode: String, state: Dictionary) -> void:
	_mode = mode
	title_label.text = "Guardar partida" if mode == "save" else "Cargar partida"
	_render_slots(state.get("slots", []), state.get("slot_activo"))
	set_request_pending(false)


func set_request_pending(pending: bool) -> void:
	back_button.disabled = pending
	for button in slots_container.get_children():
		button.disabled = pending or bool(button.get_meta("blocked", false))


func _render_slots(slots: Array, active_slot) -> void:
	_clear_slots()
	for slot_data in slots:
		var slot := int(slot_data.get("slot", 0))
		var occupied := bool(slot_data.get("ocupado", false))
		var button := Button.new()
		button.text = _slot_text(slot_data, slot == active_slot)
		button.set_meta("occupied", occupied)
		button.set_meta("blocked", _mode == "load" and not occupied)
		button.disabled = bool(button.get_meta("blocked"))
		button.pressed.connect(_on_slot_pressed.bind(slot, occupied))
		slots_container.add_child(button)


func _slot_text(slot_data: Dictionary, is_active: bool) -> String:
	var slot := int(slot_data.get("slot", 0))
	var prefix := "Slot %s" % slot
	if is_active:
		prefix += " · ACTIVO"
	if not slot_data.get("ocupado", false):
		return "%s\nVacío" % prefix

	var summary: Dictionary = slot_data.get("resumen", {})
	return "%s\n%s · Nivel %s · Habitación %s\n%s" % [
		prefix,
		summary.get("personaje", "Aventurero"),
		summary.get("nivel", 1),
		summary.get("habitacion", 1),
		_format_date(str(summary.get("fecha", ""))),
	]


func _format_date(value: String) -> String:
	if value.is_empty():
		return "Fecha desconocida"
	return value.replace("T", " ").replace("+00:00", " UTC")


func _on_slot_pressed(slot: int, occupied: bool) -> void:
	if _mode == "save" and occupied:
		_pending_overwrite_slot = slot
		overwrite_dialog.popup_centered()
		return
	_emit_slot(slot)


func _on_overwrite_confirmed() -> void:
	if _pending_overwrite_slot <= 0:
		return
	var slot := _pending_overwrite_slot
	_pending_overwrite_slot = 0
	_emit_slot(slot)


func _emit_slot(slot: int) -> void:
	set_request_pending(true)
	slot_selected.emit(_mode, slot)


func _on_back_pressed() -> void:
	back_requested.emit()


func _clear_slots() -> void:
	for child in slots_container.get_children():
		slots_container.remove_child(child)
		child.queue_free()
