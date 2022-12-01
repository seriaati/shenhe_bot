import io
from typing import Dict

import discord
from PIL import Image, ImageDraw

import asset
from ambr.models import Character, Domain, Weapon
from apps.draw.utility import dynamic_font_size, get_cache, get_font
from apps.genshin.utils import get_domain_title


def draw_domain_card(
    domain: Domain,
    locale: discord.Locale | str,
    items: Dict[int, Character | Weapon],
) -> io.BytesIO:
    # get domain template image
    background_paths = ["", "Mondstat", "Liyue", "Inazuma", "Sumeru"]
    domain_card: Image.Image = Image.open(
        f"yelan/templates/farm/{background_paths[domain.city.id]} Farm.png"
    )

    # draw the domain text
    text = get_domain_title(domain, locale)
    font = dynamic_font_size(text, 30, 90, 1198, get_font(locale, 50))
    draw = ImageDraw.Draw(domain_card)
    draw.text((987, 139), text, fill=asset.primary_text, font=font, anchor="mm")

    # find the highest rarity item in the domain and draw it
    highest_rarity = 1
    highest_reward = None
    for reward in domain.rewards:
        if reward.rarity > highest_rarity:
            highest_rarity = reward.rarity
            highest_reward = reward
    if highest_reward is not None:
        icon = get_cache(highest_reward.icon)
        icon.thumbnail((160, 160))
        domain_card.paste(icon, (87, 60), icon)

    count = 1
    offset = (150, 340)
    for item in items.values():
        icon = get_cache(item.icon)
        icon.thumbnail((180, 180))
        domain_card.paste(icon, offset, icon)

        # is the character a traveler?
        if "10000007" in str(item.id) and isinstance(item, Character):
            # draw the element of the traveler
            element_icon: Image.Image = Image.open(
                f"yelan/templates/elements/{item.element.lower()}.png"
            )
            element_icon.thumbnail((64, 64))
            domain_card.paste(
                element_icon, (offset[0] + 140, offset[1] + 120), element_icon
            )

        # change offset
        offset = (offset[0] + 400, offset[1])

        # if four in a row, move to next row
        if count % 4 == 0:
            offset = (150, offset[1] + 250)
        offset = tuple(offset)

        count += 1

    domain_card = domain_card.convert("RGB")
    fp = io.BytesIO()
    domain_card.save(fp, "JPEG", optimize=True, quality=40)
    return fp
