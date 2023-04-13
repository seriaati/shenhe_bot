import io
from typing import List, Optional, Tuple

import discord
from PIL import Image, ImageDraw

import dev.asset as asset
from ambr import Material
from dev.models import DynamicBackgroundInput, TopPadding
from utils import (
    circular_crop,
    draw_dynamic_background,
    dynamic_font_size,
    get_cache,
    get_font,
    human_format,
)


def material_card(
    material_list: List[Tuple[Material, int | str]],
    title: str,
    dark_mode: bool,
    locale: str | discord.Locale,
    draw_title: bool = True,
    background_color: Optional[str] = None,
) -> io.BytesIO:
    background_color = background_color or asset.light_theme_background
    if dark_mode:
        background_color = asset.dark_theme_background
    im, max_card_num = draw_dynamic_background(
        DynamicBackgroundInput(
            top_padding=TopPadding(with_title=190, without_title=90),
            left_padding=95,
            right_padding=95,
            bottom_padding=90,
            card_num=len(material_list),
            background_color=background_color,
            draw_title=draw_title,
            card_height=140,
            card_width=645,
            card_x_padding=60,
            card_y_padding=45,
        )
    )
    draw = ImageDraw.Draw(im)

    for index, material in enumerate(material_list):
        if material[0].id == 202:
            if isinstance(material[1], str) and material[1].isdigit():
                material = (material[0], human_format(int(material[1])))
            elif isinstance(material[1], int):
                material = (material[0], human_format(material[1]))
            elif "/" in material[1]:
                splited = material[1].split("/")
                material = (
                    material[0],
                    f"{human_format(int(splited[0]))}/{human_format(int(splited[1]))}",
                )

        # draw the card
        card = small_card(material[0], material[1], dark_mode, locale)

        # paste the card
        x = 95 + (644 + 60) * (index // max_card_num)
        padding = 190 if draw_title else 90
        y = padding + (140 + 45) * (index % max_card_num)
        im.paste(card, (x, y), card)

    # title
    if draw_title:
        font = get_font(locale, 75, "Bold")
        fill = asset.white if dark_mode else asset.primary_text
        text = title
        font = dynamic_font_size(text, 1, 75, 1200, font)
        draw.text((95, 121), text, font=font, fill=fill, anchor="ls")

    fp = io.BytesIO()
    im.save(fp, "JPEG", quality=95, optimize=True)
    return fp


def small_card(
    material: Material,
    item_num: int | str,
    dark_mode: bool,
    locale: discord.Locale | str,
) -> Image.Image:
    im = Image.open(
        f"yelan/templates/todo/[{'light' if not dark_mode else 'dark'}] todo.png"
    )
    draw = ImageDraw.Draw(im)

    # material icon
    if material.icon:
        icon = get_cache(material.icon)
        icon = circular_crop(icon)
        icon = icon.resize((80, 80))
        im.paste(icon, (18, 30), icon)

    # material name
    font = get_font(locale, 40)
    fill = asset.primary_text if not dark_mode else asset.white

    num_font = get_font(locale, 36)
    num_length = num_font.getlength(str(item_num))
    num_left = 620 - num_length
    material_name = material.name
    long_name = 156 + font.getlength(material_name) >= num_left - 80
    while 156 + font.getlength(material_name) >= num_left - 80:
        material_name = material_name[:-1]

    draw.text(
        (156, 38), f"{material_name}{'...' if long_name else ''}", font=font, fill=fill
    )

    # number
    font = get_font(locale, 36, "Medium")
    fill = asset.primary_text if not dark_mode else asset.white
    text = str(item_num)
    draw.text((618 - font.getlength(text), 46), text, font=font, fill=fill)

    return im
