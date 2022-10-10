from typing import Literal

import aiosqlite
from apps.text_map.text_map_app import text_map
from discord import Locale
from text_maps.artifact_main_stat import art_main_stat_map


def get_weekday_name(
    day_num: int,
    locale: Locale,
    user_locale: Literal["str", None],
    full_name: bool = False,
) -> str:
    if not full_name:
        weekday_dict = {
            0: text_map.get(25, locale, user_locale),
            1: text_map.get(26, locale, user_locale),
            2: text_map.get(27, locale, user_locale),
            3: text_map.get(28, locale, user_locale),
            4: text_map.get(29, locale, user_locale),
            5: text_map.get(30, locale, user_locale),
            6: text_map.get(31, locale, user_locale),
        }
    else:
        weekday_dict = {
            0: text_map.get(234, locale, user_locale),
            1: text_map.get(235, locale, user_locale),
            2: text_map.get(236, locale, user_locale),
            3: text_map.get(237, locale, user_locale),
            4: text_map.get(238, locale, user_locale),
            5: text_map.get(239, locale, user_locale),
            6: text_map.get(240, locale, user_locale),
        }
    return weekday_dict.get(day_num)

def translate_main_stat(main_stat: str, locale: Locale | str) -> str:
    if str(locale) == "zh-TW" or str(locale) == "zh-CN":
        return main_stat
    result = ""
    for index, stat in enumerate(main_stat):
        result += art_main_stat_map.get(stat, stat)
        if index != len(main_stat) - 1:
            result += "-"
    return result

def get_element_name(
    element_name: str, locale: Locale, user_locale: Literal["str", None]
) -> str:
    element_dict = {
        "Cryo": text_map.get(213, locale, user_locale),
        "Geo": text_map.get(214, locale, user_locale),
        "Pyro": text_map.get(215, locale, user_locale),
        "Anemo": text_map.get(216, locale, user_locale),
        "Hydro": text_map.get(217, locale, user_locale),
        "Dendro": text_map.get(218, locale, user_locale),
        "Electro": text_map.get(219, locale, user_locale),
    }
    return (
        element_dict.get(element_name)
        or element_dict.get(element_name.lower())
        or element_name
    )


def get_month_name(month: int, locale: Locale, user_locale: Literal["str", None]):
    month_dict = {
        1: text_map.get(221, locale, user_locale),
        2: text_map.get(222, locale, user_locale),
        3: text_map.get(223, locale, user_locale),
        4: text_map.get(224, locale, user_locale),
        5: text_map.get(225, locale, user_locale),
        6: text_map.get(226, locale, user_locale),
        7: text_map.get(227, locale, user_locale),
        8: text_map.get(228, locale, user_locale),
        9: text_map.get(229, locale, user_locale),
        10: text_map.get(230, locale, user_locale),
        11: text_map.get(231, locale, user_locale),
        12: text_map.get(232, locale, user_locale),
    }
    return month_dict.get(month) or month


async def get_user_locale(user_id: int, db: aiosqlite.Connection) -> str | None:
    c = await db.cursor()
    await c.execute("SELECT lang FROM user_settings WHERE user_id = ?", (user_id,))
    user_lang = await c.fetchone()
    if user_lang is None:
        return None
    else:
        return user_lang[0]
