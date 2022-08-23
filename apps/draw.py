from typing import Dict

import aiohttp
from discord import Locale
from ambr.models import Character, Domain, Weapon
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from data.draw.fonts import get_font
from enkanetwork.model.character import CharacterInfo
from enkanetwork.enum import DigitType, EquipmentsType
from apps.text_map.text_map_app import text_map


async def draw_domain_card(domain: Domain, locale: Locale | str) -> Image:
    text = domain.name
    font_family = get_font(locale)

    # get domain template image
    background_paths = ['', 'Mondstat', 'Liyue', 'Inazuma', 'Sumeru']
    domain_image = Image.open(
        f'resources/images/templates/{background_paths[domain.city.id]} Farm.png')

    # dynamic font size
    fontsize = 50
    font = ImageFont.truetype(f'resources/fonts/{font_family}', fontsize)
    while font.getsize(text)[0] < 0.5*domain_image.size[0]:
        fontsize += 1
        font = ImageFont.truetype(f'resources/fonts/{font_family}', fontsize)

    # draw the domain text
    draw = ImageDraw.Draw(domain_image)
    draw.text((987, 139), text, fill="#333", font=font, anchor='mm')

    return domain_image


async def draw_item_icons_on_domain_card(domain_card: Image, items: Dict[int, Character | Weapon], session: aiohttp.ClientSession) -> BytesIO:
    # initialize variables
    count = 1
    offset = (150, 340)

    for item_id, item in items.items():
        # get path based on object
        if isinstance(item, Weapon):
            path = f'resources/images/weapon/{item.id}.png'
        else:
            path = f'resources/images/character/{item.id}.png'

        # try to use local image
        try:
            icon = Image.open(path)
            icon = icon.convert('RGBA')

        # if not found then download it
        except FileNotFoundError:
            async with session.get(item.icon) as r:
                bytes_obj = BytesIO(await r.read())
            icon = Image.open(bytes_obj)
            icon = icon.convert('RGBA')
            icon.save(path, 'PNG')

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

    domain_card = domain_card.convert('RGB')
    fp = BytesIO()
    domain_card.save(fp, 'JPEG', optimize=True, quality=40)
    return fp

async def draw_character_card(character: CharacterInfo, locale: Locale | str, session: aiohttp.ClientSession) -> BytesIO:
    # load font
    font_family = get_font(locale)
    
    character_id = character.id
    
    # traveler
    if character.id == 10000005 or character.id == 10000007:
        character_id = f'{character.id}-{character.element.name.lower()}'
    
    # try to get the template
    try:
        card = Image.open(f'resources/images/templates/build_cards/{character_id}.png')
    except FileNotFoundError:
        return None
    
    draw = ImageDraw.Draw(card)
    font = ImageFont.truetype(f'resources/fonts/{font_family}', 50)
    
    element = character.element.name
    element_text_map = {
        'Pyro': 273,
        'Electro': 274,
        'Hydro': 275,
        'Dendro': 276,
        'Anemo': 277,
        'Geo': 278,
        'Cryo': 279
    }
    element_text_map_hash = element_text_map.get(element)
    
    # character stats
    texts = {
        text_map.get(292, locale): character.stats.FIGHT_PROP_MAX_HP.to_rounded(),
        text_map.get(294, locale): character.stats.FIGHT_PROP_CUR_DEFENSE.to_rounded(),
        text_map.get(293, locale): character.stats.FIGHT_PROP_CUR_ATTACK.to_rounded(),
        text_map.get(296, locale): character.stats.FIGHT_PROP_CRITICAL.to_percentage_symbol(),
        text_map.get(297, locale): character.stats.FIGHT_PROP_CRITICAL_HURT.to_percentage_symbol(),
        text_map.get(298, locale): character.stats.FIGHT_PROP_CHARGE_EFFICIENCY.to_percentage_symbol(),
        text_map.get(295, locale): character.stats.FIGHT_PROP_ELEMENT_MASTERY.to_rounded(),
        text_map.get(element_text_map_hash, locale): character.stats.FIGHT_PROP_ELEC_ADD_HURT.to_percentage_symbol()
    }
    
    # write character stats
    y_pos = 770
    xpos = 230
    for key, value in texts.items():
        text = key+' - '+str(value)
        draw.text((xpos, y_pos), text, (0, 0, 0), font=font)
        y_pos += 110
        
    # draw weapon icon
    weapon = character.equipments[-1]
    
    path = f'resources/images/weapon/{weapon.id}.png'
    try:
        icon = Image.open(path)
        icon = icon.convert('RGBA')
    except FileNotFoundError:
        async with session.get(weapon.detail.icon.url) as r:
            bytes_obj = BytesIO(await r.read())
        icon = Image.open(bytes_obj)
        icon = icon.convert('RGBA')
        icon.save(path, 'PNG')

    icon.thumbnail((200, 200))
    card.paste(icon, (968, 813), icon)
    
    # write weapon refinement text
    draw.text((956, 736), f"R{weapon.refinement}", font=font, fill='#212121')

    # write weapon name
    draw.text((1220, 785), weapon.detail.name, fill='#212121', font=font)

    # draw weapon mainstat icon
    mainstat = weapon.detail.mainstats
    fight_prop = Image.open(
        f'resources/images/fight_props/{mainstat.prop_id}.png')
    fight_prop.thumbnail((50, 50))
    card.paste(fight_prop, (1220, 890), fight_prop)

    # write weapon mainstat text
    draw.text(
        (1300, 875), f"{mainstat.value}{'%' if mainstat.type == DigitType.PERCENT else ''}", fill='#212121', font=font)

    # draw weapon substat icon
    if len(weapon.detail.substats) != 0:
        substat = weapon.detail.substats[0]
        fight_prop = Image.open(
            f'resources/images/fight_props/{substat.prop_id}.png')
        fight_prop.thumbnail((50, 50))
        card.paste(fight_prop, (1450, 890), fight_prop)
    
        # write weapon substat text
        draw.text(
            (1520, 875), f"{substat.value}{'%' if substat.type == DigitType.PERCENT else ''}", fill='#212121', font=font)

    # write weapon level text
    draw.text((1220, 960), f'Lvl. {weapon.level}', font=font, fill='#212121')

    # write character constellation text
    draw.text(
        (956, 1084), f'C{character.constellations_unlocked}', font=font, fill='#212121')

    # write talent levels
    x_pos = 1132
    y_pos = 1180
    for index, talent in enumerate(character.skills):
        if (character.id == 10000002 or character.id == 10000041) and index == 2:
            continue
        draw.text((x_pos, y_pos),
                  f'Lvl. {talent.level}', font=font, fill='#212121')
        y_pos += 165

    # artifacts
    x_pos = 1860
    y_pos = 111
    substat_x_pos = 2072
    substat_y_pos = 138
    font = ImageFont.truetype(f'resources/fonts/{font_family}', 44)
    for artifact in filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments):
        
        # draw artifact icons
        path = f'resources/images/artifact/{artifact.id}.png'
        try:
            icon = Image.open(path)
            icon = icon.convert('RGBA')
        except FileNotFoundError:
            async with session.get(artifact.detail.icon.url) as r:
                bytes_obj = BytesIO(await r.read())
            icon = Image.open(bytes_obj)
            icon = icon.convert('RGBA')
            icon.save(path, 'PNG')

        icon.thumbnail((180, 180))
        card.paste(icon, (x_pos, y_pos), icon)

        # write artifact level
        draw.text((x_pos+560, y_pos-66),
                  f'+{artifact.level}', font=font, fill='#212121')
        
        # draw artifact mainstat icon
        mainstat = artifact.detail.mainstats
        fight_prop = Image.open(
            f'resources/images/fight_props/{mainstat.prop_id}.png')
        fight_prop.thumbnail((45, 45))
        card.paste(fight_prop, (x_pos+550+105, y_pos-53), fight_prop)
        
        # write artifact mainstat text
        draw.text((x_pos+550+170, y_pos-66), f"{mainstat.value}{'%' if mainstat.type == DigitType.PERCENT else ''}", fill='#212121', font=font)

        # atifact substats
        num = 1
        for substat in artifact.detail.substats:
            if num == 3:
                substat_y_pos += 85
                substat_x_pos = 2072
                
            # draw substat icons
            fight_prop = Image.open(
                f'resources/images/fight_props/{substat.prop_id}.png')
            fight_prop.thumbnail((45, 45))
            card.paste(fight_prop, (substat_x_pos, substat_y_pos), fight_prop)
            
            # write substat text
            draw.text((substat_x_pos+70, substat_y_pos-15), f"{substat.value}{'%' if substat.type == DigitType.PERCENT else ''}", fill='#212121', font=font)
            substat_x_pos += 288
            num += 1
            
        substat_x_pos = 2072
        substat_y_pos += 250

        y_pos += 333
        
    card = card.convert('RGB')
    fp = BytesIO()
    card.save(fp, 'JPEG', optimize=True, quality=40)
    
    return fp