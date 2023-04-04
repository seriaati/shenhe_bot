import io
from typing import List

import enkanetwork as enka
from discord import Locale
from PIL import Image, ImageDraw

import dev.asset as asset
from apps.draw.utility import circular_crop, get_cache, get_font
from apps.text_map import text_map
from data.game.artifact_slot import get_artifact_slot_name
from data.game.calc_substat_roll import calculate_substat_roll


def combine_artifact_images(images: List[Image.Image], dark_mode: bool) -> io.BytesIO:
    # Get the size of each image
    size = images[0].size

    # Calculate the number of rows and columns
    num_rows = len(images) // 3 + 1 if len(images) % 3 != 0 else len(images) // 3
    num_cols = 3 if len(images) >= 3 else len(images)

    # Create a new image with the required size
    background_color = (
        asset.dark_theme_background if dark_mode else asset.light_theme_background
    )
    im = Image.new("RGB", (num_cols * size[0], num_rows * size[1]), background_color)

    # Paste each image onto the new image
    for i, item in enumerate(images):
        row = i // 3
        col = i % 3
        x = col * size[0]
        y = row * size[1]
        if row == 1:
            x += size[0] // 2
        im.paste(item, (x, y))

    fp = io.BytesIO()
    im = im.convert("RGB")
    im.save(fp, format="JPEG", quality=100, optimize=True)
    return fp


def draw_artifact(
    artifact: enka.Equipments,
    character: enka.CharacterInfo,
    locale: Locale | str,
    dark_mode: bool,
) -> Image.Image:
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
        f"{main_stat.value} {'%' if main_stat.type is enka.DigitType.PERCENT else ''}",
        font=font,
        fill=color,
    )

    # sub stats
    cv_value = 0.0
    for index, substat in enumerate(artifact.detail.substats):
        font = get_font(locale, 18)
        color = asset.white if dark_mode else asset.primary_text
        draw.text(
            (42, 341 + index * 29),
            f"{substat.name} +{substat.value}{'%' if substat.type is enka.DigitType.PERCENT else ''}",
            font=font,
            fill=color,
        )

        roll = calculate_substat_roll(
            substat.prop_id, substat.value, artifact.detail.rarity
        )
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

    # level
    font = get_font(locale, 16)
    color = asset.white
    text = f"+{artifact.level}"
    text_size = font.getsize(text)
    width = 42 + 17 * 2 + text_size[0]
    height = 294 + text_size[1] + 8
    draw.rounded_rectangle(
        (
            42,
            294,
            width,
            height,
        ),
        fill="#303030" if dark_mode else "#7d7d7d",
        radius=30,
    )
    draw.text(
        (42 + (width - 42) // 2, 294 + (height - 294) // 2),
        text,
        font=font,
        fill=color,
        anchor="mm",
    )

    # cv value
    font = get_font(locale, 16)
    color = asset.white
    text = f"{text_map.get(747, locale)} {round(cv_value, 1)}"
    text_size = font.getsize(text)
    width = 115 + 17 * 2 + text_size[0]
    height = 294 + text_size[1] + 8
    draw.rounded_rectangle(
        (
            115,
            294,
            width,
            height,
        ),
        fill="#303030" if dark_mode else "#7d7d7d",
        radius=30,
    )
    draw.text(
        (115 + (width - 115) // 2, 294 + (height - 294) // 2),
        text,
        font=font,
        fill=color,
        anchor="mm",
    )

    # equipper name
    font = get_font(locale, 18)
    color = asset.white if dark_mode else asset.primary_text
    draw.text(
        (102, 489),
        text_map.get(79, locale).format(character_name=character.name),
        font=font,
        fill=color,
    )

    return im


def draw_artifact_image(
    character: enka.CharacterInfo,
    artifacts: List[enka.Equipments],
    locale: Locale | str,
    dark_mode: bool,
) -> io.BytesIO:
    images = []
    for artifact in artifacts:
        images.append(draw_artifact(artifact, character, locale, dark_mode))

    return combine_artifact_images(images, dark_mode)
