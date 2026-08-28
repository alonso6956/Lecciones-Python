class_name VisualCatalog
extends RefCounted

const COMBATANTS := {
	"player_default": preload("res://assets/test_player.png"),
	"enemy_default": preload("res://assets/test_enemy.png"),
}

const ITEMS := {
	"espada_hierro": preload("res://tiles/long_sword_01.png"),
	"dagas_hierro": preload("res://tiles/dagger_01.png"),
	"maza_hierro": preload("res://tiles/mace_01.png"),
	"morning_star": preload("res://tiles/labrys_01.png"),
	"estoque_acero": preload("res://tiles/odachi_01.png"),
}


static func combatant_texture(visual_id: String) -> Texture2D:
	return COMBATANTS.get(visual_id)


static func item_texture(item_id: String) -> Texture2D:
	return ITEMS.get(item_id)
