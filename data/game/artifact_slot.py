from discord import Locale
from enkanetwork import enum

from apps.text_map import text_map

ARTIFACT_SLOT_EMOJIS = {
    enum.EquipType.Flower: "<:Flower_of_Life:982167959717945374>",
    enum.EquipType.Feather: "<:Plume_of_Death:982167959915077643>",
    enum.EquipType.Sands: "<:Sands_of_Eon:982167959881547877>",
    enum.EquipType.Goblet: "<:Goblet_of_Eonothem:982167959835402240>",
    enum.EquipType.Circlet: "<:Circlet_of_Logos:982167959692787802>",
}


def get_artifact_slot_emoji(slot: enum.EquipType) -> str:
    return ARTIFACT_SLOT_EMOJIS.get(slot, "")


def get_artifact_slot_name(slot: enum.EquipType, lang: Locale | str) -> str:
    if slot is enum.EquipType.Flower:
        return text_map.get(734, lang)
    if slot is enum.EquipType.Feather:
        return text_map.get(735, lang)
    if slot is enum.EquipType.Sands:
        return text_map.get(736, lang)
    if slot is enum.EquipType.Goblet:
        return text_map.get(737, lang)
    if slot is enum.EquipType.Circlet:
        return text_map.get(738, lang)
    return ""
