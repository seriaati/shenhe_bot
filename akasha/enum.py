from enum import Enum


class ArtifactType(Enum):
    """Artifact type enum."""

    SANDS = "EQUIP_SHOES"
    GOBLET = "EQUIP_RING"
    CIRCLET = "EQUIP_DRESS"


class AritfactMainStat(Enum):
    """Artifact main stat enum."""

    HP_PERCENT = "HP%"
    ATK_PERCENT = "ATK%"
    DEF_PERCENT = "DEF%"

    HP = "HP"
    ATK = "ATK"
    DEF = "DEF"

    GEO_DMG_BONUS = "Geo DMG Bonus"
    ANEMO_DMG_BONUS = "Anemo DMG Bonus"
    PYRO_DMG_BONUS = "Pyro DMG Bonus"
    HYDRO_DMG_BONUS = "Hydro DMG Bonus"
    ELECTRO_DMG_BONUS = "Electro DMG Bonus"
    CRYO_DMG_BONUS = "Cryo DMG Bonus"
    DENDRO_DMG_BONUS = "Dendro DMG Bonus"
    PHYSICAL_DMG_BONUS = "Physical DMG Bonus"
    HEALING_BONUS = "Healing Bonus"

    ELEMENTAL_MASTERY = "Elemental Mastery"
    ENERGY_RECHARGE = "Energy Recharge"
    CRIT_RATE = "Crit RATE"
    CRIT_DMG = "Crit DMG"


class CharacterStat(Enum):
    """Character stat enum."""

    CRIT_RATE = "critRate"
    CRIT_DMG = "critDamage"
    ENERGY_RECHARGE = "energyRecharge"
    HEALING_BONUS = "healingBonus"
    INCOMING_HEALING_BONUS = "incomingHealingBonus"
    ELEMENTAL_MASTERY = "elementalMastery"

    PHYSICAL_DMG_BONUS = "physicalDamageBonus"
    PYRO_DMG_BONUS = "pyroDamageBonus"
    HYDRO_DMG_BONUS = "hydroDamageBonus"
    ELECTRO_DMG_BONUS = "electroDamageBonus"
    ANEMO_DMG_BONUS = "anemoDamageBonus"
    CRYO_DMG_BONUS = "cryoDamageBonus"
    GEO_DMG_BONUS = "geoDamageBonus"
    DENDRO_DMG_BONUS = "dendroDamageBonus"

    MAX_HP = "maxHp"
    ATK = "atk"
    DEF = "def"


class TalentType(Enum):
    """Talent type enum."""

    NORMAL_ATTACK = "normalAttacks"
    ELEMENTAL_SKILL = "elementalSkill"
    ELEMENTAL_BUSRT = "elementalBurst"


class OptionType(Enum):
    """Option type enum."""


class FilterType(OptionType):
    """Filter type enum."""

    REGION = "region"

    WEAPON = "weapon.name"
    REFINEMENT = "weapon.weaponInfo.refinementLevel.evel.value"

    NAME = "name"
    CONSTELLATION = "constellation"

    ONE_PIECE = "artifactSets.$1"
    TWO_PIECE = "artifactSets.$2"
    FOUR_PIECE = "artifactSets.$4"

    SANDS_MAIN_STAT = "artifactObjects.EQUIP_SHOES.mainStatKey"
    GOBLET_MAIN_STAT = "artifactObjects.EQUIP_RING.mainStatKey"
    CIRCLET_MAIN_STAT = "artifactObjects.EQUIP_DRESS.mainStatKey"


class PageType(OptionType):
    LESS_THAN = "lt"
    GREATER_THAN = "gt"
