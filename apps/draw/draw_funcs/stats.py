import io
from typing import List

import discord
import enkanetwork
import genshin
from PIL import Image, ImageDraw

import asset
from apps.draw.utility import circular_crop, get_cache, get_font


def stats_card(
    user_stats: genshin.models.Stats,
    namecard: enkanetwork.Namecard,
    pfp: discord.Asset,
    character_num: int,
    dark_mode: bool,
) -> io.BytesIO:
    stats = {
        "active_days": user_stats.days_active,
        "characters": f"{user_stats.characters}/{character_num}",
        "achievements": user_stats.achievements,
        "abyss": user_stats.spiral_abyss,
        "anemo": f"{user_stats.anemoculi}/66",
        "geo": f"{user_stats.geoculi}/131",
        "electro": f"{user_stats.electroculi}/181",
        "dendro": f"{user_stats.dendroculi}/180",
        "normal": user_stats.common_chests,
        "rare": user_stats.exquisite_chests,
        "gold": user_stats.precious_chests,
        "lux": user_stats.luxurious_chests,
    }
    mode_txt = "dark" if dark_mode else "light"
    stat_card = Image.open(f"yelan/templates/stats/[{mode_txt}] Stat Card Template.png")
    name_card = get_cache(namecard.banner.url)
    w, h = name_card.size
    factor = 2.56
    name_card = name_card.resize((int(w * factor), int(h * factor)))
    w, h = name_card.size
    name_card = name_card.crop((0, 190, w, h - 190))
    stat_card.paste(name_card, (112, 96))

    profile_pic = get_cache(pfp.url)
    profile_pic = profile_pic.resize((412, 412))
    profile_pic = circular_crop(profile_pic)
    stat_card.paste(profile_pic, (979, 462), profile_pic)
    draw = ImageDraw.Draw(stat_card)
    font = get_font("en-US", 90)
    fill = asset.white if dark_mode else asset.primary_text
    x, y = 415, 1360
    count = 1
    for text in list(stats.values()):
        draw.text((x, y), str(text), fill, font, anchor="mm")
        if count == 4:
            x = 415
            y += 625
        elif count == 8:
            x = 415
            y += 650
        else:
            x += 514
        count += 1

    stat_card = stat_card.convert("RGB")
    fp = io.BytesIO()
    stat_card.save(fp, "JPEG", optimize=True, quality=40)
    return fp


def area_card(explorations: List[genshin.models.Exploration], dark_mode: bool):
    mode_txt = "dark" if dark_mode else "light"
    card = Image.open(f"yelan/templates/area/[{mode_txt}] Area Card Template.png")
    card_draw = ImageDraw.Draw(card)
    fill = asset.white if dark_mode else asset.primary_text
    font = get_font("en-US", 90)
    pos = 481, 175
    for index in range(8):
        exploration = [e for e in explorations if e.id == index + 1]
        if not exploration:
            pos = pos[0], pos[1] + 350
            continue
        exploration = exploration[0]
        percentage = exploration.explored
        file_name = f"light_{exploration.id}"
        try:
            im = Image.open(f"yelan/templates/area/{file_name}.png")
        except FileNotFoundError:
            continue
        mask = Image.new("L", im.size, 0)
        empty = Image.new("RGBA", im.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle(
            (0, 0, int(percentage / 100 * im.width), im.height),
            fill=asset.white,
            radius=20,
        )
        card_draw.text(
            (pos[0] + 180 + int(percentage / 100 * im.width), pos[1] + im.height // 2),
            f"{percentage}%",
            fill=fill,
            font=font,
            anchor="mm",
        )
        im = Image.composite(im, empty, mask)
        card.paste(im, pos, im)
        pos = pos[0], pos[1] + 350
    fp = io.BytesIO()
    card = card.convert("RGB")
    card.save(fp, "JPEG", optimize=True)
    return fp
