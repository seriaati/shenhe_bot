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

class CheckInType(Enum):
    LOCAL = "local"
    API = "api"

class CheckInAPI(Enum):
    VERCEL = "vercel"
    RENDER = "render"
    DETA = "deta"