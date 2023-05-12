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
    LOCAL = "local"
    VERCEL = "vercel"
    RENDER = "render"
    DETA = "deta"
    RAILWAY = "railway"


class NotificationType(Enum):
    RESIN = "resin"
    POT = "pot"
    PT = "pt"

class GameType(Enum):
    GENSHIN = "genshin"
    HSR = "hsr"
    HONKAI = "honkai"