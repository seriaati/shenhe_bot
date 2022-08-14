from typing import Literal

from discord import Locale


to_enka_dict = {
    'zh-CN': 'chs',
    'zh-TW': 'cht',
    'de': 'de',
    'en-US': 'en',
    'es-ES': 'es',
    'fr': 'fr',
    'ja': 'jp',
    'ko': 'kr',
    'th': 'th',
    'pt-BR': 'pt',
    'ru': 'ru',
    'vi': 'vi'
}

to_ambr_top_dict = {
    'zh-CN': 'chs',
    'zh-TW': 'cht',
    'de': 'de',
    'en-US': 'en',
    'es-ES': 'es',
    'fr': 'fr',
    'ja': 'jp',
    'ko': 'kr',
    'th': 'th',
    'pt-BR': 'pt',
    'ru': 'ru',
    'vi': 'vi'
}

to_genshin_py_dict = {
    'zh-CN': 'zh-cn',
    'zh-TW': 'zh-tw',
    'de': 'de-de',
    'en-US': 'en-us',
    'es-ES': 'es-es',
    'fr': 'fr-fr',
    'ja': 'ja-jp',
    'ko': 'ko-kr',
    'th': 'th-th',
    'pt-BR': 'pt-pt',
    'ru': 'ru-ru',
    'vi': 'vi-vn'
}

to_go_dict = {
    'zh-CN': 1,
    'zh-TW': 2,
    'de': 3,
    'en-US': 4,
    'es-ES': 5,
    'fr': 6,
    'in': 7,
    'ja': 8,
    'ko': 9,
    'pt-BR': 10,
    'ru': 11,
    'th': 12,
    'vi': 13
}

paths = {
    'de': 'de-DE',
    'en-US': 'en-US',
    'es-ES': 'es-ES',
    'fr': 'fr-FR',
    'ja': 'ja-JP',
    'ko': 'ko-KR',
    'pt-BR': 'pt-PT',
    'ru': 'ru-RU',
    'th': 'th-TH',
    'vi': 'vi-VN',
    'zh-CN': 'zh-CN'
}


def to_enka(locale: Locale | str):
    return to_enka_dict.get(str(locale)) or 'en'


def to_ambr_top(locale: Locale | str):
    return to_ambr_top_dict.get(str(locale)) or 'en'


def to_genshin_py(locale: Locale | str):
    return to_genshin_py_dict.get(str(locale)) or 'en-us'


def to_go(locale: Locale | str):
    return to_go_dict.get(str(locale)) or 4

def to_paths(locale: Locale | str):
    return paths.get(str(locale)) or 'en-US'