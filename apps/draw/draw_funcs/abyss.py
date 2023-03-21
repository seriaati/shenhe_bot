import io
from typing import List

import discord
import genshin
from PIL import Image, ImageDraw

import asset
from apps.draw.draw_funcs import leaderboard
from apps.draw.utility import (
    draw_dynamic_background,
    dynamic_font_size,
    get_cache,
    get_font,
)
from apps.text_map import text_map
from models import (
    CharacterUsageResult,
    DynamicBackgroundInput,
    RunLeaderboardUser,
    SingleStrikeLeaderboardUser,
    TopPadding,
    UsageCharacter,
)


def one_page(
    user: genshin.models.PartialGenshinUserStats,
    abyss: genshin.models.SpiralAbyss,
    locale: discord.Locale | str,
    dark_mode: bool,
    user_characters: List[genshin.models.Character],
) -> io.BytesIO:
    app_mode = "dark" if dark_mode else "light"
    font = get_font(locale, 60)
    fill = asset.white if dark_mode else asset.primary_text
    im = Image.open(f"yelan/templates/abyss/[{app_mode}] Abyss One Page.png")
    draw = ImageDraw.Draw(im)

    # write the title
    draw.text((595, 134), text_map.get(85, locale), fill=fill, font=font, anchor="mm")
    # write the four basic stats
    draw.text((1361, 134), str(abyss.total_stars), fill=fill, font=font, anchor="mm")
    draw.text((1861, 134), str(abyss.max_floor), fill=fill, font=font, anchor="mm")
    draw.text(
        (2361, 134),
        f"{abyss.total_wins}/{abyss.total_battles}",
        fill=fill,
        font=font,
        anchor="mm",
    )
    draw.text((2861, 134), str(user.info.level), fill=fill, font=font, anchor="mm")

    # most played characters
    draw.text((528, 326), text_map.get(613, locale), fill=fill, font=font, anchor="mm")
    most_played = abyss.ranks.most_played[:4]
    offset = (75, 453)
    for character in most_played:
        icon = get_cache(character.icon)
        icon = icon.resize((220, 220))
        icon = icon.crop((28, 0, 192, 220))
        im.paste(icon, offset, icon)
        offset = (offset[0] + 250, offset[1])

    # other ranks
    character_rank = {
        text_map.get(83, locale): abyss.ranks.most_bursts_used[0],
        text_map.get(84, locale): abyss.ranks.most_skills_used[0],
        text_map.get(80, locale): abyss.ranks.strongest_strike[0],
        text_map.get(81, locale): abyss.ranks.most_kills[0],
        text_map.get(82, locale): abyss.ranks.most_damage_taken[0],
    }
    character_level = {}
    for floor in abyss.floors:
        for chamber in floor.chambers:
            for battle in chamber.battles:
                for character in battle.characters:
                    character_level[character.id] = character.level
    offset = (1387, 326)
    icon_offset = (1772, 284)
    count = 1
    font = get_font(locale, 45)
    value_font = get_font(locale, 88)
    level_font = get_font(locale, 40)
    for text, character in character_rank.items():
        if count == 3:
            offset = (375, 823)
            icon_offset = (offset[0] + 386, offset[1] - 34)
        draw.text(offset, text=text, fill=fill, font=font, anchor="mm")
        text_offset = (offset[0], offset[1] + 236)
        draw.text(
            text_offset,
            text=str(character.value),
            fill=fill,
            font=value_font,
            anchor="mm",
        )
        if count >= 3:
            level_offset = (icon_offset[0] + 108, icon_offset[1] + 374)
        else:
            level_offset = (icon_offset[0] + 108, icon_offset[1] + 382)
        if character.id in character_level:
            draw.text(
                level_offset,
                text=f"Lv. {character_level[character.id]}",
                fill=fill,
                font=level_font,
                anchor="mm",
            )
        icon = get_cache(character.icon)
        icon = icon.resize((280, 280))
        icon = icon.crop((33, 0, 247, 280))
        im.paste(icon, icon_offset, icon)
        offset = (offset[0] + 1009, offset[1])
        icon_offset = (icon_offset[0] + 1008, icon_offset[1])
        count += 1

    # abyss floors
    level_font = get_font(locale, 20)
    split_floors = [abyss.floors[:2], abyss.floors[2:]]
    offset = (104, 1313)
    for index, floors in enumerate(split_floors):
        if index == 1:
            offset = (104, 2133)
        for floor in floors:
            for chamber in floor.chambers:
                for battle in chamber.battles:
                    characters = battle.characters
                    for index in range(4):
                        try:
                            character = characters[index]
                            icon = get_cache(character.icon)
                            icon = icon.resize((129, 129))
                            icon = icon.crop((17, 0, 112, 129))
                            im.paste(icon, offset, icon)
                            draw.text(
                                (offset[0] + 48, offset[1] + 170),
                                text=f"Lv. {character.level}",
                                fill=fill,
                                font=level_font,
                                anchor="mm",
                            )
                            u_c = next(
                                (x for x in user_characters if x.id == character.id),
                                None,
                            )
                            if u_c is not None:
                                draw.text(
                                    (offset[0] - 9, offset[1] - 9),
                                    text=f"C{u_c.constellation}",
                                    fill=fill,
                                    font=level_font,
                                    anchor="mm",
                                )
                        except IndexError:
                            pass
                        offset = (offset[0] + 160, offset[1])
                    offset = (offset[0] + 149, offset[1])
                offset = (offset[0] - 1578, offset[1] + 244)
            offset = (offset[0] + 1503, offset[1] - 732)

    # draw stars
    font = get_font(locale, 30)
    stars = {
        1: f"yelan/templates/abyss/[{app_mode}] One Star.png",
        2: f"yelan/templates/abyss/[{app_mode}] Two Star.png",
        3: f"yelan/templates/abyss/[{app_mode}] Three Star.png",
    }
    star_offset = {
        1: (-13, 25),
        2: (-23, 25),
        3: (-34, 25),
    }
    offset = (786, 1377)

    # chamber and floor texts
    for index, floors in enumerate(split_floors):
        if index == 1:
            offset = (786, 2198)
        for floor in floors:
            for chamber in floor.chambers:
                text = f"{floor.floor}-{chamber.chamber}"
                draw.text(offset, text=text, font=font, fill=fill, anchor="mm")
                if chamber.stars != 0:
                    star = Image.open(stars[chamber.stars])
                    star = star.resize((star.width // 2, star.height // 2))
                    im.paste(
                        star,
                        (
                            offset[0] + star_offset[chamber.stars][0],
                            offset[1] + star_offset[chamber.stars][1],
                        ),
                        star,
                    )
                offset = (offset[0], offset[1] + 244)
            offset = (offset[0] + 1503, offset[1] - 732)

    im = im.convert("RGB")
    fp = io.BytesIO()
    im.save(fp, "JPEG", quality=95, optimize=True)
    return fp


def strike_leaderboard(
    locale: discord.Locale | str,
    dark_mode: bool,
    users: List[SingleStrikeLeaderboardUser],
    current_uid: int,
) -> io.BytesIO:
    """Draw the "Strongest Single Strike" leaderboard."""
    im = leaderboard.board(
        dark_mode, users, current_uid, 80, [89, 198, 199, 201, 610], locale
    )
    fp = io.BytesIO()
    im = im.convert("RGB")
    im.save(fp, format="JPEG", quality=95, optimize=True)
    return fp


def run_leaderboard(
    locale: discord.Locale | str,
    dark_mode: bool,
    users: List[RunLeaderboardUser],
    current_uid: int,
) -> io.BytesIO:
    """Draw the "Runs Taken to Full Clear" leaderboard."""
    im = leaderboard.board(
        dark_mode, users, current_uid, 160, [89, 198, 186, 293, 610], locale
    )
    fp = io.BytesIO()
    im = im.convert("RGB")
    im.save(fp, format="JPEG", quality=95, optimize=True)
    return fp


def overview(
    locale: discord.Locale | str,
    dark_mode: bool,
    abyss: genshin.models.SpiralAbyss,
    user: genshin.models.PartialGenshinUserStats,
) -> io.BytesIO:
    app_mode = "light" if not dark_mode else "dark"
    card: Image.Image = Image.open(
        f"yelan/templates/abyss/[{app_mode}] Abyss Overview.png"
    )
    draw = ImageDraw.Draw(card)

    font = get_font(locale, 90)
    fill = asset.white if app_mode == "dark" else asset.primary_text
    text = text_map.get(85, locale)
    offset = (950, 230)
    draw.text(offset, text=text, fill=fill, font=font, anchor="mm")
    text = str(abyss.total_stars)
    offset = (offset[0] + 1290, offset[1])
    draw.text(offset, text=text, fill=fill, font=font, anchor="mm")
    text = str(abyss.max_floor)
    offset = (offset[0] + 830, offset[1])
    draw.text(offset, text=text, fill=fill, font=font, anchor="mm")
    text = f"{abyss.total_wins}/{abyss.total_battles}"
    offset = (offset[0] + 840, offset[1])
    draw.text(offset, text=text, fill=fill, font=font, anchor="mm")
    text = f"AR {user.info.level}"
    offset = (offset[0] + 830, offset[1])
    draw.text(offset, text=text, fill=fill, font=font, anchor="mm")
    offset = (950 - 100, 220 + 320)
    text = text_map.get(613, locale)
    draw.text(offset, text=text, fill=fill, font=font, anchor="mm")
    most_played = abyss.ranks.most_played[:4]
    offset = (120, 760)
    for character in most_played:
        icon = get_cache(character.icon)
        icon = icon.resize((360, 360))
        icon = icon.crop((45, 0, 320, 360))
        card.paste(icon, offset, icon)
        offset = (offset[0] + 415, offset[1])
    character_rank = {
        text_map.get(83, locale): abyss.ranks.most_bursts_used[0],
        text_map.get(84, locale): abyss.ranks.most_skills_used[0],
        text_map.get(80, locale): abyss.ranks.strongest_strike[0],
        text_map.get(81, locale): abyss.ranks.most_kills[0],
        text_map.get(82, locale): abyss.ranks.most_damage_taken[0],
    }
    character_level = {}
    for floor in abyss.floors:
        for chamber in floor.chambers:
            for battle in chamber.battles:
                for character in battle.characters:
                    character_level[character.id] = character.level
    offset = (2300, 540)
    icon_offset = (2950, 490)
    count = 1
    font = get_font(locale, 75)
    value_font = get_font(locale, 128)
    level_font = get_font(locale, 75)
    for text, character in character_rank.items():
        if count == 3:
            offset = (610, 1370)
            icon_offset = (offset[0] + 660, offset[1] - 50)
        draw.text(offset, text=text, fill=fill, font=font, anchor="mm")
        text_offset = (offset[0], offset[1] + 380)
        draw.text(
            text_offset,
            text=str(character.value),
            fill=fill,
            font=value_font,
            anchor="mm",
        )
        level_offset = (icon_offset[0] + 160, icon_offset[1] + 610)
        if character.id in character_level:
            draw.text(
                level_offset,
                text=f"Lv. {character_level[character.id]}",
                fill=fill,
                font=level_font,
                anchor="mm",
            )
        icon = get_cache(character.icon)
        icon = icon.resize((453, 453))
        icon = icon.crop((65, 0, 400, 453))
        card.paste(icon, icon_offset, icon)
        offset = (offset[0] + 1690, offset[1])
        if count == 3:
            icon_offset = (icon_offset[0] + 1680, icon_offset[1])
        else:
            icon_offset = (icon_offset[0] + 1670, icon_offset[1])
        count += 1

    card = card.convert("RGB")
    fp = io.BytesIO()
    card.save(fp, "JPEG", optimize=True, quality=40)
    return fp


def floor(
    dark_mode: bool,
    floor: genshin.models.Floor,
    characters: List[genshin.models.Character],
) -> io.BytesIO:
    app_mode = "dark" if dark_mode else "light"
    im: Image.Image = Image.open(f"yelan/templates/abyss/[{app_mode}] Abyss Floor.png")
    fill = asset.white if dark_mode else asset.primary_text
    font = get_font("en-US", 28)
    floor_font = get_font("en-US", 45)
    draw = ImageDraw.Draw(im)
    offset = (154, 101)
    text_offset = (240, 383)
    floor_offset = (1287, 197)
    stars = {
        1: f"yelan/templates/abyss/[{app_mode}] One Star.png",
        2: f"yelan/templates/abyss/[{app_mode}] Two Star.png",
        3: f"yelan/templates/abyss/[{app_mode}] Three Star.png",
    }
    star_x_offset = {1: 1267, 2: 1243, 3: 1218}
    star_offset = (0, 231)
    for chamber in floor.chambers:
        if chamber.stars != 0:
            star_offset = (star_x_offset.get(chamber.stars, 154), star_offset[1])
            star = Image.open(stars.get(chamber.stars, stars[1]))
            im.paste(star, star_offset, star)
        draw.text(
            floor_offset,
            f"{floor.floor}-{chamber.chamber}",
            fill=fill,
            font=floor_font,
            anchor="mm",
        )
        for battle in chamber.battles:
            cs = battle.characters
            for index in range(4):
                try:
                    c = cs[index]
                    g_c = next((x for x in characters if x.id == c.id), None)
                    if g_c is not None:
                        draw.text(
                            (text_offset[0] - 89, text_offset[1] - 297),
                            f"C{g_c.constellation}",
                            fill=fill,
                            font=font,
                            anchor="mm",
                        )
                    icon = get_cache(c.icon)
                    icon = icon.resize((210, 210))
                    icon = icon.crop((20, 0, 190, 210))
                    draw.text(
                        text_offset, f"Lv. {c.level}", fill=fill, font=font, anchor="mm"
                    )
                    im.paste(icon, offset, icon)
                except IndexError:
                    pass
                offset = (offset[0] + 257, offset[1])
                text_offset = (text_offset[0] + 257, text_offset[1])
            offset = (offset[0] + 296, offset[1])
            text_offset = (text_offset[0] + 296, text_offset[1])
        star_offset = (star_offset[0], star_offset[1] + 484)
        offset = (154, offset[1] + 484)
        text_offset = (240, text_offset[1] + 484)
        floor_offset = (1287, floor_offset[1] + 484)
    im = im.convert("RGB")
    fp = io.BytesIO()
    im.save(fp, "JPEG", optimize=True, quality=40)
    return fp


def character_usage(
    uc_list: List[UsageCharacter],
    dark_mode: bool,
    locale: discord.Locale | str,
) -> CharacterUsageResult:
    total = sum(x.usage_num for x in uc_list)
    uc_list = sorted(uc_list, key=lambda x: x.usage_num, reverse=True)
    im, max_card_num = draw_dynamic_background(
        DynamicBackgroundInput(
            top_padding=TopPadding(with_title=190, without_title=90),
            left_padding=95,
            right_padding=95,
            bottom_padding=90,
            card_num=len(uc_list),
            background_color=asset.light_theme_background
            if not dark_mode
            else asset.dark_theme_background,
            card_height=140,
            card_width=645,
            card_x_padding=60,
            card_y_padding=45,
            max_card_num=11,
        )
    )
    draw = ImageDraw.Draw(im)

    # title
    font = get_font(locale, 75, "Bold")
    fill = asset.white if dark_mode else asset.primary_text
    text = text_map.get(617, locale)
    font = dynamic_font_size(text, 1, 75, 645, font)
    draw.text((95, 40), text, font=font, fill=fill)

    # draw cards
    for index, uc in enumerate(uc_list):
        card = leaderboard.c_usage_card(
            uc.character,
            uc.usage_num,
            uc.usage_num / total * 100,
            dark_mode,
            locale,
        )
        x = 95 + (644 + 60) * (index // max_card_num)
        y = 190 + (140 + 45) * (index % max_card_num)
        im.paste(card, (x, y), card)

    first_character = uc_list[0]

    fp = io.BytesIO()
    im.save(fp, "JPEG", quality=95, optimize=True)
    return CharacterUsageResult(
        fp=fp,
        first_character=first_character.character,
        uses=first_character.usage_num,
        percentage=first_character.usage_num / total * 100,
    )
