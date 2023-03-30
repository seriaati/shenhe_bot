from enum import Enum


class ArtifactType(Enum):
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

    ELEMENTAL_MASTERY = "Elemental Mastery"
    ENERGY_RECHARGE = "Energy Recharge"
    CRIT_RATE = "Crit Rate"
    CRIT_DMG = "Crit DMG"


class CharacterStat(Enum):
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
    NORMAL_ATTACK = "normalAttacks"
    ELEMENTAL_SKILL = "elementalSkill"
    ELEMENTAL_BUSRT = "elementalBurst"
