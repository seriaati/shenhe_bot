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

class TextMapType(Enum):
    LANG = "langs"
    
    ARTIFACT = "reliquary"
    CHARACTER = "avatar"
    MATERIAL = "material"
    WEAPON = "weapon"
    DOMAIN = "dailyDungeon"
    ITEM_NAME = "item_name"

class LangType(Enum):
    EN_US = "en-US"
    JA_JP = "ja-JP"
    TH_TH = "th-TH"
    ZH_CN = "zh-CN"
    ZH_TW = "zh-TW"
    ID_ID = "id-ID"
    UK_UA = "uk-UA"