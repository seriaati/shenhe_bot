import io
from typing import Optional, Tuple

import discord
import enkanetwork
import langdetect
from PIL import Image, ImageChops, ImageDraw

import asset
from apps.draw.utility import (
    circular_crop,
    draw_dynamic_background,
    dynamic_font_size,
    get_cache,
    get_font,
    shorten_text,
)
from apps.genshin.custom_model import DynamicBackgroundInput, TopPadding
from apps.text_map.convert_locale import convert_langdetect
from apps.text_map.text_map_app import text_map


def character_card(
    character: enkanetwork.model.CharacterInfo,
    locale: discord.Locale | str,
    dark_mode: bool = False,
    custom_image_url: Optional[str] = None,
) -> Optional[io.BytesIO]:
    # traveler
    character_id = character.id
    if character.id == 10000005 or character.id == 10000007:
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
    font = get_font(locale, 50)
    y_pos = 773
    xpos = 230
    for key, value in texts.items():
        text = key + " - " + str(value)
        draw.text((xpos, y_pos), text, fill=color, font=font)
        y_pos += 110

    # draw weapon icon
    weapon = character.equipments[-1]
    icon = get_cache(weapon.detail.icon.url)
    icon.thumbnail((200, 200))
    card.paste(icon, (968, 813), icon)

    # write weapon refinement text
    draw.text((989, 774), f"R{weapon.refinement}", font=font, fill=color, anchor="mm")

    # write weapon name
    text = shorten_text(weapon.detail.name, 517, font)
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
    font = dynamic_font_size(text, 20, 50, 220, font)
    draw.text((1050, 1122), text=text, font=font, fill=color, anchor="mm")

    # write talent levels
    x_pos = 1150
    y_pos = 1205
    font = get_font(locale, 50)
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
    font = get_font(locale, 44)
    for artifact in filter(
        lambda x: x.type == enkanetwork.EquipmentsType.ARTIFACT, character.equipments
    ):

        # draw artifact icons
        icon = get_cache(artifact.detail.icon.url)
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
        custom_image = crop_custom_character_image(custom_image_url)
        element = Image.open(
            f"yelan/templates/element/[{'dark' if dark_mode else 'light'}] {character.element.name}.png"
        )
        card.paste(custom_image, (58, 61), custom_image)
        card.paste(element, (1652, 595), element)

    card = card.convert("RGB")
    fp = io.BytesIO()
    card.save(fp, "JPEG", optimize=True)
    return fp


def crop_custom_character_image(image_url: str) -> Image.Image:
    im = get_cache(image_url)

    # resize the image
    target_width = 1663
    ratio = target_width / im.width
    im = im.resize((target_width, int(im.height * ratio)))

    # crop the image
    target_height = 629
    im = im.crop((0, 0, target_width, target_height))

    # make rounded corners
    mask = Image.new("L", im.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, target_width, target_height), radius=20, fill=255)
    im.putalpha(mask)

    return im


def overview_and_characters(
    data: enkanetwork.model.base.EnkaNetworkResponse,
    dark_mode: bool,
    locale: str | discord.Locale,
) -> Tuple[io.BytesIO, io.BytesIO]:
    profile_card, _ = draw_dynamic_background(
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
    character_bg, _ = draw_dynamic_background(
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
        character_card = user_character_card(dark_mode, character, locale)
        character_bg.paste(character_card, offset, character_card)
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
):
    im = Image.open(
        f"yelan/templates/profile/[{'dark' if dark_mode else 'light'}] Profile Card.png"
    )

    # resize and paste the namecard
    namecard = get_cache(player.namecard.banner.url)
    namecard = namecard.resize((723, 340))
    mask = Image.new("L", namecard.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, 723, 340), radius=10, fill=255)
    namecard.putalpha(mask)
    im.paste(namecard, (0, 0), namecard)

    # draw player icon
    player_icon = get_cache(player.avatar.icon.url)
    player_icon = player_icon.resize((183, 183))
    player_icon = circular_crop(player_icon, "#EFEFEF")
    im.paste(player_icon, (42, 231), player_icon)

    # nickname
    draw = ImageDraw.Draw(im)
    langdetect.DetectorFactory.seed = 0
    font = get_font(convert_langdetect(langdetect.detect(player.nickname)), 36, "Bold")
    fill = asset.primary_text if not dark_mode else asset.white
    draw.text((241, 351), player.nickname, font=font, fill=fill)

    # signature
    fill = asset.primary_text if not dark_mode else asset.white
    font = get_font(convert_langdetect(langdetect.detect(player.signature)), 28)
    text = player.signature
    # if the signature is too long, split it into multiple lines
    text_list = []
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
    draw.text((42, 436), text=text, font=font, fill=fill)

    # other user info
    fill = asset.secondary_text if not dark_mode else asset.white
    font = get_font("en-US", 24)
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
):
    im = Image.open(
        f"yelan/templates/profile/[{'dark' if dark_mode else 'light'}] Character Card.png"
    )
    character_icon = get_cache(character.image.icon.url)
    character_icon = character_icon.resize((115, 115))
    character_icon = circular_crop(character_icon)
    im.paste(character_icon, (115, 19), character_icon)
    draw = ImageDraw.Draw(im)
    font = get_font(locale, 32, "Medium")
    fill = asset.primary_text if not dark_mode else asset.white
    draw.text((173, 170), character.name, font=font, fill=fill, anchor="mm")
    font = get_font(locale, 24)
    fill = asset.secondary_text if not dark_mode else asset.white
    draw.text(
        (90, 196),
        f"C{character.constellations_unlocked}R{character.equipments[-1].refinement} Lv. {character.level}/{character.max_level}",
        font=font,
        fill=fill,
    )
    offset = (23, 258)
    font = get_font(locale, 20)
    for talent in character.skills:
        if talent.id in [10013, 10413]:  # ayaka and mona passive sprint
            continue
        talent_icon = get_cache(talent.icon.url)
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
