from apps.draw.utility import calculate_time
import discord
import genshin
from typing import List
import io
from PIL import Image, ImageDraw

@calculate_time
def draw_abyss_one_page(
    user: genshin.models.PartialGenshinUserStats,
    abyss: genshin.models.SpiralAbyss,
    locale: discord.Locale | str,
    dark_mode: bool,
    user_characters: List[genshin.models.Character],
) -> io.BytesIO:
    app_mode = "dark" if dark_mode else "light"
    font_family = get_font(locale)
    fill = asset.white if dark_mode else "#333"
    im = Image.open(f"yelan/templates/abyss/[{app_mode}] Abyss One Page.png")
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(font_family, 60)

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
        bytes_obj = await access_character_cache(character, session)
        icon = Image.open(bytes_obj)
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
    font = ImageFont.truetype(font_family, 45)
    value_font = ImageFont.truetype(font_family, 88)
    level_font = ImageFont.truetype(font_family, 40)
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
        bytes_obj = await access_character_cache(character, session)
        icon = Image.open(bytes_obj)
        icon = icon.resize((280, 280))
        icon = icon.crop((33, 0, 247, 280))
        im.paste(icon, icon_offset, icon)
        offset = (offset[0] + 1009, offset[1])
        icon_offset = (icon_offset[0] + 1008, icon_offset[1])
        count += 1

    # abyss floors
    level_font = ImageFont.truetype(font_family, 20)
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
                            bytes_obj = await access_character_cache(character, session)
                            icon = Image.open(bytes_obj)
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

    # chamber and floor text
    # draw stars
    font = ImageFont.truetype(font_family, 30)
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
    for index, floors in enumerate(split_floors):
        if index == 1:
            offset = (786, 2198)
        for floor in floors:
            for chamber in floor.chambers:
                text = f"{floor.floor}-{chamber.chamber}"
                draw.text(offset, text=text, font=font, fill=fill, anchor="mm")
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
    fp = BytesIO()
    im.save(fp, "JPEG", quality=95, optimize=True)
    return fp