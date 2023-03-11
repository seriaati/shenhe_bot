import io
from typing import List, Optional
from apps.text_map.utils import get_element_name
from apps.draw.utility import (
    circular_crop,
    draw_dynamic_background,
    dynamic_font_size,
    get_cache,
    get_font,
    shorten_text,
)
from apps.genshin.custom_model import DynamicBackgroundInput, TopPadding
from apps.text_map.text_map_app import text_map

import discord
import genshin
from PIL import Image, ImageDraw

import asset
from data.game.elements import get_element_color


def card(
    all_characters: List[genshin.models.Character],
    dark_mode: bool,
    locale: str | discord.Locale,
    element: str,
    custom_title: Optional[str] = None,
) -> io.BytesIO:
    if element == "All":
        characters = all_characters
        element_name = text_map.get(701, locale)
    else:
        characters = [c for c in all_characters if c.element == element]
        element_name = get_element_name(element, locale)

    # create the background based on the number of characters
    im, max_card_num = draw_dynamic_background(
        DynamicBackgroundInput(
            top_padding=TopPadding(with_title=190, without_title=90),
            left_padding=95,
            right_padding=95,
            bottom_padding=90,
            card_num=len(characters),
            background_color=get_element_color(element)
            if not dark_mode
            else asset.dark_theme_background,
            card_height=140,
            card_width=645,
            card_x_padding=60,
            card_y_padding=45,
        )
    )
    draw = ImageDraw.Draw(im)

    # title
    font = get_font(locale, 75, "Bold")
    fill = asset.white if dark_mode else asset.primary_text
    text = custom_title or (
        text_map.get(19, locale)
        if element == "All"
        else text_map.get(52, locale).format(element=element_name)
    )
    font = dynamic_font_size(text, 1, 75, 645, font)
    draw.text((95, 40), text, font=font, fill=fill)

    for index, character in enumerate(characters):
        # draw the card
        card = s_card(character, dark_mode, locale)
        # paste the card
        x = 95 + (644 + 60) * (index // max_card_num)
        y = 190 + (140 + 45) * (index % max_card_num)
        im.paste(card, (x, y), card)

    fp = io.BytesIO()
    im.save(fp, "JPEG", quality=95, optimize=True)
    return fp


def s_card(
    character: genshin.models.Character,
    dark_mode: bool,
    locale: str | discord.Locale,
) -> Image.Image:
    # card
    im = Image.open(
        f"yelan/templates/character/[{'light' if not dark_mode else 'dark'}] card.png"
    )
    draw = ImageDraw.Draw(im)

    # character icon
    icon = get_cache(character.icon)
    icon = circular_crop(icon)
    icon = icon.resize((95, 95))
    im.paste(icon, (17, 23), icon)

    # character name
    font = get_font(locale, 40, "Bold")
    fill = asset.primary_text if not dark_mode else asset.white
    text = shorten_text(character.name, 321, font)
    draw.text((127, 23), text, font=font, fill=fill)

    # constellation and refinement
    font = get_font(locale, 25)
    fill = asset.secondary_text if not dark_mode else asset.white
    draw.text(
        (127, 77),
        f"C{character.constellation}R{character.weapon.refinement} {text_map.get(578, locale)} {character.friendship}",
        font=font,
        fill=fill,
    )

    # level
    font = get_font(locale, 36, "Medium")
    fill = asset.primary_text if not dark_mode else asset.white
    text = f"Lv. {character.level}"
    draw.text((620 - font.getlength(text), 46), text, font=font, fill=fill)

    return im
