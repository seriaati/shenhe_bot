from discord import Locale


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
}

GENSHIN_OPTIMIZER_LANGS = {
    "zh-CN": 1,
    "zh-TW": 2,
    "de": 3,
    "en-US": 4,
    "es-ES": 5,
    "fr": 6,
    "in": 7,
    "it": 8,
    "ja": 9,
    "ko": 10,
    "pt-BR": 11,
    "ru": 12,
    "th": 13,
    "tr": 14,
    "vi": 15,
}

CROWDIN_FILE_PATHS = {
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
}

AMBR_EVENT_LANGS = {
    "zh-TW": "CHT",
    "zh-CN": "CHS",
    "en-US": "EN",
    "ja": "JP",
    "ko": "KR",
    "ru": "RU",
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
}


def to_enka(locale: Locale | str):
    return ENKA_LANGS.get(str(locale)) or "en"


def to_ambr_top(locale: Locale | str):
    return AMBR_LANGS.get(str(locale)) or "en"


def to_genshin_py(locale: Locale | str):
    return GENSHIN_PY_LANGS.get(str(locale)) or "en-us"


def to_go(locale: Locale | str):
    return GENSHIN_OPTIMIZER_LANGS.get(str(locale)) or 4


def to_paths(locale: Locale | str):
    return CROWDIN_FILE_PATHS.get(str(locale)) or "en-US"


def to_event_lang(locale: Locale | str):
    return AMBR_EVENT_LANGS.get(str(locale), "EN")


def to_hutao_login_lang(locale: Locale | str):
    return HUTAO_LOGIN_LANGS.get(str(locale), "en")

def to_genshin_db(locale: Locale | str):
    return GENSHIN_DB_LANGS.get(str(locale), "English")