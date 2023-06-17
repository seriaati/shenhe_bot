from discord import Locale
from mihomo import Language

MIHOMO_LANGS = {
    "zh-CN": Language.CHS,
    "zh-TW": Language.CHT,
    "de": Language.DE,
    "en-US": Language.EN,
    "es-ES": Language.ES,
    "fr": Language.FR,
    "ja": Language.JP,
    "ko": Language.KR,
    "th": Language.TH,
    "pt-BR": Language.PT,
    "ru": Language.RU,
    "vi": Language.VI,
}

ENKA_LANGS = {
    "zh-CN": "chs",
    "zh-TW": "cht",
    "de": "de",
    "en-US": "en",
    "es-ES": "es",
    "fr": "fr",
    "ja": "jp",
    "ko": "kr",
    "th": "th",
    "pt-BR": "pt",
    "ru": "ru",
    "vi": "vi",
    "it": "it",
    "tr": "tr",
    "id": "id",
}

AMBR_LANGS = {
    "zh-CN": "chs",
    "zh-TW": "cht",
    "de": "de",
    "en-US": "en",
    "es-ES": "es",
    "fr": "fr",
    "ja": "jp",
    "ko": "kr",
    "th": "th",
    "pt-BR": "pt",
    "ru": "ru",
    "vi": "vi",
    "it": "it",
    "tr": "tr",
    "id": "id",
}

GENSHIN_PY_LANGS = {
    "zh-CN": "zh-cn",
    "zh-TW": "zh-tw",
    "de": "de-de",
    "en-US": "en-us",
    "es-ES": "es-es",
    "fr": "fr-fr",
    "ja": "ja-jp",
    "ko": "ko-kr",
    "th": "th-th",
    "pt-BR": "pt-pt",
    "ru": "ru-ru",
    "vi": "vi-vn",
    "it": "it-it",
    "tr": "tr-tr",
    "id": "id-id",
}

GENSHIN_OPTIMIZER_LANGS = {
    "zh-CN": 1,
    "zh-TW": 2,
    "de": 3,
    "en-US": 4,
    "es-ES": 5,
    "fr": 6,
    "id": 7,
    "it": 8,
    "ja": 9,
    "ko": 10,
    "pt-BR": 11,
    "ru": 12,
    "th": 13,
    "tr": 14,
    "vi": 15,
}

CROWDIN_LANGS = {
    "de": "de-DE",
    "en-US": "en-US",
    "es-ES": "es-ES",
    "fr": "fr-FR",
    "ja": "ja-JP",
    "ko": "ko-KR",
    "pt-BR": "pt-PT",
    "ru": "ru-RU",
    "th": "th-TH",
    "vi": "vi-VN",
    "zh-CN": "zh-CN",
    "zh-TW": "zh-TW",
    "uk": "uk-UA",
    "id": "id-ID",
}

HUTAO_LOGIN_LANGS = {
    "zh-TW": "zh-tw",
    "zh-CN": "zh-cn",
    "th": "th",
    "ja": "jp",
    "en-US": "en",
}

GENSHIN_DB_LANGS = {
    "zh-TW": "ChineseTraditional",
    "zh-CN": "ChineseSimplified",
    "en-US": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian",
    "de": "German",
    "fr": "French",
    "es-ES": "Spanish",
    "pt-BR": "Portuguese",
    "th": "Thai",
    "vi": "Vietnamese",
    "it": "Italian",
    "tr": "Turkish",
    "id": "Indonesian",
}


def to_ambr_top(lang: Locale | str):
    return AMBR_LANGS.get(str(lang)) or "en"


def to_genshin_py(lang: Locale | str):
    return GENSHIN_PY_LANGS.get(str(lang)) or "en-us"
