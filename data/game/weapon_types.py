weapon_emoji_map = {
    "WEAPON_BOW": "<:UI_GachaTypeIcon_Bow:1030825784702672906>",
    "WEAPON_CATALYST": "<:UI_GachaTypeIcon_Catalyst:1030825786204237885>",
    "WEAPON_CLAYMORE": "<:UI_GachaTypeIcon_Claymore:1030825789492564008>",
    "WEAPON_POLE": "<:UI_GachaTypeIcon_Pole:1030825788024561715>",
    "WEAPON_SWORD_ONE_HAND": "<:UI_GachaTypeIcon_Sword:1030825790998319154>",
}

def get_weapon_type_emoji(weapon_type: str) -> str:
    return weapon_emoji_map.get(weapon_type, "")