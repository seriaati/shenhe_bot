from typing import Dict

import aiohttp
from discord import Locale
from ambr.models import Character, Domain, Weapon
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from data.draw.fonts import FONTS


def draw_domain_card(domain: Domain, locale: Locale | str) -> Image:
    text = domain.name
    font_family = FONTS.get(str(locale))

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
