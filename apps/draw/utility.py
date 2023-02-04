import math
import os
import time
import asset
from typing import Any, Dict, List, Literal, Optional, Tuple
from apps.text_map.text_map_app import text_map
import aiofiles
import aiohttp
import discord
import diskcache
import genshin
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from apps.genshin.custom_model import DynamicBackgroundInput
from data.draw.fonts import FONTS
from utility.utils import DefaultEmbed, log


def extract_file_name(url: str):
    """Extract file name from url."""
    return url.split("/")[-1].split("?")[0]


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
                async with aiofiles.open("apps/draw/cache/" + file_name, "wb") as f:
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
        
    if int("{:.2f}".format(num).split(".")[1]) == 0:
        return "%d%s" % (num, ["", "K", "M", "G", "T", "P"][magnitude])
    
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


def shorten_text(text: str, max_length: int, font: ImageFont.FreeTypeFont) -> str:
    """Shorten text to a maximum length."""
    if font.getlength(text) <= max_length:
        return text
    else:
        return text[: int(max_length // font.getlength("..."))] + "..."


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


def draw_dynamic_background(
    input: DynamicBackgroundInput,
) -> Tuple[Image.Image, int]:
    max_card_num = None
    for index in range(2, input.card_num):
        if input.card_num % index == 0:
            max_card_num = index
    max_card_num = input.max_card_num or max_card_num or 7
    if max_card_num > 7:
        max_card_num = 7
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


async def image_gen_transition(
    i: discord.Interaction, view: discord.ui.View, locale: discord.Locale | str
):
    """Disable all items in a view, show a loader text"""
    embed = DefaultEmbed().set_author(
        name=text_map.get(644, locale), icon_url=asset.loader
    )
    # disable all items in the view
    for item in view.children:
        # if item is a button or a select
        if isinstance(item, (discord.ui.Button, discord.ui.Select)):
            item.disabled = True
    try:
        await i.response.edit_message(embed=embed, view=view, attachments=[])
    except discord.InteractionResponded:
        await i.edit_original_response(embed=embed, view=view, attachments=[])


def global_write(
    draw: ImageDraw.ImageDraw,
    pos: Tuple[int, int],
    text: str,
    size: int,
    fill: str,
    variation: str = "Regular",
    anchor: Optional[str] = None,
):
    """Write a piece of text with the proper fonts"""
    # load fonts
    fonts: Dict[str, TTFont] = {}
    for val in FONTS.values():
        path = f"resources/fonts/{val['name']}-{variation}.{val['extension']}"
        fonts[path] = TTFont(path)

    # prior font is the font that was used for the previous glyph
    prior_font = None
    for glyph in text:
        # try to use the prior font
        if prior_font is not None and has_glyph(prior_font["font_obj"], glyph):
            f = ImageFont.truetype(prior_font["font_path"], size=size)
            draw.text(pos, glyph, fill=fill, anchor=anchor, font=f)
            pos = (pos[0] + f.getlength(glyph), pos[1])
            continue

        # prior font doesn't have the glyph, find a font that does
        found = False
        for font_path, ttfont_obj in fonts.items():
            f = ImageFont.truetype(font_path, size=size)
            if has_glyph(ttfont_obj, glyph):
                found = True
                prior_font = {"font_path": font_path, "font_obj": ttfont_obj}
                draw.text(pos, glyph, fill=fill, anchor=anchor, font=f)
                pos = (pos[0] + f.getlength(glyph), pos[1])
                break

        # sadly none of our fonts have the glyph, write the sad square
        f = ImageFont.truetype(list(fonts.keys())[0], size=size)
        if not found:
            draw.text(pos, glyph, fill=fill, anchor=anchor, font=f)
            pos = (pos[0] + f.getlength(glyph), pos[1])


def has_glyph(font: TTFont, glyph: str):
    for table in font["cmap"].tables:
        if ord(glyph) in table.cmap.keys():
            return True
    return False
