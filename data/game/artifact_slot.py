from discord import Locale
from enkanetwork import enum

from apps.text_map.text_map_app import text_map

ARTIFACT_SLOT_EMOJIS = {
    0: "<:Flower_of_Life:982167959717945374>",
    1: "<:Plume_of_Death:982167959915077643>",
    2: "<:Sands_of_Eon:982167959881547877>",
    3: "<:Goblet_of_Eonothem:982167959835402240>",
    4: "<:Circlet_of_Logos:982167959692787802>",
}

def get_artifact_slot_emoji(slot: int) -> str:
    return ARTIFACT_SLOT_EMOJIS.get(slot, "")


def get_artifact_slot_name(slot: enum.EquipType, locale: Locale | str):
    if slot is enum.EquipType.Flower:
        return text_map.get(734, locale)
    elif slot is enum.EquipType.Feather:
        return text_map.get(735, locale)
    elif slot is enum.EquipType.Sands:
        return text_map.get(736, locale)
    elif slot is enum.EquipType.Goblet:
        return text_map.get(737, locale)
    elif slot is enum.EquipType.Circlet:
        return text_map.get(738, locale)