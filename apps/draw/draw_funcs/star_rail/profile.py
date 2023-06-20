import io
import random
from typing import Any, Dict, Optional

import discord.utils as dutils
import mihomo
from PIL import Image, ImageDraw

import utils.draw as utils
from apps.text_map import text_map
from dev.asset import trailblazer_ids
from utils.general import open_json

tree_info = open_json("HSRMaps/maps/en/avatartree.json")


def draw_profile_card_v1(
    character: mihomo.models.Character,
    lang: str,
    dark_mode: bool,
    image_url: str,
    card_data: Dict[str, Any],
) -> io.BytesIO:
    dark_mode = False  # TODO: Add dark mode colors
    if dark_mode:
        colors = card_data["colors"]["dark"]
        white = "#0D0D0D"
    else:
        colors = card_data["colors"]["light"]
        white = "#FFFFFF"
    primary = colors["primary"]
    bk = colors["bk"]
    bk_light = colors["bk_light"]
    dark = colors["dark"]
    image_url = random.choice(card_data["arts"])

    im = Image.new("RGBA", (2244, 1297), bk)
    draw = ImageDraw.Draw(im)

    # character image
    character_im = utils.get_cache(image_url)
    character_im = utils.resize_and_crop_image(
        character_im,
        target_width=640,
        target_height=1138,
        radius=0,
    )
    # if dark_mode:
    # mask = Image.open("yelan/star_rail/profile/1/img/dark_mask.png")
    # else:
    mask = Image.open("yelan/star_rail/profile/1/img/mask.png")
    im.paste(character_im, (0, 159), mask)

    # base card
    if dark_mode:
        card = Image.open("yelan/star_rail/profile/1/base/dark_card.png")
    else:
        card = Image.open("yelan/star_rail/profile/1/base/light_card.png")
    width = 1540
    height = 1260
    shodow_width = card.width - width
    shodow_height = card.height - height
    real_pos = (704, 37)
    pos = (real_pos[0] - shodow_width, real_pos[1] - shodow_height)
    im.paste(card, pos, card)

    # character name
    font = utils.get_font(lang, 128, "Bold")
    name = character.name.upper()
    if character.id in trailblazer_ids:
        name = text_map.get(793, lang).upper()
    draw.text((770, 52), name, font=font, fill=primary)
    text_right_pos = 770 + font.getlength(name)
    name_height = draw.textsize(name, font=font)[1]

    # character level
    padding = 50
    width = 337
    height = 110
    radius = 30
    box_x = text_right_pos + padding
    box_y = name_height // 2 - height // 2 + 52 + 23
    draw.rounded_rectangle(
        (box_x, box_y, box_x + width, box_y + height),
        radius,
        primary,
    )
    box_right_pos = box_x + width
    # write in the middle of the rectangle
    text = f"Lv. {character.level}/{character.max_level}"
    font = utils.get_font(lang, 64, "Medium")
    draw.text(
        (box_x + width // 2, box_y + height // 2),
        text,
        font=font,
        fill=white,
        anchor="mm",
    )

    # character eldolon
    padding = 36
    width = 135
    box_x = box_right_pos + padding
    draw.rounded_rectangle(
        (box_x, box_y, box_x + width, box_y + height), radius, primary
    )
    # write in the middle of the rectangle
    text = f"E{character.eidolon}"
    font = utils.get_font(lang, 64, "Medium")
    draw.text(
        (box_x + width // 2, box_y + height // 2),
        text,
        font=font,
        fill=white,
        anchor="mm",
    )

    # abilities
    width = 564
    height = 377
    radius = 25
    box_x = 770
    box_y = 252
    draw.rounded_rectangle(
        (box_x, box_y, box_x + width, box_y + height), radius, bk_light
    )

    trace_bk = Image.open("yelan/star_rail/profile/1/base/trace_bk.png")
    trace_bk = utils.mask_image_with_color(trace_bk, primary)
    x = 825
    y = 273
    padding = 16
    font = utils.get_font(lang, 48, "Bold" if dark_mode else "Medium")
    traces = (
        dutils.get(character.traces, type="Talent"),
        dutils.get(character.traces, type="Normal"),
        dutils.get(character.traces, type="BPSkill"),
        dutils.get(character.traces, type="Ultra"),
    )

    pos_tree: dict[str, mihomo.TraceTreeNode] = {}
    for t in character.trace_tree:
        t_info = tree_info[str(t.id)]
        pos = t_info["pos"]
        pos_tree[pos] = t

    technique = dutils.get(character.traces, type="Maze")
    main_bubbles: dict[str, Optional[mihomo.Trace | mihomo.TraceTreeNode]] = {
        "Talent": pos_tree.get("Point08"),
        "Normal": pos_tree.get("Point06"),
        "BPSkill": pos_tree.get("Point07"),
        "Ultra": technique,  # type: ignore
    }
    sub_bubbles: dict[str, list[mihomo.TraceTreeNode | None]] = {
        "Talent": [
            pos_tree.get("Point16"),
            pos_tree.get("Point17"),
            pos_tree.get("Point18"),
        ],
        "Normal": [
            pos_tree.get("Point10"),
            pos_tree.get("Point11"),
            pos_tree.get("Point12"),
        ],
        "BPSkill": [
            pos_tree.get("Point13"),
            pos_tree.get("Point14"),
            pos_tree.get("Point15"),
        ],
        "Ultra": [pos_tree.get("Point09")],
    }

    for i, t in enumerate(traces):
        if t is None:
            continue

        # trace bubble
        icon = utils.get_cache(t.icon)
        icon = utils.mask_image_with_color(icon, white)
        icon = icon.resize((65, 65))
        im.paste(trace_bk, (x, y), trace_bk)
        im.paste(icon, (x + 7, y + 4), icon)
        draw.text((x + 109, y + 35), str(t.level), font=font, fill=white, anchor="mm")

        # main bubble
        circle_height = 72
        circle_x = x + 178
        main_bubble = main_bubbles[t.type]
        if main_bubble:
            icon = utils.get_cache(main_bubble.icon)
            icon = utils.mask_image_with_color(icon, white)
            icon = icon.resize((60, 60))
            draw.ellipse(
                (circle_x, y, circle_x + circle_height, y + circle_height),
                fill=primary,
            )
            im.paste(icon, (circle_x + 6, y + 6), icon)

        # sub bubbles
        circle_x += circle_height + 14
        sub_circle_height = 50
        circle_y = y + (circle_height - sub_circle_height) // 2
        sub_bubbles_ = sub_bubbles[t.type]
        for sub_bubble in sub_bubbles_:
            if sub_bubble is None:
                continue
            # draw a line in the middle of the circle
            width = 10
            draw.line(
                (
                    circle_x - 15,
                    y + circle_height // 2,
                    circle_x + width,
                    y + circle_height // 2,
                ),
                fill=bk,
                width=width,
            )
            draw.ellipse(
                (
                    circle_x,
                    circle_y,
                    circle_x + sub_circle_height,
                    circle_y + sub_circle_height,
                ),
                fill=bk,
            )

            icon = utils.get_cache(sub_bubble.icon)
            icon = utils.mask_image_with_color(icon, white)
            icon = icon.resize((50, 50))
            # place the icon in the middle of the circle
            icon_x = circle_x + (sub_circle_height - icon.width) // 2
            icon_y = circle_y + (sub_circle_height - icon.height) // 2
            im.paste(icon, (icon_x, icon_y), icon)

            circle_x += 64

        y += trace_bk.height + padding

    # character stats
    width = 564
    height = 609
    box_x = 770
    box_y = 653
    radius = 25
    draw.rounded_rectangle(
        (box_x, box_y, box_x + width, box_y + height), radius, bk_light
    )

    dmg_exception = ("break_dmg", "crit_dmg")
    dmg_additions = [
        a
        for a in character.additions
        if "dmg" in a.field and not any(e in a.field for e in dmg_exception)
    ]
    max_dmg_add = max(dmg_additions, key=lambda a: a.value) if dmg_additions else None

    field_names = [
        "hp",
        "def",
        "atk",
        "spd",
        "crit_rate",
        "crit_dmg",
        "break_dmg",
        "effect_hit",
        "effect_res",
        "sp_rate",
        "heal_rate",
    ]
    stats = (
        dutils.get(character.attributes, field=field_names[0]),
        dutils.get(character.attributes, field=field_names[1]),
        dutils.get(character.attributes, field=field_names[2]),
        dutils.get(character.attributes, field=field_names[3]),
        dutils.get(character.attributes, field=field_names[4]),
        dutils.get(character.attributes, field=field_names[5]),
        dutils.get(character.attributes, field=field_names[6]),
        dutils.get(character.attributes, field=field_names[7]),
        dutils.get(character.attributes, field=field_names[8]),
        dutils.get(character.attributes, field=field_names[9]),
        dutils.get(character.attributes, field=field_names[10]),
        max_dmg_add,
    )
    x = 804
    y = 685
    text_padding = 14
    padding = 13
    for i, s in enumerate(stats):
        value = 0
        if s:
            value += s.value

        if i == 11:
            if s:
                field_names.append(s.field)
            else:
                element = character.element
                field_names.append(f"{element.id.lower()}_dmg")
        else:
            add = dutils.get(character.additions, field=field_names[i])
            if add:
                value += add.value

        if i >= 4:
            text = f"{round(value*100, 1)}%"
        else:
            text = f"{round(value):,}"

        icon = Image.open(f"yelan/star_rail/profile/1/icon/{field_names[i]}.png")
        icon = icon.resize((80, 80))
        icon = utils.mask_image_with_color(icon, dark)
        im.paste(icon, (x, y), icon)

        font = utils.get_font(lang, 40)
        draw.text(
            (
                x + icon.width + text_padding,
                y + 13,
            ),
            text,
            font=font,
            fill=dark,
        )

        if field_names[i] == "crit_dmg":
            x = 1070
            y = 685
        else:
            y += icon.height + padding

    # light cone
    cone = character.light_cone
    if cone:
        width = 629
        height = 377
        box_x = 1375
        box_y = 252
        radius = 25
        draw.rounded_rectangle(
            (box_x, box_y, box_x + width, box_y + height), radius, bk_light
        )

        # light cone icon
        icon = utils.get_cache(cone.portrait)
        icon = icon.resize((221, 314))
        im.paste(icon, (box_x + 27, box_y + 25), icon)
        icon_right_pos = box_x + 27 + icon.width
        icon_top_pos = box_y + 25

        # light cone name
        font = utils.get_font(lang, 48, "Medium")
        text = cone.name
        max_width = 312
        if font.getlength(text) > max_width:
            text = utils.shorten_text(text, max_width, font)
        draw.text(
            (icon_right_pos + 28, icon_top_pos),
            text,
            font=font,
            fill=dark,
        )
        text_bottom_pos = icon_top_pos + font.getbbox(text)[3]
        text_left_pos = icon_right_pos + 28

        # level
        width = 182
        height = 55
        radius = 10
        box_x = text_left_pos
        box_y = text_bottom_pos + 20
        draw.rounded_rectangle(
            (box_x, box_y, box_x + width, box_y + height), radius, primary
        )
        font = utils.get_font(lang, 36, "Medium")
        text = f"Lv. {cone.level}/{cone.max_level}"
        draw.text(
            (box_x + width // 2, box_y + height // 2),
            text,
            font=font,
            fill=white,
            anchor="mm",
        )
        box_right_pos = box_x + width

        # superimpose
        width = 82
        height = 55
        radius = 10
        box_x = box_right_pos + 20
        draw.rounded_rectangle(
            (box_x, box_y, box_x + width, box_y + height), radius, primary
        )
        font = utils.get_font(lang, 36, "Medium")
        text = f"S{cone.superimpose}"
        draw.text(
            (box_x + width // 2, box_y + height // 2),
            text,
            font=font,
            fill=white,
            anchor="mm",
        )
        box_bottom_pos = box_y + height

        x = text_left_pos
        y = box_bottom_pos + 20
        text_padding = 17
        font = utils.get_font(lang, 36)
        for i, attr in enumerate(cone.attributes):
            icon = Image.open(f"yelan/star_rail/profile/1/icon/{attr.field}.png")
            icon = icon.resize((50, 50))
            icon = utils.mask_image_with_color(icon, dark)
            im.paste(icon, (x, y), icon)

            text = attr.displayed_value
            text_x = x + icon.width + 5
            draw.text((text_x, y), text, font=font, fill=dark)
            text_right_pos = text_x + font.getbbox(text)[2]
            x = text_right_pos + text_padding
            if i == 1:
                x = text_left_pos
                y += icon.height + 20

    # relic
    relics = character.relics
    x = 1374
    y = 653
    width = 399
    height = 187
    radius = 25
    x_padding = 40
    y_padding = 24
    for r_i, r in enumerate(relics):
        # relic icon
        draw.rounded_rectangle((x, y, x + width, y + height), radius, bk_light)
        icon = utils.get_cache(r.icon)
        icon = icon.resize((128, 128))
        im.paste(icon, (x + 14, y + 19), icon)
        icon_right_pos = x + 14 + icon.width

        # rarity
        star_icon = Image.open("yelan/star_rail/profile/1/img/star.png")
        star_icon = star_icon.resize((20, 20))
        star_icon = utils.mask_image_with_color(star_icon, primary)
        # align with the middle of relic icon
        pos = (x + 68 + star_icon.height // 2, y + 150 + star_icon.height // 2)
        number = r.rarity
        size = star_icon.size
        upper_left = (pos[0] - number / 2 * size[0], pos[1] - size[1] / 2)
        for i in range(number):
            im.paste(
                star_icon,
                (int(upper_left[0] + i * (size[0])), int(upper_left[1])),
                star_icon,
            )

        # main stat
        icon = Image.open(f"yelan/star_rail/profile/1/icon/{r.main_affix.field}.png")
        icon = icon.resize((50, 50))
        icon = utils.mask_image_with_color(icon, dark)
        icon_y = y + 25
        im.paste(icon, (icon_right_pos, icon_y), icon)
        main_stat_icon_right_pos = icon_right_pos + icon.width
        # text
        font = utils.get_font(lang, 36, "Medium")
        text = r.main_affix.displayed_value
        draw.text(
            (main_stat_icon_right_pos + 5, icon_y + 1), text, font=font, fill=dark
        )
        text_right_pos = main_stat_icon_right_pos + 5 + font.getbbox(text)[2]

        # level
        level_width = 58
        level_height = 34
        radius = 10
        padding = 10
        box_y = y + 33
        draw.rounded_rectangle(
            (
                text_right_pos + padding,
                box_y,
                text_right_pos + padding + level_width,
                box_y + level_height,
            ),
            radius,
            primary,
        )
        box_x = text_right_pos + padding
        font = utils.get_font(lang, 24, "Bold" if dark_mode else "Medium")
        text = f"+{r.level}"
        draw.text(
            (box_x + level_width // 2, box_y + level_height // 2),
            text,
            font=font,
            fill=white,
            anchor="mm",
        )

        # sub stats
        stat_x = icon_right_pos + 8  # main stat icon right pos
        stat_y = icon_y + icon.height + 10  # main stat icon bottom pos
        stat_y_padding = 10
        font = utils.get_font(lang, 24)
        for i, stat in enumerate(r.sub_affixes):
            icon = Image.open(f"yelan/star_rail/profile/1/icon/{stat.field}.png")
            icon = icon.resize((40, 40))
            icon = utils.mask_image_with_color(icon, dark)
            im.paste(icon, (stat_x, stat_y), icon)
            sub_stat_icon_right_pos = stat_x + icon.width

            text = stat.displayed_value
            draw.text(
                (sub_stat_icon_right_pos + 5, stat_y + 3), text, font=font, fill=dark
            )
            stat_x = sub_stat_icon_right_pos + 81
            if i == 1:
                stat_x = icon_right_pos + 8
                stat_y += icon.height + stat_y_padding

        y += height + y_padding
        if r_i == 2:
            x += width + x_padding
            y = 653

    # shenhe logo
    x = 2047
    y = 250
    width = 168
    height = 178
    radius = 25
    draw.rounded_rectangle((x, y, x + width, y + height), radius, bk_light)
    box_bottom_pos = y + height

    shenhe_logo = Image.open("yelan/star_rail/profile/1/img/shenhe.png")
    shenhe_logo = shenhe_logo.resize((150, 150))
    shenhe_logo = utils.mask_image_with_color(shenhe_logo, bk)
    im.paste(shenhe_logo, (x + 9, y + 4), shenhe_logo)

    font = utils.get_font(lang, 20, "Medium")
    text = "shenhe.bot.nu"
    draw.text((x + width // 2, y + height - 14), text, font=font, fill=bk, anchor="mm")

    # mihomo logo
    x = 2047
    y = box_bottom_pos + 32
    draw.rounded_rectangle((x, y, x + width, y + height), radius, bk_light)

    mihomo_logo = Image.open("yelan/star_rail/profile/1/img/mihomo.png")
    mihomo_logo = mihomo_logo.resize((150, 150))
    mihomo_logo = utils.mask_image_with_color(mihomo_logo, bk)
    im.paste(mihomo_logo, (x + 9, y + 4), mihomo_logo)

    text = "api.mihomo.me"
    draw.text((x + width // 2, y + height - 14), text, font=font, fill=bk, anchor="mm")

    bytes_obj = io.BytesIO()
    im.save(bytes_obj, "PNG", optimize=True)
    return bytes_obj
