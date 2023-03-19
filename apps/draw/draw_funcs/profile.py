import io
from typing import Optional, Tuple, Union

import discord
import enkanetwork
from PIL import Image, ImageChops, ImageDraw

import asset
import apps.draw.utility as draw_utility
from apps.genshin.custom_model import DynamicBackgroundInput, TopPadding
from apps.text_map.text_map_app import text_map


def character_card(
    character: enkanetwork.model.CharacterInfo,
    locale: discord.Locale | str,
    dark_mode: bool = False,
    custom_image_url: Optional[str] = None,
) -> Optional[io.BytesIO]:
    # traveler
    character_id = character.id
    if character.id in (10000005, 10000007):
        character_id = f"{character.id}-{character.element.name.lower()}"

    # get the template
    if dark_mode:
        path = f"yelan/templates/build_cards/[dark] {character_id}.png"
        fight_prop_path = "resources/images/fight_props/[dark] "
        color = asset.white
    else:
        path = f"yelan/templates/build_cards/[light] {character_id}.png"
        fight_prop_path = "resources/images/fight_props/[light] "
        color = asset.primary_text
    try:
        card: Image.Image = Image.open(path)
    except FileNotFoundError:
        return None

    element = character.element.name
    add_hurt_dict = {
        "Pyro": character.stats.FIGHT_PROP_FIRE_ADD_HURT,
        "Electro": character.stats.FIGHT_PROP_ELEC_ADD_HURT,
        "Hydro": character.stats.FIGHT_PROP_WATER_ADD_HURT,
        "Dendro": character.stats.FIGHT_PROP_GRASS_ADD_HURT,
        "Anemo": character.stats.FIGHT_PROP_WIND_ADD_HURT,
        "Geo": character.stats.FIGHT_PROP_ROCK_ADD_HURT,
        "Cryo": character.stats.FIGHT_PROP_ICE_ADD_HURT,
    }
    add_hurt_text = (
        add_hurt_dict.get(element, character.stats.FIGHT_PROP_ICE_ADD_HURT)
    ).to_percentage_symbol()

    # character stats
    texts = {
        text_map.get(292, locale): character.stats.FIGHT_PROP_MAX_HP.to_rounded(),
        text_map.get(262, locale): character.stats.FIGHT_PROP_CUR_DEFENSE.to_rounded(),
        text_map.get(260, locale): character.stats.FIGHT_PROP_CUR_ATTACK.to_rounded(),
        text_map.get(
            264, locale
        ): character.stats.FIGHT_PROP_CRITICAL.to_percentage_symbol(),
        text_map.get(
            265, locale
        ): character.stats.FIGHT_PROP_CRITICAL_HURT.to_percentage_symbol(),
        text_map.get(
            267, locale
        ): character.stats.FIGHT_PROP_CHARGE_EFFICIENCY.to_percentage_symbol(),
        text_map.get(
            266, locale
        ): character.stats.FIGHT_PROP_ELEMENT_MASTERY.to_rounded(),
        text_map.get(273, locale): add_hurt_text,
    }

    draw = ImageDraw.Draw(card)

    # write character stats
    font = draw_utility.get_font(locale, 50)
    y_pos = 773
    xpos = 230
    for key, value in texts.items():
        text = key + " - " + str(value)
        draw.text((xpos, y_pos), text, fill=color, font=font)
        y_pos += 110

    # draw weapon icon
    weapon = character.equipments[-1]
    icon = draw_utility.get_cache(weapon.detail.icon.url)
    icon.thumbnail((200, 200))
    card.paste(icon, (968, 813), icon)

    # write weapon refinement text
    draw.text((989, 774), f"R{weapon.refinement}", font=font, fill=color, anchor="mm")

    # write weapon name
    text = draw_utility.shorten_text(weapon.detail.name, 517, font)
    draw.text((1220, 835), text, fill=color, font=font, anchor="ls")

    # draw weapon mainstat icon
    mainstat = weapon.detail.mainstats
    fight_prop: Image.Image = Image.open(f"{fight_prop_path}{mainstat.prop_id}.png")
    fight_prop.thumbnail((50, 50))
    card.paste(fight_prop, (1220, 890), fight_prop)

    # write weapon mainstat text
    draw.text(
        (1300, 875),
        f"{mainstat.value}{'%' if mainstat.type == enkanetwork.DigitType.PERCENT else ''}",
        fill=color,
        font=font,
    )

    # draw weapon substat icon
    if len(weapon.detail.substats) != 0:
        substat = weapon.detail.substats[0]
        fight_prop = Image.open(f"{fight_prop_path}{substat.prop_id}.png")
        fight_prop.thumbnail((50, 50))
        card.paste(fight_prop, (1450, 890), fight_prop)

        # write weapon substat text
        draw.text(
            (1520, 875),
            f"{substat.value}{'%' if substat.type == enkanetwork.DigitType.PERCENT else ''}",
            fill=color,
            font=font,
        )

    # write weapon level text
    draw.text((1220, 960), f"Lv.{weapon.level}", font=font, fill=color)

    # write character constellation text
    text = f"C{character.constellations_unlocked}  Lv.{character.level}"
    font = draw_utility.dynamic_font_size(text, 20, 50, 220, font)
    draw.text((1050, 1122), text=text, font=font, fill=color, anchor="mm")

    # write talent levels
    x_pos = 1150
    y_pos = 1205
    font = draw_utility.get_font(locale, 50)
    for talent in character.skills:
        if talent.id in [10013, 10413]:  # ayaka and mona passive sprint
            continue
        draw.text((x_pos, y_pos), f"Lv.{talent.level}", font=font, fill=color)
        y_pos += 165

    # artifacts
    x_pos = 1860
    y_pos = 111
    substat_x_pos = 2072
    substat_y_pos = 138
    font = draw_utility.get_font(locale, 44)
    for artifact in filter(
        lambda x: x.type == enkanetwork.EquipmentsType.ARTIFACT, character.equipments
    ):
        # draw artifact icons
        icon = draw_utility.get_cache(artifact.detail.icon.url)
        icon.thumbnail((180, 180))
        card.paste(icon, (x_pos, y_pos), icon)

        # write artifact level
        draw.text(
            (x_pos + 560, y_pos - 64), f"+{artifact.level}", font=font, fill=color
        )

        # draw artifact mainstat icon
        mainstat = artifact.detail.mainstats
        fight_prop = Image.open(f"{fight_prop_path}{mainstat.prop_id}.png")
        fight_prop.thumbnail((45, 45))
        card.paste(fight_prop, (x_pos + 550 + 105, y_pos - 53), fight_prop)

        # write artifact mainstat text
        draw.text(
            (x_pos + 550 + 170, y_pos - 64),
            f"{mainstat.value}{'%' if mainstat.type == enkanetwork.DigitType.PERCENT else ''}",
            fill=color,
            font=font,
        )

        # atifact substats
        num = 1
        for substat in artifact.detail.substats:
            if num == 3:
                substat_y_pos += 85
                substat_x_pos = 2072

            # draw substat icons
            fight_prop = Image.open(f"{fight_prop_path}{substat.prop_id}.png")
            fight_prop.thumbnail((45, 45))
            card.paste(fight_prop, (substat_x_pos, substat_y_pos), fight_prop)

            # write substat text
            draw.text(
                (substat_x_pos + 70, substat_y_pos - 15),
                f"{substat.value}{'%' if substat.type == enkanetwork.DigitType.PERCENT else ''}",
                fill=color,
                font=font,
            )
            substat_x_pos += 288
            num += 1
        if num <= 3:
            substat_y_pos += 85

        substat_x_pos = 2072
        substat_y_pos += 250

        y_pos += 333

    if custom_image_url is not None:
        image_ = draw_utility.get_cache(custom_image_url)
        custom_image = draw_utility.resize_and_crop_image(image_, dark_mode=dark_mode)
        if custom_image is not None:
            element = Image.open(
                f"yelan/templates/element/[{'dark' if dark_mode else 'light'}] {character.element.name}.png"
            )
            card.paste(custom_image, (58, 61), custom_image)
            card.paste(element, (1652, 595), element)

    card = card.convert("RGB")
    fp = io.BytesIO()
    card.save(fp, "JPEG", optimize=True)
    return fp


def overview_and_characters(
    data: enkanetwork.model.base.EnkaNetworkResponse,
    dark_mode: bool,
    locale: str | discord.Locale,
) -> Tuple[io.BytesIO, io.BytesIO]:
    profile_card, _ = draw_utility.draw_dynamic_background(
        DynamicBackgroundInput(
            left_padding=43,
            top_padding=TopPadding(with_title=49, without_title=49),
            right_padding=44,
            bottom_padding=48,
            card_width=723,
            card_height=655,
            max_card_num=1,
            card_num=1,
            card_x_padding=0,
            card_y_padding=0,
            background_color=asset.dark_theme_background
            if dark_mode
            else asset.light_theme_background,
        )
    )
    user_card = user_profile_card(data.player, dark_mode)
    profile_card.paste(user_card, (45, 48), user_card)
    character_bg, _ = draw_utility.draw_dynamic_background(
        DynamicBackgroundInput(
            left_padding=46,
            top_padding=TopPadding(with_title=48, without_title=48),
            right_padding=46,
            bottom_padding=48,
            card_width=345,
            card_height=311,
            max_card_num=2,
            card_num=len(data.characters),
            card_x_padding=33,
            card_y_padding=33,
            background_color=asset.dark_theme_background
            if dark_mode
            else asset.light_theme_background,
        )
    )
    offset = (46, 48)
    for index, character in enumerate(data.characters):
        index += 1
        u_c_card = user_character_card(dark_mode, character, locale)
        character_bg.paste(u_c_card, offset, u_c_card)
        if index % 2 == 0:
            offset = (offset[0] + 378, 48)
        else:
            offset = (offset[0], offset[1] + 344)
    profile_card = profile_card.convert("RGB")
    fp = io.BytesIO()
    profile_card.save(fp, format="JPEG", quality=95, optimize=True)
    character_bg = character_bg.convert("RGB")
    fp_two = io.BytesIO()
    character_bg.save(fp_two, format="JPEG", quality=95, optimize=True)
    return fp, fp_two


def user_profile_card(
    player: enkanetwork.model.PlayerInfo,
    dark_mode: bool,
) -> Image.Image:
    im = Image.open(
        f"yelan/templates/profile/[{'dark' if dark_mode else 'light'}] Profile Card.png"
    )

    # resize and paste the namecard
    namecard = draw_utility.get_cache(player.namecard.banner.url)
    namecard = namecard.resize((723, 340))
    mask = Image.new("L", namecard.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, 723, 340), radius=10, fill=255)
    namecard.putalpha(mask)
    im.paste(namecard, (0, 0), namecard)

    # draw player icon
    player_icon = draw_utility.get_cache(player.avatar.icon.url)
    player_icon = player_icon.resize((183, 183))
    player_icon = draw_utility.circular_crop(player_icon, "#EFEFEF")
    im.paste(player_icon, (42, 231), player_icon)

    # nickname
    draw = ImageDraw.Draw(im)
    draw_utility.global_write(
        draw,
        (241, 351),
        player.nickname,
        fill=asset.primary_text if not dark_mode else asset.white,
        size=36,
        variation="Bold",
    )

    # signature
    text = player.signature
    if text:
        fill = asset.primary_text if not dark_mode else asset.white
        # if the signature is too long, split it into multiple lines
        text_list = []
        font = draw_utility.get_font("en-US", 28)
        if font.getlength(text) > 616:
            new_text = ""
            for character in text:
                if font.getlength(new_text + character) > 616:
                    text_list.append(new_text)
                    new_text = character
                else:
                    new_text += character
            text_list.append(new_text)
        else:
            text_list = [text]
        text = "\n".join(text_list)
        draw_utility.global_write(
            draw,
            (42, 436),
            text,
            fill=fill,
            size=28,
        )

    # other user info
    fill = asset.secondary_text if not dark_mode else asset.white
    font = draw_utility.get_font("en-US", 24)
    draw.text((96, 597), f"AR {player.level}", font=font, fill=fill)
    draw.text((249, 597), f"W{player.world_level}", font=font, fill=fill)
    draw.text(
        (372, 597), f"{player.abyss_floor}-{player.abyss_room}", font=font, fill=fill
    )
    draw.text((504, 597), f"{player.achievement}", font=font, fill=fill)

    return im


def user_character_card(
    dark_mode: bool,
    character: enkanetwork.model.CharacterInfo,
    locale: discord.Locale | str,
) -> Image.Image:
    im = Image.open(
        f"yelan/templates/profile/[{'dark' if dark_mode else 'light'}] Character Card.png"
    )
    character_icon = draw_utility.get_cache(character.image.icon.url)
    character_icon = character_icon.resize((115, 115))
    character_icon = draw_utility.circular_crop(character_icon)
    im.paste(character_icon, (115, 19), character_icon)
    draw = ImageDraw.Draw(im)
    font = draw_utility.get_font(locale, 32, "Medium")
    fill = asset.primary_text if not dark_mode else asset.white
    draw.text((173, 170), character.name, font=font, fill=fill, anchor="mm")
    font = draw_utility.get_font(locale, 24)
    fill = asset.secondary_text if not dark_mode else asset.white
    draw.text(
        (90, 196),
        f"C{character.constellations_unlocked}R{character.equipments[-1].refinement} Lv. {character.level}/{character.max_level}",
        font=font,
        fill=fill,
    )
    offset = (23, 258)
    font = draw_utility.get_font(locale, 20)
    for talent in character.skills:
        if talent.id in [10013, 10413]:  # ayaka and mona passive sprint
            continue
        talent_icon = draw_utility.get_cache(talent.icon.url)
        talent_icon = talent_icon.resize((36, 36))
        talent_icon = talent_icon.convert("RGBA")
        mask = Image.new(
            "RGBA",
            talent_icon.size,
            asset.primary_text if not dark_mode else asset.white,
        )
        talent_icon = ImageChops.multiply(talent_icon, mask)
        im.paste(talent_icon, offset, talent_icon)
        fill = asset.primary_text if not dark_mode else asset.white
        draw.text(
            (offset[0] + 39, offset[1] + 5),
            str(talent.level),
            font=font,
            fill=fill,
        )
        offset = (offset[0] + 80, offset[1])
    draw.text((300, 263), str(character.friendship_level), fill=fill, font=font)
    return im


def card_v2(
    locale: Union[discord.Locale, str],
    dark_mode: bool,
    character: enkanetwork.model.CharacterInfo,
    image_url: str,
) -> io.BytesIO:
    mode = "dark" if dark_mode else "light"
    # main card
    im: Image.Image = Image.open(
        f"yelan/templates/profile_v2/{mode}_{character.element.name}.png"
    )

    # character image
    c_image = draw_utility.resize_and_crop_image(
        draw_utility.get_cache(image_url), version=2, dark_mode=dark_mode
    )
    if not c_image:
        raise AssertionError("Character image not found")
    im.paste(c_image, (51, 34), c_image)

    # stats
    stats = character.stats
    stats_list = [
        stats.FIGHT_PROP_MAX_HP.to_rounded(),
        stats.FIGHT_PROP_CUR_DEFENSE.to_rounded(),
        stats.FIGHT_PROP_CUR_ATTACK.to_rounded(),
        stats.FIGHT_PROP_CRITICAL.to_percentage_symbol(),
        stats.FIGHT_PROP_CRITICAL_HURT.to_percentage_symbol(),
        stats.FIGHT_PROP_CHARGE_EFFICIENCY.to_percentage_symbol(),
        stats.FIGHT_PROP_ELEMENT_MASTERY.to_rounded(),
    ]
    add_hurt_dict = {
        "Cryo": stats.FIGHT_PROP_ICE_ADD_HURT,
        "Pyro": stats.FIGHT_PROP_FIRE_ADD_HURT,
        "Electro": stats.FIGHT_PROP_ELEC_ADD_HURT,
        "Dendro": stats.FIGHT_PROP_GRASS_ADD_HURT,
        "Hydro": stats.FIGHT_PROP_WATER_ADD_HURT,
        "Anemo": stats.FIGHT_PROP_WIND_ADD_HURT,
        "Geo": stats.FIGHT_PROP_ROCK_ADD_HURT,
        "Physical": stats.FIGHT_PROP_PHYSICAL_ADD_HURT,
    }
    add_hurt_icon_dict = {
        46: "Cryo",
        40: "Pyro",
        41: "Electro",
        43: "Dendro",
        42: "Hydro",
        44: "Anemo",
        45: "Geo",
        30: "ATK",
    }
    if sum([h.value for h in add_hurt_dict.values()]) == 0:
        final_add_hurt = add_hurt_dict[character.element.name]
    else:
        final_add_hurt = max(list(add_hurt_dict.values()), key=lambda x: x.value)
    stats_list.append(final_add_hurt.to_percentage_symbol())
    add_hurt_icon = Image.open(
        f"yelan/templates/profile_v2/{mode}_{add_hurt_icon_dict.get(final_add_hurt.id)}_icon.png"
    )
    im.paste(add_hurt_icon, (590, 812), add_hurt_icon)

    draw = ImageDraw.Draw(im)
    color = (241, 241, 241, 204) if dark_mode else (33, 33, 33, 204)
    font = draw_utility.get_font("en-US", 45, "Medium")
    for index, stat in enumerate(stats_list):
        draw.text((676, 155 + 93 * index), str(stat), color, font=font)

    weapon = character.equipments[-1]
    # weapon
    weapon_icon = draw_utility.get_cache(weapon.detail.icon.url)
    weapon_icon = weapon_icon.resize((160, 160))
    im.paste(weapon_icon, (947, 151), weapon_icon)

    x_offset = 1135
    font = draw_utility.get_font(locale, 40, "Medium")
    weapon_name = weapon.detail.name
    weapon_name = draw_utility.shorten_text(weapon_name, x_offset - 819, font)
    draw.text((x_offset, 151), weapon_name, color, font=font)

    font = draw_utility.get_font("en-US", 35, "Regular")
    main_stat = weapon.detail.mainstats
    main_stat_icon = Image.open(
        f"yelan/templates/profile_v2/{mode}_{main_stat.prop_id}.png"
    )
    main_stat_icon = main_stat_icon.resize((36, 36))
    im.paste(main_stat_icon, (x_offset + 8, 220), main_stat_icon)
    text = draw_utility.format_stat(main_stat)
    draw.text((x_offset + 62, 213), text, color, font=font)

    sub_stat = weapon.detail.substats
    if sub_stat:
        sub_x_offset = x_offset + 62 + int(font.getlength(text))
        sub_stat_icon = Image.open(
            f"yelan/templates/profile_v2/{mode}_{sub_stat[0].prop_id}.png"
        )
        sub_stat_icon = sub_stat_icon.resize((36, 36))
        im.paste(sub_stat_icon, (sub_x_offset + 40, 220), sub_stat_icon)
        draw.text(
            (sub_x_offset + 40 + 54, 213),
            draw_utility.format_stat(sub_stat[0]),
            color,
            font=font,
        )

    text = f"R{weapon.refinement}"
    draw.text((x_offset, 275), text, color, font=font)
    draw.text(
        (x_offset + int(font.getlength(text)) + 30, 275),
        f"Lv.{weapon.level}/{weapon.max_level}",
        color,
        font=font,
    )

    # constellations
    # start pos (1025, 380)
    # 3x2 grid, x offset between each item is 137, y offset is 106
    for index, const in enumerate(character.constellations):
        if const.unlocked:
            icon_color = (255, 255, 255, 255) if dark_mode else (67, 67, 67, 255)
        else:
            icon_color = (255, 255, 255, 50) if dark_mode else (67, 67, 67, 38)
        const_icon = draw_utility.get_cache(const.icon.url)
        const_icon = const_icon.convert("RGBA")
        const_icon = const_icon.resize((80, 80))
        const_icon = draw_utility.mask_image_with_color(const_icon, icon_color)
        im.paste(
            const_icon, (1025 + 137 * (index % 3), 380 + 106 * (index // 3)), const_icon
        )

    # talents
    # start pos (1025, 636)
    # 3x1 grid, x offset between each item is 137
    # text is 92 below the icon
    for index, t in enumerate(character.skills):
        x_pos = 1025 + 137 * index
        icon_color = (255, 255, 255, 255) if dark_mode else (67, 67, 67, 255)
        talent_icon = draw_utility.get_cache(t.icon.url)
        talent_icon = talent_icon.convert("RGBA")
        talent_icon = talent_icon.resize((80, 80))
        talent_icon = draw_utility.mask_image_with_color(talent_icon, icon_color)
        im.paste(talent_icon, (x_pos, 636), talent_icon)

        draw.text(
            (x_pos + talent_icon.width // 2, 748),
            str(t.level),
            color,
            font=font,
            anchor="mm",
        )

    # friendship level
    font = draw_utility.get_font("en-US", 30, "Regular")
    draw.text((1132, 840), str(character.friendship_level), color, font=font)

    # level
    draw.text(
        (1215, 840), f"Lv.{character.level}/{character.max_level}", color, font=font
    )

    # artifacts
    # start pos (68, 970)
    # 5x1 grid, x offset between each item is 296
    artifacts = [
        e for e in character.equipments if e.type is enkanetwork.EquipmentsType.ARTIFACT
    ]
    for index, a in enumerate(artifacts):
        x_pos = 68 + 296 * index

        # icon
        artifact_icon = draw_utility.get_cache(a.detail.icon.url)
        artifact_icon = artifact_icon.resize((90, 90))
        im.paste(artifact_icon, (x_pos, 970), artifact_icon)

        # rarity
        rarity_x_dict = {1: 36, 2: 25, 3: 16, 4: 6, 5: -4}
        rarity_icon = Image.open(
            f"yelan/templates/profile_v2/{mode}_{a.detail.rarity}.png"
        )
        im.paste(
            rarity_icon, (x_pos + rarity_x_dict[a.detail.rarity], 1066), rarity_icon
        )

        # main stat
        font = draw_utility.get_font("en-US", 30, "Medium")
        main_stat = a.detail.mainstats
        main_stat_icon = Image.open(
            f"yelan/templates/profile_v2/{mode}_{main_stat.prop_id}.png"
        )
        main_stat_icon = main_stat_icon.resize((32, 32))
        text = draw_utility.format_stat(main_stat)
        main_stat_x = int(x_pos + 245 - font.getlength(text))
        draw.text((main_stat_x, 1050), text, color, font=font)
        im.paste(
            main_stat_icon,
            (main_stat_x - main_stat_icon.width - 10, 1056),
            main_stat_icon,
        )

        # level
        level_text = f"+{a.level}"
        draw.text(
            (
                main_stat_x + font.getlength(text) - font.getlength(level_text),
                1004,
            ),
            level_text,
            color,
            font=font,
        )

        # sub stats
        # 2x2 grid
        font = draw_utility.get_font("en-US", 23, "Light")
        for sub_index, sub_stat in enumerate(a.detail.substats):
            sub_x_offset = x_pos + 30 + 116 * (sub_index % 2)
            sub_y_offset = 1120 + 54 * (sub_index // 2)
            sub_stat_icon = Image.open(
                f"yelan/templates/profile_v2/{mode}_{sub_stat.prop_id}.png"
            )
            icon_color = (255, 255, 255, 200) if dark_mode else (67, 67, 67, 150)
            sub_stat_icon = sub_stat_icon.resize((27, 27))
            sub_stat_icon = sub_stat_icon.convert("RGBA")
            sub_stat_icon = draw_utility.mask_image_with_color(
                sub_stat_icon, icon_color
            )
            im.paste(sub_stat_icon, (sub_x_offset, sub_y_offset), sub_stat_icon)
            draw.text(
                (sub_x_offset + 35, sub_y_offset - 2),
                draw_utility.format_stat(sub_stat),
                icon_color,
                font=font,
            )

    im = im.convert("RGB")
    fp = io.BytesIO()
    im.save(fp, format="JPEG", quality=95, optimize=True)
    return fp
