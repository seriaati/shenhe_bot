import json
import logging
import re
import zipfile
from datetime import datetime
from io import BytesIO
from itertools import islice
from typing import Dict, Generator, List, TypeVar, Union

import aiohttp
import discord
import pytz
from sentry_sdk.integrations.logging import LoggingIntegration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("log.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
    encoding="utf-8",
)
log = logging
sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)


def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    return start <= x or x <= end


T = TypeVar("T")


def divide_chunks(li: List[T], n: int) -> Generator[list[T], None, None]:
    return (li[i : i + n] for i in range(0, len(li), n))


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


def get_dt_now(with_tz: bool = False) -> datetime:
    """Get current datetime in UTC+8"""
    tz = pytz.timezone("Asia/Shanghai")  # UTC+8 timezone
    utc_now = datetime.utcnow()  # get current UTC time
    utc8_now = utc_now.replace(tzinfo=pytz.utc).astimezone(
        tz
    )  # convert to UTC+8 timezone
    if not with_tz:
        return utc8_now.replace(tzinfo=None)
    return utc8_now


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


async def dm_embed(
    user: Union[discord.User, discord.Member], embed: discord.Embed
) -> bool:
    """
    Send a Discord embed message to a user via direct message.

    Args:
        user (Union[discord.User, discord.Member]): The user to send the message to.
        embed (discord.Embed): The embed to send.

    Returns:
        bool: True if the message was sent successfully, False otherwise.

    Raises:
        Nothing.

    This function attempts to send a Discord embed to the specified user via direct message. If the send is
    successful, the function returns True. If the send fails due to a Discord.Forbidden or DiscordServerError error,
    the function returns False.
    """
    try:
        await user.send(embed=embed)
    except (discord.Forbidden, discord.DiscordServerError):
        return False
    else:
        return True


def convert_dict_to_zipped_json(data_dict: Dict[str, str]) -> BytesIO:
    """
    Description:
        This function takes a dictionary and returns a BytesIO object containing a zip file that contains a JSON file.
        The JSON file contains the dictionary converted to a JSON string.

    Arguments:
        data_dict: A dictionary of strings to strings

    Returns:
        A BytesIO object containing a zip file that contains a JSON file.
    """
    # Convert dictionary to JSON string
    json_str: str = json.dumps(data_dict)

    # Create a BytesIO object to hold the zip file
    zip_buffer: BytesIO = BytesIO()

    # Create a zip archive containing the JSON file
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("data.json", json_str)

    # Reset the buffer pointer to the beginning of the buffer
    zip_buffer.seek(0)

    # Return the BytesIO object containing the zipped file
    return zip_buffer


async def get_dc_user(bot: discord.Client, user_id: int) -> discord.User:
    """Get a discord user from their id. If the user is not cached, fetch them from the discord API"""
    return bot.get_user(user_id) or await bot.fetch_user(user_id)


async def upload_img(url: str, session: aiohttp.ClientSession) -> str:
    payload = {
        "key": "6d207e02198a847aa98d0a2a901485a5",
        "source": url,
    }
    async with session.post(
        "https://freeimage.host/api/1/upload", data=payload
    ) as resp:
        data = await resp.json()
    return data["image"]["url"]
