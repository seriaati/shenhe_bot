from typing import Literal

from discord import Locale


to_enka_dict = {
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
}

to_ambr_top_dict = {
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
}

to_genshin_py_dict = {
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
}

to_go_dict = {
    "zh-CN": 1,
    "zh-TW": 2,
    "de": 3,
    "en-US": 4,
    "es-ES": 4,
    "fr": 5,
    "in": 6,
    "ja": 7,
    "ko": 8,
    "pt-BR": 9,
    "ru": 10,
    "th": 11,
    "vi": 12,
}

paths = {
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
}

to_event_lang_dict = {
    "zh-TW": "CHT",
    "zh-CN": "CHS",
    "en-US": "EN",
    "ja": "JP",
    "ko": "KR",
    "ru": "RU",
}

to_hutao_login_dict = {
    "zh-TW": "zh-tw",
    "zh-CN": "zh-cn",
    "th": "th",
    "ja": "jp",
    "en-US": "en",
}


def to_enka(locale: Locale | str):
    return to_enka_dict.get(str(locale)) or "en"


def to_ambr_top(locale: Locale | str):
    return to_ambr_top_dict.get(str(locale)) or "en"


def to_genshin_py(locale: Locale | str):
    return to_genshin_py_dict.get(str(locale)) or "en-us"


def to_go(locale: Locale | str):
    return to_go_dict.get(str(locale)) or 4


def to_paths(locale: Locale | str):
    return paths.get(str(locale)) or "en-US"


def to_event_lang(locale: Locale | str):
    return to_event_lang_dict.get(str(locale), "EN")


def to_hutao_login_lang(locale: Locale | str):
    return to_hutao_login_dict.get(str(locale), "en")
