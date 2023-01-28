from PIL import Image, ImageDraw
from apps.draw.utility import get_cache, circular_crop, get_font
from data.game.artifact_slot import get_artifact_slot_name
from data.game.calc_substat_roll import calculate_substat_roll
from enkanetwork import DigitType, Equipments, CharacterInfo
from discord import Locale
import asset
from apps.text_map.text_map_app import text_map
import io


def draw_artifact(
    artifact: Equipments,
    character: CharacterInfo,
    locale: Locale | str,
    dark_mode: bool,
) -> io.BytesIO:
    im: Image.Image = Image.open(
        f"yelan/templates/artifact/[{'dark' if dark_mode else 'light'}] {artifact.detail.rarity}.png"
    )

    # artifact icon
    artifact_icon = get_cache(artifact.detail.icon.url)
    artifact_icon = artifact_icon.resize((157, 157))
    im.paste(artifact_icon, (228, 109), artifact_icon)

    # character icon
    character_icon = get_cache(character.image.icon.url)
    character_icon = character_icon.resize((40, 40))
    character_icon = circular_crop(character_icon)
    im.paste(character_icon, (42, 483), character_icon)

    draw = ImageDraw.Draw(im)

    # artifact name
    font = get_font(locale, 26, "Medium")
    color = asset.white
    draw.text((42, 27), artifact.detail.name, font=font, fill=color)

    # slot name
    font = get_font(locale, 20)
    color = asset.white if dark_mode else asset.primary_text
    draw.text(
        (42, 84),
        get_artifact_slot_name(artifact.detail.artifact_type, locale),
        font=font,
        fill=color,
    )

    # main stat name
    font = get_font(locale, 20)
    color = asset.white if dark_mode else asset.secondary_text
    main_stat = artifact.detail.mainstats
    draw.text((42, 177), main_stat.name, font=font, fill=color)

    # main stat value
    font = get_font(locale, 36, "Medium")
    color = asset.white if dark_mode else asset.primary_text
    draw.text(
        (42, 206),
        f"{main_stat.value} {'%' if main_stat.type is DigitType.PERCENT else ''}",
        font=font,
        fill=color,
    )

    # artifact level
    font = get_font(locale, 16)
    color = asset.white
    draw.text((71, 306), f"+{artifact.level}", font=font, fill=color, anchor="mm")

    # sub stats
    cv_value = 0.0
    for index, substat in enumerate(artifact.detail.substats):
        font = get_font(locale, 18)
        color = asset.white if dark_mode else asset.primary_text
        draw.text(
            (42, 341 + index * 29),
            f"{substat.name} +{substat.value}{'%' if substat.type is DigitType.PERCENT else ''}",
            font=font,
            fill=color,
        )

        roll = calculate_substat_roll(substat.prop_id, substat.value)
        for i in range(1, roll + 1):
            roll_icon = Image.open(
                f"yelan/templates/artifact/[{'dark' if dark_mode else 'light'}] _{i}.png"
            )
            roll_icon = roll_icon.resize((8, 18))
            im.paste(roll_icon, (358 - i * 15, 341 + index * 29), roll_icon)

        if substat.prop_id == "FIGHT_PROP_CRITICAL":
            cv_value += substat.value * 2
        elif substat.prop_id == "FIGHT_PROP_CRITICAL_HURT":
            cv_value += substat.value

    # cv value
    font = get_font(locale, 16)
    color = asset.white
    draw.text((159, 306), f"CV {round(cv_value, 1)}", font=font, fill=color, anchor="mm")

    # equipper name
    font = get_font(locale, 18)
    color = asset.white if dark_mode else asset.primary_text
    draw.text(
        (102, 489),
        text_map.get(79, locale).format(character_name=character.name),
        font=font,
        fill=color,
    )
    
    fp = io.BytesIO()
    im = im.convert("RGB")
    im.save(fp, format="JPEG", quality=100, optimize=True)
    return fp