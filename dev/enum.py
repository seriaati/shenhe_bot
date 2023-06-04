from enum import Enum


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


class GameType(Enum):
    GENSHIN = "genshin"
    HSR = "hsr"
    HONKAI = "honkai"


class Category(Enum):
    SINGLE_STRIKE = "single_strike_damage"
    CHARACTER_USAGE_RATE = "character_usage_rate"
    FULL_CLEAR = "full_clear"
