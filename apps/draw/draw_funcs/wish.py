import io

import discord
from PIL import Image, ImageDraw

import asset
from apps.draw.utility import (
    circular_crop,
    dynamic_font_size,
    get_cache,
    get_font,
    global_write,
)
from apps.text_map import text_map
from models import WishData


def overview(
    locale: discord.Locale | str,
    wish_data: WishData,
    pfp: str,
    user_name: str,
    dark_mode: bool,
) -> io.BytesIO:
    im = Image.open(
        f"yelan/templates/wish/[{'light' if not dark_mode else 'dark'}] Wish Overview.png"
    )
    draw = ImageDraw.Draw(im)
    fill = asset.primary_text if not dark_mode else asset.white
    locale = str(locale)

    # profile picture
    profile_pic = get_cache(pfp)
    profile_pic = circular_crop(profile_pic)
    profile_pic = profile_pic.resize((50, 50))
    im.paste(profile_pic, (30, 30), profile_pic)

    # user name
    global_write(draw, (93, 37), user_name, 22, fill, "Light")

    # banner name
    font = get_font(locale, 40, "Bold")
    draw.text((30, 100), wish_data.title, font=font, fill=fill)

    # primogem amount
    font = get_font(locale, 20, "Regular")
    primo_count = f"{wish_data.total_wishes*160:,}"
    draw.text(
        (69, 171),
        text_map.get(649, locale).format(a=primo_count),
        font=font,
        fill=fill,
    )

    # stats
    stats = {
        text_map.get(650, locale): wish_data.total_wishes,
        text_map.get(651, locale): wish_data.pity,
        text_map.get(652, locale): wish_data.four_star,
        text_map.get(653, locale): wish_data.five_star,
    }

    col = 0
    offset = (89, 273)
    for text, stat in stats.items():
        col += 1
        if col == 3:
            offset = (89, offset[1] + 118)
        font = get_font(locale, 20, "Light")
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
            str(stat), 30, 50, left_point - 30 - 20, get_font(locale, 50, "Medium")
        )
        draw.text((mid_point, offset[1]), str(stat), font=font, fill=fill, anchor="mm")
        offset = (offset[0] + 232, offset[1])

    # recent 5 star pulls
    font = get_font(locale, 30, "Bold")
    draw.text((30, 469), text_map.get(654, locale), font=font, fill=fill)

    offset = (55, 553)
    row = 0
    for item in wish_data.recents:
        row += 1
        if row == 5:
            offset = (offset[0] + 236, 553)
        elif row == 9:
            break

        # item icon
        if item.icon is not None:
            icon = get_cache(item.icon)
            icon = circular_crop(icon)
            icon = icon.resize((55, 55))
            im.paste(icon, offset, icon)

        # character name
        font = get_font(locale, 20, "Medium")
        fill = asset.primary_text if not dark_mode else asset.white
        character_name = item.name
        if font.getlength(character_name) >= 85:
            index = 1
            while font.getlength(character_name) >= 110:
                character_name = character_name[: len(character_name) - index] + "..."
                index += 1
        draw.text((offset[0] + 69, offset[1] + 5), character_name, font=font, fill=fill)

        # number of pulls
        font = get_font(locale, 16, "Regular")
        if 1 <= int(item.pull_num) <= 50:
            fill = "#5FA846" if not dark_mode else "#afff9c"
        elif 51 <= int(item.pull_num) <= 70:
            fill = "#4f87ff" if not dark_mode else "#8cb0ff"
        else:
            fill = "#CF5656" if not dark_mode else "#ff8c8c"
        draw.text(
            (offset[0] + 69, offset[1] + 28),
            f"{item.pull_num} {text_map.get(396, locale)}",
            font=font,
            fill=fill,
        )

        offset = (offset[0], offset[1] + 75)

    fp = io.BytesIO()
    im = im.convert("RGB")
    im.save(fp, "JPEG", quality=95, optimize=True)
    return fp
