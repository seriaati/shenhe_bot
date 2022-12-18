from io import BytesIO
from typing import Dict, List, Tuple

from discord import Locale
from genshin.models import LineupPreview
from PIL import Image, ImageDraw

import asset
from apps.draw.utility import get_cache, get_font
from apps.text_map.text_map_app import text_map


def card(
    dark_mode: bool, locale: str | Locale, lineup: LineupPreview, character_id: int
) -> BytesIO:
    # rarity colors
    if dark_mode:
        rarity_colors = {
            1: "#343434",
            2: "#2d2e38",
            3: "#2c332e",
            4: "#333138",
            5: "#38332d",
        }
    else:
        rarity_colors = {
            1: "#d7d7d7",
            2: "#8BA8F3",
            3: "#909BFF",
            4: "#CAB7FF",
            5: "#FFCA8C",
        }

    fill = asset.white if dark_mode else asset.primary_text
    pill_color = "#373737" if dark_mode else "#E8E8E8"

    lineup_characters = lineup.characters[0]
    for characters in lineup.characters:
        for character in characters:
            if character.id == character_id:
                lineup_characters = characters
                break

    lineup_characters = list(lineup_characters)
    im: Image.Image = Image.open(
        f"yelan/templates/lineup/[{'dark' if dark_mode else 'light'}] lineup.jpg"
    )
    draw = ImageDraw.Draw(im)

    offset = (78, 57)
    for character in lineup_characters:
        # pc icon
        pc_icon = get_cache(character.pc_icon)
        pc_icon = pc_icon.resize((383, 383))
        im.paste(pc_icon, offset, pc_icon)

        # weapon
        font = get_font(locale, 30)
        draw.text(
            (offset[0] + 438, offset[1] + 94),
            text_map.get(33, locale),
            font=font,
            fill=fill,
        )
        # rarity box
        draw.rounded_rectangle(
            (
                offset[0] + 438,
                offset[1] + 152,
                offset[0] + 438 + 188,
                offset[1] + 152 + 188,
            ),
            10,
            fill=rarity_colors[character.weapon.rarity],
        )
        # weapon icon
        weapon_icon = get_cache(character.weapon.icon)
        weapon_icon = weapon_icon.resize((169, 169))
        im.paste(weapon_icon, (offset[0] + 448, offset[1] + 161), weapon_icon)

        # artifacts
        draw.text(
            (offset[0] + 700, offset[1] + 94),
            text_map.get(37, locale),
            font=font,
            fill=fill,
        )
        # rarity box
        draw.rounded_rectangle(
            (
                offset[0] + 700,
                offset[1] + 152,
                offset[0] + 700 + 188,
                offset[1] + 152 + 188,
            ),
            10,
            fill=rarity_colors[character.artifacts[0].rarity],
        )
        if len(character.artifacts) == 2:
            artifact_icon_1 = get_cache(character.artifacts[0].icon)
            artifact_icon_1 = artifact_icon_1.resize((105, 105))
            im.paste(
                artifact_icon_1, (offset[0] + 700, offset[1] + 152), artifact_icon_1
            )

            artifact_icon_2 = get_cache(character.artifacts[1].icon)
            artifact_icon_2 = artifact_icon_2.resize((105, 105))
            im.paste(
                artifact_icon_2, (offset[0] + 784, offset[1] + 234), artifact_icon_2
            )
        else:
            aritfact_icon = get_cache(character.artifacts[0].icon)
            aritfact_icon = aritfact_icon.resize((169, 169))
            im.paste(aritfact_icon, (offset[0] + 710, offset[1] + 161), aritfact_icon)

        # artifact substats
        font = get_font(locale, 24)
        substat_string = " > ".join(
            [s.name.replace("Percentage", "%") for s in character.secondary_attributes]
        )
        texts = substat_string.split(" ")
        cursor = 0
        stat_offset = (1067, offset[1] + 239)
        text_list: List[Dict[str, Tuple[int, int]]] = []
        two_rows = False
        for text in texts:
            if cursor + font.getlength(text) > 393:
                draw.rounded_rectangle(
                    (
                        1050,
                        stat_offset[1],
                        1050 + cursor + 34,
                        stat_offset[1] + 41,
                    ),
                    50,
                    fill=pill_color,
                )
                stat_offset = (1067, stat_offset[1] + 62)
                two_rows = True
                cursor = 0
            text_list.append({f"{text} ": (stat_offset[0], stat_offset[1] + 3)})
            stat_offset = (
                stat_offset[0] + font.getlength(text + " "),
                stat_offset[1],
            )
            cursor += font.getlength(text + " ")
        y_offset = 0 if two_rows else 53
        draw.rounded_rectangle(
            (
                1050,
                stat_offset[1] + y_offset,
                1050 + cursor + 34,
                stat_offset[1] + 41 + y_offset,
            ),
            50,
            fill=pill_color,
        )
        for text in text_list:
            text_offset = list(text.values())[0]
            draw.text(
                (text_offset[0], text_offset[1] + y_offset),
                list(text.keys())[0],
                font=font,
                fill=fill,
            )

        # aritfact stats
        font = get_font(locale, 24)
        row_offset = 0 if two_rows else 53
        stat_offset = (offset[0] + 972, offset[1] + 53 + row_offset)
        slot_dict = {
            0: "circlet",
            1: "goblet",
            2: "sand",
        }
        for index, stat in enumerate(character.artifact_attributes):
            draw.rounded_rectangle(
                (
                    stat_offset[0],
                    stat_offset[1],
                    stat_offset[0] + font.getlength(stat.name) + 65,
                    stat_offset[1] + 41,
                ),
                50,
                fill=pill_color,
            )
            slot_icon = Image.open(
                f"yelan/templates/lineup/[{'dark' if dark_mode else 'light'}] {slot_dict[index]}.png"
            )
            im.paste(slot_icon, (stat_offset[0] + 10, stat_offset[1] + 5), slot_icon)
            draw.text(
                (stat_offset[0] + 51, stat_offset[1] + 3),
                stat.name,
                font=font,
                fill=fill,
            )

            stat_offset = (stat_offset[0], stat_offset[1] + 62)

        offset = (offset[0], offset[1] + 437)

    fp = BytesIO()
    im = im.convert("RGB")
    im.save(fp, format="JPEG", quality=95, optimize=True)
    return fp
