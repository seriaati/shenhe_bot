import logging
import re
from datetime import datetime
from itertools import islice
from typing import Any, Dict, List, Optional, Union

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
        text_map,
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


def divide_chunks(li: List[Any], n: int):
    for i in range(0, len(li), n):
        yield li[i : i + n]


def parse_html(html_string: str):
    html_string = html_string.replace("\\n", "\n")
    # replace tags with style attributes
    html_string = html_string.replace("</p>", "\n")
    html_string = html_string.replace("<strong>", "**")
    html_string = html_string.replace("</strong>", "**")

    # remove all HTML tags
    CLEANR = re.compile(r"<[^>]*>|&([a-z0-9]+|#\d{1,6}|#x[0-9a-f]{1,6});")
    html_string = re.sub(CLEANR, "", html_string)

    # remove time tags from mihoyo
    html_string = html_string.replace('t class="t_gl"', "")
    html_string = html_string.replace('t class="t_lc"', "")
    html_string = html_string.replace("/t", "")

    return html_string


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


async def send_embed(user: Union[discord.User, discord.Member], embed: discord.Embed):
    try:
        await user.send(embed=embed)
    except discord.Forbidden:
        pass
