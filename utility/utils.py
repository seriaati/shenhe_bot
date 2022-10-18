import logging
import re
from itertools import islice
from typing import Dict, List, Optional
import aiosqlite
import discord
from dateutil import parser
from discord.utils import format_dt
from sentry_sdk.integrations.logging import LoggingIntegration
from PIL.ImageFont import FreeTypeFont

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging

sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)


def default_embed(title: str = "", message: str = ""):
    embed = discord.Embed(title=title, description=message, color=0xA68BD3)
    return embed


def error_embed(title: str = "", message: str = ""):
    embed = discord.Embed(title=title, description=message, color=0xFC5165)
    return embed


def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end


def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i : i + n]


def parse_HTML(HTML_string: str):
    HTML_string = HTML_string.replace("\\n", "\n")
    # replace tags with style attributes
    HTML_string = HTML_string.replace("</p>", "\n")
    HTML_string = HTML_string.replace("<strong>", "**")
    HTML_string = HTML_string.replace("</strong>", "**")

    # remove all HTML tags
    CLEANR = re.compile("<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});")
    HTML_string = re.sub(CLEANR, "", HTML_string)

    # remove time tags from mihoyo
    HTML_string = HTML_string.replace('t class="t_gl"', "")
    HTML_string = HTML_string.replace('t class="t_lc"', "")
    HTML_string = HTML_string.replace("/t", "")

    # turn date time string into discord timestamps
    matches = re.findall(r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}", HTML_string)
    for match in matches:
        datetime_obj = parser.parse(match)
        HTML_string = HTML_string.replace(match, format_dt(datetime_obj))

    return HTML_string


def divide_dict(d: Dict, size: int):
    it = iter(d)
    for i in range(0, len(d), size):
        yield {k: d[k] for k in islice(it, size)}


def get_weekday_int_with_name(weekday_name: str) -> int:
    weekday_name_dict = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    return weekday_name_dict.get(weekday_name)


def split_text_and_number(text: str) -> List[str]:
    for i, c in enumerate(text):
        if (
            c.isalpha() and text[i + 1].isdigit()
        ):  # the alphabet is followed by a numer immediately
            break
    result = [text[: i + 1], text[i + 1 :]]
    if result[1] == "":  # if the split fails
        for i, c in enumerate(text):
            if (
                c.isdigit() and text[i - 1] == " "
            ):  # the character before the number is a space
                break
    result = [text[: i + 1], text[i + 1 :]]
    return result


async def get_user_appearance_mode(user_id: int, db: aiosqlite.Connection) -> bool:
    c = await db.cursor()
    await c.execute("SELECT dark_mode FROM user_settings WHERE user_id = ?", (user_id,))
    mode = await c.fetchone()
    if mode is not None and mode[0] == 1:
        return True
    return False


async def get_user_timezone(user_id: int, db: aiosqlite.Connection) -> str:
    async with db.execute(
        "SELECT timezone FROM user_settings WHERE user_id = ?", (user_id,)
    ) as cursor:
        timezone = await cursor.fetchone()
    if timezone is None:
        return "Asia/Taipei"
    else:
        return timezone[0] or "Asia/Taipei"

def dynamic_font_size(text: str, initial_font_size: int, max_font_size: int, max_width: int, font: FreeTypeFont) -> int:
    font = font.font_variant(size=initial_font_size)
    font_size = initial_font_size
    while font.getlength(text) < max_width:
        if font_size == max_font_size:
            break
        font_size += 1
        font = font.font_variant(size=font_size)
    return font_size