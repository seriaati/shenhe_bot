import logging
import re
from datetime import datetime
from itertools import islice
from typing import Any, Dict, List, Optional, Union
from apps.text_map.text_map_app import text_map

import asyncpg
import discord
from sentry_sdk.integrations.logging import LoggingIntegration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("log.log"),
        logging.StreamHandler(),
    ],
)
log = logging

sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)


class DefaultEmbed(discord.Embed):
    def __init__(self, title: Optional[str] = None, description: Optional[str] = None):
        super().__init__(title=title, description=description, color=0xA68BD3)


class ErrorEmbed(discord.Embed):
    def __init__(self, title: Optional[str] = None, description: Optional[str] = None):
        super().__init__(title=title, description=description, color=0xFC5165)

    def set_title(
        self,
        map_hash: int,
        locale: Union[discord.Locale, str],
        user: Union[discord.Member, discord.User],
    ):
        self.set_author(
            name=text_map.get(map_hash, locale), icon_url=user.display_avatar.url
        )
        return self


def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    return start <= x or x <= end


def divide_chunks(l: List[Any], n: int):
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

    return HTML_string


def divide_dict(d: Dict, size: int):
    it = iter(d)
    for _ in range(0, len(d), size):
        yield {k: d[k] for k in islice(it, size)}


def format_number(text: str) -> str:
    """Format numbers into bolded texts."""
    return re.sub(r"(\(?\d+.?\d+%?\)?)", r" **\1** ", text)  # type: ignore


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
    return weekday_name_dict.get(weekday_name, 0)


async def get_user_appearance_mode(user_id: int, pool: asyncpg.Pool) -> bool:
    dark_mode: Optional[bool] = await pool.fetchval(
        "SELECT dark_mode FROM user_settings WHERE user_id = $1", user_id
    )
    if dark_mode is None:
        return False
    return dark_mode


async def get_user_notification(user_id: int, pool: asyncpg.Pool) -> bool:
    notification: Optional[bool] = await pool.fetchval(
        "SELECT notification FROM user_settings WHERE user_id = $1", user_id
    )
    if notification is None:
        return True
    return notification


async def get_user_auto_redeem(user_id: int, pool: asyncpg.Pool) -> bool:
    auto_redeem: Optional[bool] = await pool.fetchval(
        "SELECT auto_redeem FROM user_settings WHERE user_id = $1", user_id
    )
    if auto_redeem is None:
        return False
    return auto_redeem


def get_dt_now() -> datetime:
    """Get current datetime in UTC+8"""
    return datetime.now()


def add_bullet_points(texts: List[str]) -> str:
    """Add bullet points to a list of texts."""
    return "\n".join([f"• {text}" for text in texts])


def disable_view_items(view: discord.ui.View) -> None:
    """Disable all items in a view.

    Args:
        view (discord.ui.View): The view to disable items in.
    """
    for child in view.children:
        if isinstance(child, (discord.ui.Select, discord.ui.Button)):
            child.disabled = True
