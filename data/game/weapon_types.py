weapon_emoji_map = {
    "Bow": "<:UI_GachaTypeIcon_Bow:1030825784702672906>",
    "Catalyst": "<:UI_GachaTypeIcon_Catalyst:1030825786204237885>",
    "Claymore": "<:UI_GachaTypeIcon_Claymore:1030825789492564008>",
    "Polearm": "<:UI_GachaTypeIcon_Pole:1030825788024561715>",
    "Sword": "<:UI_GachaTypeIcon_Sword:1030825790998319154>",
}

weapon_text_map = {
    "Bow": 471,
    "Catalyst": 469,
    "Claymore": 470,
    "Polearm": 472,
    "Sword": 468,
}

def get_weapon_types() -> list[str]:
    return list(weapon_emoji_map.keys())

def get_weapon_type_emoji(weapon_type: str) -> str:
    return weapon_emoji_map.get(weapon_type, "")

def get_weapon_type_text(weapon_type: str) -> int:
    return weapon_text_map.get(weapon_type, 700)