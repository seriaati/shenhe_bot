import math
import os
import re
import time
from typing import Any, List, Literal, Optional, Tuple

import aiofiles
import aiohttp
import discord
import diskcache
import genshin
from PIL import Image, ImageDraw, ImageFont

from apps.genshin.custom_model import DynamicBackgroundInput
from data.draw.fonts import FONTS
from utility.utils import log


def extract_file_name(url: str):
    """Extract file name from url."""
    return url.split("/")[-1]


def extract_urls(objects: List[Any]) -> List[str]:
    """Extract urls from a list of objects."""
    urls = []
    for obj in objects:
        if not hasattr(obj, "icon"):
            continue
        if obj.icon not in urls:
            urls.append(obj.icon)
    return urls


async def download_images(urls: List[str], session: aiohttp.ClientSession) -> None:
    """Download images from urls."""
    for url in urls:
        file_name = extract_file_name(url)
        if os.path.exists("apps/draw/cache/" + file_name):
            continue
        async with session.get(url) as resp:
            if resp.status == 200:
                async with aiofiles.open(
                    "apps/draw/cache/" + file_name, "wb"
                ) as f:
                    await f.write(await resp.read())


def get_cache(url: str) -> Image.Image:
    """Get a cached image file from url."""
    return Image.open("apps/draw/cache/" + extract_file_name(url))


def calculate_time(func):
    """Decorator to calculate the time spent on executing a function."""

    async def inner_func(*args, **kwargs):
        begin = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        log.info(f"[Draw][{func.__name__}] Time: {round(end-begin, 5)}s")
        return result

    return inner_func


def human_format(num: int | float):
    """Format number to human readable format."""
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return "%.2f%s" % (num, ["", "K", "M", "G", "T", "P"][magnitude])


def dynamic_font_size(
    text: str,
    initial_font_size: int,
    max_font_size: int,
    max_width: int,
    font: ImageFont.FreeTypeFont,
) -> ImageFont.FreeTypeFont:
    """Dynamically adjust font size to fit text into a box."""
    font = font.font_variant(size=initial_font_size)
    font_size = initial_font_size
    while font.getlength(text) < max_width:
        if font_size == max_font_size:
            break
        font_size += 1
        font = font.font_variant(size=font_size)
    return font.font_variant(size=font_size)


def circular_crop(
    image: Image.Image, background_color: Optional[str] = None
) -> Image.Image:
    """Crop an image into a circle."""
    mask = Image.new("L", image.size, 0)
    empty = Image.new("RGBA", image.size, 0)
    draw = ImageDraw.Draw(mask)
    x, y = image.size
    eX, eY = image.size
    bbox = (x / 2 - eX / 2, y / 2 - eY / 2, x / 2 + eX / 2, y / 2 + eY / 2)
    draw.ellipse(bbox, fill=255)
    image = Image.composite(image, empty, mask)
    if background_color is not None:
        background = Image.new("RGBA", image.size, 0)
        draw = ImageDraw.Draw(background)
        draw.ellipse(bbox, fill=background_color)
        background.paste(image, (0, 0), image)
        return background
    return image


def format_number(text: str) -> str:
    """Format numbers into bolded texts."""
    return re.sub("(\(?\d+.?\d+%?\)?)", r" **\1** ", text)


def shorten_text(text: str, max_length: int, font: ImageFont.FreeTypeFont) -> str:
    """Shorten text to a maximum length."""
    if font.getlength(text) <= max_length:
        return text
    else:
        return (
            text[: -len(text) + math.floor(max_length / font.getlength("..."))] + "..."
        )


def get_font_name(
    locale: discord.Locale | str,
    variation: Literal[
        "Bold", "Light", "Thin", "Black", "Medium", "Regular"
    ] = "Regular",
) -> str:
    """Get a font name from the font folder."""
    path = "resources/fonts/"
    default = {"extension": "ttf", "name": "NotoSans"}
    return (
        path
        + FONTS.get(str(locale), default)["name"]
        + "-"
        + variation
        + "."
        + FONTS.get(str(locale), default)["extension"]
    )


def get_font(
    locale: discord.Locale | str,
    size: int,
    variation: Literal[
        "Bold", "Light", "Thin", "Black", "Medium", "Regular"
    ] = "Regular",
) -> ImageFont.FreeTypeFont:
    """Get a font"""
    font_name = get_font_name(locale, variation)
    return ImageFont.truetype(font_name, size)

def get_l_character_data(uuid: str) -> genshin.models.Character:
    with diskcache.FanoutCache("data/abyss_leaderboard") as cache:
        character_data = cache.get(uuid)
        if character_data is None:
            raise ValueError("Character data not found")
        return character_data
    
def draw_dynamic_background(
    input: DynamicBackgroundInput,
) -> Tuple[Image.Image, int]:
    max_card_num = None
    for index in range(2, input.card_num):
        if input.card_num % index == 0:
            max_card_num = index
    max_card_num = input.max_card_num or max_card_num or 7
    num = input.card_num
    cols = num // max_card_num + 1 if num % max_card_num != 0 else num // max_card_num
    width = input.left_padding
    height = (
        input.top_padding.with_title
        if input.draw_title
        else input.top_padding.without_title
    )  # top padding
    width += input.right_padding
    height += input.bottom_padding
    width += input.card_width * cols  # width of the cards
    width += input.card_x_padding * (cols - 1)  # padding between cards
    if num < max_card_num:
        max_card_num = num
    height += input.card_height * max_card_num  # height of the cards
    height += input.card_y_padding * (max_card_num - 1)  # padding between cards
    im = Image.new("RGB", (width, height), input.background_color)

    return im, max_card_num