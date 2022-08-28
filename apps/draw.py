from os import listdir
from os.path import join, isfile
from random import choice
from typing import Dict, List, Tuple
from time import process_time
from utility.utils import log
import aiohttp
from discord import Locale
import genshin
from discord import Asset
from ambr.client import AmbrTopAPI
from ambr.models import Character, Domain, Material, Weapon
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from apps.text_map.convert_locale import to_ambr_top
from data.draw.fonts import get_font
from enkanetwork.model.character import CharacterInfo
from enkanetwork.model.assets import IconAsset
from enkanetwork.enum import DigitType, EquipmentsType
from apps.text_map.text_map_app import text_map
from utility.utils import divide_chunks
import uuid
import yaml


async def draw_domain_card(
    domain: Domain,
    locale: Locale | str,
    items: Dict[int, Character | Weapon],
) -> Image:
    with open("data/draw/domain_card_map.yaml", "r+") as f:
        card_map = yaml.full_load(f)

    if card_map.get(str(items)) is not None:
        domain_card = Image.open(
            f"resources/images/domain_cards/{card_map[str(items)]}.jpeg"
        )
        fp = BytesIO()
        domain_card.save(fp, "JPEG", optimize=True, quality=40)

    else:
        session = aiohttp.ClientSession()
        text = domain.name
        font_family = get_font(locale)

        # get domain template image
        background_paths = ["", "Mondstat", "Liyue", "Inazuma", "Sumeru"]
        domain_card = Image.open(
            f"resources/images/templates/{background_paths[domain.city.id]} Farm.png"
        )

        # dynamic font size
        fontsize = 50
        font = ImageFont.truetype(f"resources/fonts/{font_family}", fontsize)
        while font.getsize(text)[0] < 0.5 * domain_card.size[0]:
            fontsize += 1
            font = ImageFont.truetype(f"resources/fonts/{font_family}", fontsize)

        # draw the domain text
        draw = ImageDraw.Draw(domain_card)
        draw.text((987, 139), text, fill="#333", font=font, anchor="mm")
        # initialize variables
        count = 1
        offset = (150, 340)

        for item_id, item in items.items():
            # get path based on object
            if isinstance(item, Weapon):
                path = f"resources/images/weapon/{item.id}.png"
            else:
                path = f"resources/images/character/{item.id}.png"

            # try to use local image
            try:
                icon = Image.open(path)
                icon = icon.convert("RGBA")

            # if not found then download it
            except FileNotFoundError:
                async with session.get(item.icon) as r:
                    bytes_obj = BytesIO(await r.read())
                icon = Image.open(bytes_obj)
                icon = icon.convert("RGBA")
                icon.save(path, "PNG")

            # resize the icon
            icon.thumbnail((180, 180))

            # draw the icon on to the domain card
            domain_card.paste(icon, offset, icon)

            # change offset
            offset = list(offset)
            offset[0] += 400

            # if four in a row, move to next row
            if count % 4 == 0:
                offset[0] = 150
                offset[1] += 250
            offset = tuple(offset)

            count += 1

        uuid_str = str(uuid.uuid4())
        card_map[str(items)] = uuid_str
        domain_card = domain_card.convert("RGB")
        fp = BytesIO()
        domain_card.save(fp, "JPEG", optimize=True, quality=40)
        domain_card.save(f"resources/images/domain_cards/{uuid_str}.jpeg", "JPEG")
        with open("data/draw/domain_card_map.yaml", "w+") as f:
            yaml.dump(card_map, f)
        await session.close()
    return fp


async def draw_character_card(
    character: CharacterInfo, locale: Locale | str, session: aiohttp.ClientSession
) -> BytesIO:
    start = process_time()
    # load font
    font_family = get_font(locale)

    character_id = character.id

    # traveler
    if character.id == 10000005 or character.id == 10000007:
        character_id = f"{character.id}-{character.element.name.lower()}"

    # try to get the template
    try:
        card = Image.open(f"resources/images/templates/build_cards/{character_id}.png")
    except FileNotFoundError:
        return None

    draw = ImageDraw.Draw(card)
    font = ImageFont.truetype(f"resources/fonts/{font_family}", 50)

    element = character.element.name
    element_text_map = {
        "Pyro": 273,
        "Electro": 274,
        "Hydro": 275,
        "Dendro": 276,
        "Anemo": 277,
        "Geo": 278,
        "Cryo": 279,
    }
    element_text_map_hash = element_text_map.get(element)

    add_hurt_dict = {
        "Pyro": character.stats.FIGHT_PROP_FIRE_ADD_HURT,
        "Electro": character.stats.FIGHT_PROP_ELEC_ADD_HURT,
        "Hydro": character.stats.FIGHT_PROP_WATER_ADD_HURT,
        "Dendro": character.stats.FIGHT_PROP_GRASS_ADD_HURT,
        "Anemo": character.stats.FIGHT_PROP_WIND_ADD_HURT,
        "Geo": character.stats.FIGHT_PROP_ROCK_ADD_HURT,
        "Cryo": character.stats.FIGHT_PROP_ICE_ADD_HURT,
    }

    add_hurt_text = (add_hurt_dict.get(element)).to_percentage_symbol()

    # character stats
    texts = {
        text_map.get(292, locale): character.stats.FIGHT_PROP_MAX_HP.to_rounded(),
        text_map.get(294, locale): character.stats.FIGHT_PROP_CUR_DEFENSE.to_rounded(),
        text_map.get(293, locale): character.stats.FIGHT_PROP_CUR_ATTACK.to_rounded(),
        text_map.get(
            296, locale
        ): character.stats.FIGHT_PROP_CRITICAL.to_percentage_symbol(),
        text_map.get(
            297, locale
        ): character.stats.FIGHT_PROP_CRITICAL_HURT.to_percentage_symbol(),
        text_map.get(
            298, locale
        ): character.stats.FIGHT_PROP_CHARGE_EFFICIENCY.to_percentage_symbol(),
        text_map.get(
            295, locale
        ): character.stats.FIGHT_PROP_ELEMENT_MASTERY.to_rounded(),
        text_map.get(element_text_map_hash, locale): add_hurt_text,
    }

    # write character stats
    y_pos = 770
    xpos = 230
    for key, value in texts.items():
        text = key + " - " + str(value)
        draw.text((xpos, y_pos), text, (0, 0, 0), font=font)
        y_pos += 110

    # draw weapon icon
    weapon = character.equipments[-1]

    path = f"resources/images/weapon/{weapon.id}.png"
    try:
        icon = Image.open(path)
        icon = icon.convert("RGBA")
    except FileNotFoundError:
        async with session.get(weapon.detail.icon.url) as r:
            bytes_obj = BytesIO(await r.read())
        icon = Image.open(bytes_obj)
        icon = icon.convert("RGBA")
        icon.save(path, "PNG")

    icon.thumbnail((200, 200))
    card.paste(icon, (968, 813), icon)

    # write weapon refinement text
    draw.text((956, 736), f"R{weapon.refinement}", font=font, fill="#212121")

    # write weapon name
    draw.text((1220, 785), weapon.detail.name, fill="#212121", font=font)

    # draw weapon mainstat icon
    mainstat = weapon.detail.mainstats
    fight_prop = Image.open(f"resources/images/fight_props/{mainstat.prop_id}.png")
    fight_prop.thumbnail((50, 50))
    card.paste(fight_prop, (1220, 890), fight_prop)

    # write weapon mainstat text
    draw.text(
        (1300, 875),
        f"{mainstat.value}{'%' if mainstat.type == DigitType.PERCENT else ''}",
        fill="#212121",
        font=font,
    )

    # draw weapon substat icon
    if len(weapon.detail.substats) != 0:
        substat = weapon.detail.substats[0]
        fight_prop = Image.open(f"resources/images/fight_props/{substat.prop_id}.png")
        fight_prop.thumbnail((50, 50))
        card.paste(fight_prop, (1450, 890), fight_prop)

        # write weapon substat text
        draw.text(
            (1520, 875),
            f"{substat.value}{'%' if substat.type == DigitType.PERCENT else ''}",
            fill="#212121",
            font=font,
        )

    # write weapon level text
    draw.text((1220, 960), f"Lvl. {weapon.level}", font=font, fill="#212121")

    # write character constellation text
    draw.text(
        (956, 1084), f"C{character.constellations_unlocked}", font=font, fill="#212121"
    )

    # write talent levels
    x_pos = 1132
    y_pos = 1180
    for index, talent in enumerate(character.skills):
        if (character.id == 10000002 or character.id == 10000041) and index == 2:
            continue
        draw.text((x_pos, y_pos), f"Lvl. {talent.level}", font=font, fill="#212121")
        y_pos += 165

    # artifacts
    x_pos = 1860
    y_pos = 111
    substat_x_pos = 2072
    substat_y_pos = 138
    font = ImageFont.truetype(f"resources/fonts/{font_family}", 44)
    for artifact in filter(
        lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments
    ):

        # draw artifact icons
        path = f"resources/images/artifact/{artifact.id}.png"
        try:
            icon = Image.open(path)
            icon = icon.convert("RGBA")
        except FileNotFoundError:
            async with session.get(artifact.detail.icon.url) as r:
                bytes_obj = BytesIO(await r.read())
            icon = Image.open(bytes_obj)
            icon = icon.convert("RGBA")
            icon.save(path, "PNG")

        icon.thumbnail((180, 180))
        card.paste(icon, (x_pos, y_pos), icon)

        # write artifact level
        draw.text(
            (x_pos + 560, y_pos - 66), f"+{artifact.level}", font=font, fill="#212121"
        )

        # draw artifact mainstat icon
        mainstat = artifact.detail.mainstats
        fight_prop = Image.open(f"resources/images/fight_props/{mainstat.prop_id}.png")
        fight_prop.thumbnail((45, 45))
        card.paste(fight_prop, (x_pos + 550 + 105, y_pos - 53), fight_prop)

        # write artifact mainstat text
        draw.text(
            (x_pos + 550 + 170, y_pos - 66),
            f"{mainstat.value}{'%' if mainstat.type == DigitType.PERCENT else ''}",
            fill="#212121",
            font=font,
        )

        # atifact substats
        num = 1
        for substat in artifact.detail.substats:
            if num == 3:
                substat_y_pos += 85
                substat_x_pos = 2072

            # draw substat icons
            fight_prop = Image.open(
                f"resources/images/fight_props/{substat.prop_id}.png"
            )
            fight_prop.thumbnail((45, 45))
            card.paste(fight_prop, (substat_x_pos, substat_y_pos), fight_prop)

            # write substat text
            draw.text(
                (substat_x_pos + 70, substat_y_pos - 15),
                f"{substat.value}{'%' if substat.type == DigitType.PERCENT else ''}",
                fill="#212121",
                font=font,
            )
            substat_x_pos += 288
            num += 1

        substat_x_pos = 2072
        substat_y_pos += 250

        y_pos += 333

    card = card.convert("RGB")
    fp = BytesIO()
    card.save(fp, "JPEG", optimize=True, quality=40)

    end = process_time()
    log.info(f"[Draw][Character Card]: [Time]{end-start} s")
    return fp


async def draw_todo_card(
    todo_items: List[Tuple],
    locale: Locale | str,
    session: aiohttp.ClientSession,
) -> List[BytesIO]:
    start = process_time()
    result = []
    font_family = get_font(locale)
    font = ImageFont.truetype(f"resources/fonts/{font_family}", 64)

    locale = to_ambr_top(locale)
    client = AmbrTopAPI(session, locale)

    # get templates
    file_names = [
        f
        for f in listdir("resources/images/templates/todo/")
        if isfile(join("resources/images/templates/todo/", f))
    ]

    # divide todo items
    todo_items = list(divide_chunks(todo_items, 7))

    for todo_item in todo_items:
        icon_y_pos = 78
        text_x_pos = 725
        text_y_pos = 134
        file_name = choice(file_names)
        todo_card = Image.open(f"resources/images/templates/todo/{file_name}")
        draw = ImageDraw.Draw(todo_card)

        for index, tuple in enumerate(todo_item):
            item_id: str = tuple[0]
            count = tuple[1]
            if isinstance(item_id, str) and not item_id.isnumeric():
                item = Material(
                    id=0,
                    name=item_id,
                    type="custom",
                    recipe=False,
                    mapMark=False,
                    icon="",
                    rank=0,
                )
            else:
                item = await client.get_material(int(item_id))
                item = item[0]

            path = f"resources/images/material/{item_id}.png"
            # try to use local image
            try:
                icon = Image.open(path)
                icon = icon.convert("RGBA")

            # if not found then download it
            except FileNotFoundError:
                async with session.get(item.icon) as r:
                    bytes_obj = BytesIO(await r.read())
                icon = Image.open(bytes_obj)
                icon = icon.convert("RGBA")
                icon.save(path, "PNG")

            # resize the icon
            icon.thumbnail((120, 120))
            todo_card.paste(icon, (57, icon_y_pos), icon)

            # write item text
            draw.text(
                (text_x_pos, text_y_pos),
                f"{item.name} x{count}",
                fill="#212121",
                font=font,
                anchor="mm",
            )
            icon_y_pos += 233
            text_y_pos += 231
        todo_card = todo_card.convert("RGB")
        fp = BytesIO()
        todo_card.save(fp, "JPEG", optimize=True, quality=40)
        result.append(fp)

    end = process_time()
    log.info(f"[Draw][Todo Card]: [Time]{end-start} s")
    return result


async def draw_stats_card(
    user_stats: genshin.models.Stats,
    namecard: IconAsset,
    pfp: Asset,
    character_num: int,
) -> BytesIO:
    start = process_time()
    stats = {
        "active_days": user_stats.days_active,
        "characters": f"{user_stats.characters}/{character_num}",
        "achievements": user_stats.achievements,
        "abyss": user_stats.spiral_abyss,
        "anemo": f"{user_stats.anemoculi}/66",
        "geo": f"{user_stats.geoculi}/131",
        "electro": f"{user_stats.electroculi}/181",
        "dendro": f"{user_stats.dendroculi}/110",
        "normal": user_stats.common_chests,
        "rare": user_stats.precious_chests,
        "gold": user_stats.exquisite_chests,
        "lux": user_stats.luxurious_chests,
    }
    session = aiohttp.ClientSession()
    stat_card = Image.open("resources/images/templates/stats/Stat Card Template.png")

    path = f"resources/images/namecard/{namecard.filename}.png"
    try:
        namecard = Image.open(path)
    except FileNotFoundError:
        async with session.get(namecard.url) as r:
            bytes_obj = BytesIO(await r.read())
        namecard = Image.open(bytes_obj)
        namecard.save(path, "PNG")

    w, h = namecard.size
    factor = 2.56
    namecard = namecard.resize((int(w * factor), int(h * factor)))
    w, h = namecard.size
    namecard = namecard.crop((0, 190, w, h - 190))
    stat_card.paste(namecard, (112, 96))

    async with session.get(pfp.url) as r:
        bytes_obj = BytesIO(await r.read())
    pfp = Image.open(bytes_obj)

    mask = Image.new("L", pfp.size, 0)
    empty = Image.new("RGBA", pfp.size, 0)
    draw = ImageDraw.Draw(mask)
    x, y = pfp.size
    eX, eY = pfp.size
    bbox = (x / 2 - eX / 2, y / 2 - eY / 2, x / 2 + eX / 2, y / 2 + eY / 2)
    draw.ellipse(bbox, fill=255)
    pfp = Image.composite(pfp, empty, mask)
    pfp = pfp.resize((412, 412))
    stat_card.paste(pfp, (979, 462), pfp)
    draw = ImageDraw.Draw(stat_card)
    font = ImageFont.truetype("resources/fonts/NotoSans-Regular.ttf", 90)
    fill = "#333"
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
    fp = BytesIO()
    stat_card.save(fp, "JPEG", optimize=True, quality=40)
    await session.close()
    end = process_time()
    log.info(f"[Draw][Stats Card]: [Time]{end-start} s")
    return fp


async def draw_talent_reminder_card(item_ids: List[int], locale: str):
    start = process_time()
    session = aiohttp.ClientSession()
    font_family = get_font(locale)
    font = ImageFont.truetype(f"resources/fonts/{font_family}", 50)
    fill = "#333"

    locale = to_ambr_top(locale)
    client = AmbrTopAPI(session, lang=locale)

    reminder_card = Image.open(
        "resources/images/templates/remind/Talent Reminder Template.png"
    )
    icon_x, icon_y = 100, 100
    count = 1

    for item_id in item_ids:
        item = await client.get_material(item_id)
        item = item[0]

        path = f"resources/images/material/{item.id}.png"
        # try to use local image
        try:
            icon = Image.open(path)
            icon = icon.convert("RGBA")

        # if not found then download it
        except FileNotFoundError:
            async with session.get(item.icon) as r:
                bytes_obj = BytesIO(await r.read())
            icon = Image.open(bytes_obj)
            icon = icon.convert("RGBA")
            icon.save(path, "PNG")

        # resize the icon
        icon.thumbnail((120, 120))
        if count == 2:
            icon_y += 210
        elif count == 3:
            icon_y += 220
        reminder_card.paste(icon, (icon_x, icon_y), icon)
        count += 1

        draw = ImageDraw.Draw(reminder_card)
        draw.text(
            (icon_x + 670, icon_y + 55), item.name, fill=fill, font=font, anchor="mm"
        )

    reminder_card = reminder_card.convert("RGB")
    fp = BytesIO()
    reminder_card.save(fp, "JPEG", optimize=True, quality=40)
    await session.close()
    end = process_time()
    log.info(f"[Draw][Talent Reminder Card]: [Time]{end-start} s")
    return fp
