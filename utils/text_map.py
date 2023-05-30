from typing import Optional

from discord import Locale

from apps.text_map import text_map
from dev.enum import GameType
from text_maps.artifact_main_stat import ARTIFACT_MAIN_STAT_TRANSLATION

CITY_HASHES = {
    1: 129,
    2: 130,
    3: 131,
    4: 510,
    0: 700,
}


def get_city_name(
    city_id: int,
    lang: str,
) -> str:
    return text_map.get(CITY_HASHES.get(city_id, 0), lang)


def get_weekday_name(
    day_num: int,
    lang: Locale | str,
    user_locale: Optional[str] = None,
    full_name: bool = False,
) -> str:
    if not full_name:
        weekday_dict = {
            0: text_map.get(25, lang, user_locale),
            1: text_map.get(26, lang, user_locale),
            2: text_map.get(27, lang, user_locale),
            3: text_map.get(28, lang, user_locale),
            4: text_map.get(29, lang, user_locale),
            5: text_map.get(30, lang, user_locale),
            6: text_map.get(31, lang, user_locale),
        }
    else:
        weekday_dict = {
            0: text_map.get(234, lang, user_locale),
            1: text_map.get(235, lang, user_locale),
            2: text_map.get(236, lang, user_locale),
            3: text_map.get(237, lang, user_locale),
            4: text_map.get(238, lang, user_locale),
            5: text_map.get(239, lang, user_locale),
            6: text_map.get(240, lang, user_locale),
        }
    return weekday_dict.get(day_num, "Unknown weekday")


def translate_main_stat(main_stat: str, lang: Locale | str) -> str:
    if str(lang) == "zh-TW" or str(lang) == "zh-CN":
        return main_stat
    result = ""
    for index, stat in enumerate(main_stat):
        result += ARTIFACT_MAIN_STAT_TRANSLATION.get(stat, stat)
        if index != len(main_stat) - 1:
            result += " | "
    return result


def get_element_name(
    element_name: str, lang: Locale | str, user_locale: Optional[str] = None
) -> str:
    element_dict = {
        "Cryo": text_map.get(213, lang, user_locale),
        "Geo": text_map.get(214, lang, user_locale),
        "Pyro": text_map.get(215, lang, user_locale),
        "Anemo": text_map.get(216, lang, user_locale),
        "Hydro": text_map.get(217, lang, user_locale),
        "Dendro": text_map.get(218, lang, user_locale),
        "Electro": text_map.get(219, lang, user_locale),
        "Omni": text_map.get(720, lang, user_locale),
        "Black": text_map.get(721, lang, user_locale),
        "Energy": text_map.get(722, lang, user_locale),
    }
    return (
        element_dict.get(element_name)
        or element_dict.get(element_name.lower())
        or element_name
    )


def get_month_name(
    month: int, lang: Locale | str, user_locale: Optional[str] = None
) -> str:
    month_dict = {
        1: text_map.get(221, lang, user_locale),
        2: text_map.get(222, lang, user_locale),
        3: text_map.get(223, lang, user_locale),
        4: text_map.get(224, lang, user_locale),
        5: text_map.get(225, lang, user_locale),
        6: text_map.get(226, lang, user_locale),
        7: text_map.get(227, lang, user_locale),
        8: text_map.get(228, lang, user_locale),
        9: text_map.get(229, lang, user_locale),
        10: text_map.get(230, lang, user_locale),
        11: text_map.get(231, lang, user_locale),
        12: text_map.get(232, lang, user_locale),
    }
    return month_dict.get(month, str(month))


GAMES = {
    GameType.GENSHIN: 313,
    GameType.HSR: 770,
    GameType.HONKAI: 771,
}


def get_game_name(game: GameType, lang: str) -> str:
    return text_map.get(GAMES.get(game, 700), lang)
