import io
import os
import time
import typing

import aiofiles
import aiohttp
import discord
import enkanetwork as enka
from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw, ImageFont

import dev.asset as asset
from apps.text_map import text_map
from data.draw.fonts import FONTS
from dev.models import DefaultEmbed, DynamicBackgroundInput

from .general import log


def extract_file_name(url: str):
    """Extract file name from url."""
    return url.split("/")[-1].split("?")[0]


def extract_urls(objects: typing.List[typing.Any]) -> typing.List[str]:
    """Extract urls from a list of objects."""
    urls = []
    for obj in objects:
        if not hasattr(obj, "icon"):
            continue
        if obj.icon not in urls:
            urls.append(obj.icon)
    return urls


async def download_images(
    urls: typing.List[str], session: aiohttp.ClientSession
) -> None:
    """Download images from urls."""
    for url in urls:
        file_name = extract_file_name(url)
        path = f"apps/draw/cache/{file_name}"
        if os.path.exists(path):
            continue
        async with session.get(url) as resp:
            if resp.status == 200:
                async with aiofiles.open(path, "wb") as f:
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


def human_format(num: typing.Union[int, float]):
    """Format number to human readable format."""
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0

    two_sf = f"{num:.2f}"
    letters = ("", "K", "M", "G", "T", "P")

    if two_sf.split(".")[-1] == "00":
        return f"{round(num)}{letters[magnitude]}"

    return f"{two_sf}{letters[magnitude]}"


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
    image: Image.Image, background_color: typing.Optional[str] = None
) -> Image.Image:
    """Crop an image into a circle."""
    mask = Image.new("L", image.size, 0)
    empty = Image.new("RGBA", image.size, 0)
    draw = ImageDraw.Draw(mask)
    x, y = image.size
    circle_x, circle_y = image.size
    bbox = (
        x / 2 - circle_x / 2,
        y / 2 - circle_y / 2,
        x / 2 + circle_x / 2,
        y / 2 + circle_y / 2,
    )
    draw.ellipse(bbox, fill=255)
    image = Image.composite(image, empty, mask)
    if background_color is not None:
        background = Image.new("RGBA", image.size, 0)
        draw = ImageDraw.Draw(background)
        draw.ellipse(bbox, fill=background_color)
        background.paste(image, (0, 0), image)
        return background
    return image


def shorten_text(text: str, max_length: int, font: ImageFont.FreeTypeFont):
    if font.getlength(text) <= max_length:
        return text
    shortened = text[: max_length - 3] + "..."
    while font.getlength(shortened) > max_length and len(shortened) > 3:
        shortened = shortened[:-4] + "..."
    return shortened


def get_font_name(
    locale: discord.Locale | str,
    variation: typing.Literal[
        "Bold", "Light", "Thin", "Black", "Medium", "Regular"
    ] = "Regular",
) -> str:
    """Get a font name from the font folder."""
    path = "data/draw/resources/fonts/"
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
    variation: typing.Literal[
        "Bold", "Light", "Thin", "Black", "Medium", "Regular"
    ] = "Regular",
) -> ImageFont.FreeTypeFont:
    """Get a font"""
    font_name = get_font_name(locale, variation)
    return ImageFont.truetype(font_name, size)


def draw_dynamic_background(
    dynamic_input: DynamicBackgroundInput,
) -> typing.Tuple[Image.Image, int]:
    card_num = dynamic_input.card_num
    if card_num == 1:
        max_card_num = 1
    elif card_num % 2 == 0:
        max_card_num = max(i for i in range(1, card_num) if card_num % i == 0)
    else:
        max_card_num = max(
            i for i in range(1, card_num) if (card_num - (i - 1)) % i == 0
        )
    max_card_num = dynamic_input.max_card_num or min(max_card_num, 8)

    cols = (
        card_num // max_card_num + 1
        if card_num % max_card_num != 0
        else card_num // max_card_num
    )

    width = dynamic_input.left_padding
    if isinstance(dynamic_input.top_padding, int):
        height = dynamic_input.top_padding
    else:
        height = (
            dynamic_input.top_padding.with_title
            if dynamic_input.draw_title
            else dynamic_input.top_padding.without_title
        )  # top padding
    width += dynamic_input.right_padding
    height += dynamic_input.bottom_padding
    width += dynamic_input.card_width * cols  # width of the cards
    width += dynamic_input.card_x_padding * (cols - 1)  # padding between cards
    if card_num < max_card_num:
        max_card_num = card_num
    height += dynamic_input.card_height * max_card_num  # height of the cards
    height += dynamic_input.card_y_padding * (max_card_num - 1)  # padding between cards
    im = Image.new("RGB", (width, height), dynamic_input.background_color)  # type: ignore

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
    pos: typing.Tuple[int, int],
    text: str,
    size: int,
    fill: str,
    variation: str = "Regular",
    anchor: typing.Optional[str] = None,
):
    """Write a piece of text with the proper fonts"""
    # load fonts
    fonts: typing.Dict[str, TTFont] = {}
    for val in FONTS.values():
        path = f"data/draw/resources/fonts/{val['name']}-{variation}.{val['extension']}"
        fonts[path] = TTFont(file=path)

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
    return any(ord(glyph) in table.cmap.keys() for table in font["cmap"].tables)  # type: ignore


def resize_and_crop_image(
    im: Image.Image, version: int = 1, dark_mode: bool = False
) -> Image.Image:
    """Resize and crop an image to fit the card template"""
    im = im.convert("RGBA")

    # Define the target width and height
    target_width = 1663 if version == 1 else 472
    target_height = 629 if version == 1 else 839

    # Get the original width and height
    width, height = im.size

    # Calculate the ratio of the original image
    ratio = min(width / target_width, height / target_height)

    # Calculate the new size and left/top coordinates for cropping
    new_width = int(width / ratio)
    new_height = int(height / ratio)
    left = (new_width - target_width) / 2
    top = (new_height - target_height) / 2
    right = left + target_width
    bottom = top + target_height

    # Resize the image
    im = im.resize((new_width, new_height), resample=Image.LANCZOS)

    # Crop the image
    im = im.crop((left, top, right, bottom))

    if dark_mode:
        # add dark transparency to the image
        im = Image.alpha_composite(im, Image.new("RGBA", im.size, (0, 0, 0, 50)))  # type: ignore

    # make rounded corners
    radius = 20 if version == 1 else 25
    mask = Image.new("L", im.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, im.width, im.height), radius=radius, fill=255)
    im.putalpha(mask)

    # Return the resized and cropped image
    return im


def format_stat(stat: enka.EquipmentsStats) -> str:
    value = str(round(stat.value, 1))
    if stat.type is enka.DigitType.PERCENT:
        value += "%"
    return value


def mask_image_with_color(image: Image.Image, color) -> Image.Image:
    """Apply a color mask to an image"""
    image = image.convert("RGBA")
    mask = Image.new("RGBA", image.size, color)
    return ImageChops.multiply(image, mask)


def compress_image_util(fp_input: bytes) -> bytes:
    """Compress an image to a byte array"""
    im = Image.open(io.BytesIO(fp_input))
    fp = io.BytesIO()
    im = im.convert("RGB")
    im.save(fp, format="JPEG", optimize=True, quality=50)
    fp.seek(0)
    return fp.read()
