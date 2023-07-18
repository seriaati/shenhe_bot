from enum import Enum

from ambr import ItemCategory


class TodoAction(str, Enum):
    REMOVE = "remove"
    EDIT = "edit"


class TalentBoost(Enum):
    BOOST_E = "boost_e"
    BOOST_Q = "boost_q"


class CardType(Enum):
    OVERVIEW = "overview"
    RECENTS = "recents"


class CheckInAPI(Enum):
    VERCEL = "vercel"
    RENDER = "render"
    DETA = "deta"


class NotifType(Enum):
    RESIN = "resin_notification"
    POT = "pot_notification"
    PT = "pt_notification"
    TALENT = "talent_notification"
    WEAPON = "weapon_notification"
    EXPED = "exped_notif"


class GameType(Enum):
    GENSHIN = "genshin"
    HSR = "hsr"
    HONKAI = "honkai"


class BoardCategory(Enum):
    SINGLE_STRIKE = "single_strike_damage"
    CHARACTER_USAGE_RATE = "character_usage_rate"
    FULL_CLEAR = "full_clear"


class GenshinWikiCategory(Enum):
    CHARACTER = "avatar"
    WEAPON = "weapon"
    MATERIAL = "material"
    ARTIFACT = "reliquary"
    MONSTER = "monster"
    FOOD = "food"
    FURNITURE = "furniture"
    NAME_CARD = "namecard"
    BOOK = "book"
    TCG = "tcg"


class HSRWikiCategory(Enum):
    CHARACTER = "avatar"
    LIGHT_CONE = "equipment"
    ITEM = "item"
    RELIC = "relic"
    BOOK = "book"
    MESSAGE = "message"


CATEGORY_HASHES = {
    GenshinWikiCategory.CHARACTER: 815,
    GenshinWikiCategory.WEAPON: 816,
    GenshinWikiCategory.MATERIAL: 827,
    GenshinWikiCategory.ARTIFACT: 818,
    GenshinWikiCategory.MONSTER: 819,
    GenshinWikiCategory.FOOD: 820,
    GenshinWikiCategory.FURNITURE: 821,
    GenshinWikiCategory.NAME_CARD: 822,
    GenshinWikiCategory.BOOK: 823,
    GenshinWikiCategory.TCG: 831,
    HSRWikiCategory.CHARACTER: 815,
    HSRWikiCategory.LIGHT_CONE: 824,
    HSRWikiCategory.ITEM: 817,
    HSRWikiCategory.RELIC: 825,
    HSRWikiCategory.BOOK: 823,
    HSRWikiCategory.MESSAGE: 826,
}
