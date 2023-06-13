import io
from typing import List

import discord
from PIL import Image, ImageDraw

import dev.asset as asset
from apps.text_map import text_map
from apps.wish.models import RecentWish, WishData
from dev.enum import CardType
from utils import circular_crop, dynamic_font_size, get_cache, get_font


def wish_overview(
    lang: discord.Locale | str,
    wish_data: WishData,
    dark_mode: bool,
) -> io.BytesIO:
    im: Image.Image = Image.open(
        f"yelan/templates/wish/[{'light' if not dark_mode else 'dark'}] Wish Overview.png"
    )
    im = im.resize((im.width // 3, im.height // 3))
    draw = ImageDraw.Draw(im)
    fill = asset.primary_text if not dark_mode else asset.white
    lang = str(lang)

    # banner name
    font = get_font(lang, 40, "Bold")
    draw.text((30, 100), wish_data.title, font=font, fill=fill)

    # primogem amount
    font = get_font(lang, 20, "Regular")
    primo_count = f"{wish_data.total_wishes*160:,}"
    draw.text(
        (69, 171),
        text_map.get(649, lang).format(a=primo_count),
        font=font,
        fill=fill,
    )

    # stats
    stats = {
        text_map.get(650, lang): wish_data.total_wishes,
        text_map.get(651, lang): wish_data.pity,
        text_map.get(652, lang): wish_data.four_star,
        text_map.get(653, lang): wish_data.five_star,
    }

    col = 0
    offset = (89, 273)
    for text, stat in stats.items():
        col += 1
        if col == 3:
            offset = (89, offset[1] + 118)
        font = get_font(lang, 20, "Light")
        text = text.upper().split(" ")
        draw.text(
            (offset[0] + 137 - font.getlength(text[0]), offset[1] - 27),
            text[0],
            font=font,
            fill=fill,
        )
        draw.text(
            (offset[0] + 137 - font.getlength(text[1]), offset[1]),
            text[1],
            font=font,
            fill=fill,
        )
        bigger = font.getlength(text[0])
        if font.getlength(text[1]) > bigger:
            bigger = font.getlength(text[1])
        left_point = offset[0] + 137 - bigger
        adder = 262 if col in [2, 4] else 30
        mid_point = (adder + left_point) // 2
        font = dynamic_font_size(
            str(stat), 30, 50, left_point - 30 - 20, get_font(lang, 50, "Medium")
        )
        draw.text((mid_point, offset[1]), str(stat), font=font, fill=fill, anchor="mm")
        offset = (offset[0] + 232, offset[1])

    # recent 5 star pulls
    font = get_font(lang, 30, "Bold")
    draw.text((30, 469), text_map.get(654, lang), font=font, fill=fill)

    draw_wish_recents(
        lang, wish_data.recents[:8], dark_mode, im, draw, CardType.OVERVIEW
    )

    fp = io.BytesIO()
    im = im.resize((im.width * 3, im.height * 3))
    im = im.crop((0, 240, im.width, im.height))
    im.save(fp, "PNG", optimize=True)
    return fp


def draw_wish_recents_card(
    lang: discord.Locale | str,
    recents: List[RecentWish],
    dark_mode: bool,
) -> io.BytesIO:
    im: Image.Image = Image.open(
        f"yelan/templates/wish/[{'light' if not dark_mode else 'dark'}] Wish Overview p2.png"
    )
    im = im.resize((im.width // 3, im.height // 3))
    draw = ImageDraw.Draw(im)

    draw_wish_recents(lang, recents, dark_mode, im, draw, CardType.RECENTS)

    im = im.resize((im.width * 3, im.height * 3))
    fp = io.BytesIO()
    im.save(fp, "PNG", optimize=True)
    return fp


def draw_wish_recents(
    lang: discord.Locale | str,
    recents: List[RecentWish],
    dark_mode: bool,
    im: Image.Image,
    draw: ImageDraw.ImageDraw,
    card_type: CardType,
) -> None:
    row = 0
    if card_type is CardType.OVERVIEW:
        offset = (55, 553)
        original_y = 553
    elif card_type is CardType.RECENTS:
        offset = (55, 50)
        original_y = 50
    for item in recents:
        row += 1
        if (card_type is CardType.OVERVIEW and row == 5) or (
            card_type is CardType.RECENTS and row == 12
        ):
            offset = (offset[0] + 236, original_y)

        # item icon
        if item.icon is not None:
            icon = get_cache(item.icon)
            icon = circular_crop(icon)
            icon = icon.resize((55, 55))
            im.paste(icon, offset, icon)

        # character name
        font = get_font(lang, 20, "Medium")
        fill = asset.primary_text if not dark_mode else asset.white
        character_name = item.name
        if font.getlength(character_name) >= 85:
            index = 1
            while font.getlength(character_name) >= 110:
                character_name = character_name[: len(character_name) - index] + "..."
                index += 1
        draw.text((offset[0] + 69, offset[1] + 5), character_name, font=font, fill=fill)

        # number of pulls
        font = get_font(lang, 16, "Regular")
        if 1 <= int(item.pull_num) <= 50:
            fill = "#5FA846" if not dark_mode else "#afff9c"
        elif 51 <= int(item.pull_num) <= 70:
            fill = "#4f87ff" if not dark_mode else "#8cb0ff"
        else:
            fill = "#CF5656" if not dark_mode else "#ff8c8c"
        draw.text(
            (offset[0] + 69, offset[1] + 28),
            text_map.get(396, lang).format(pull=item.pull_num),
            font=font,
            fill=fill,
        )

        offset = (offset[0], offset[1] + 75)
