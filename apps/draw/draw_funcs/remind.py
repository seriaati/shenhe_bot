import io
from typing import List

import discord
from PIL import Image, ImageDraw

import asset
from ambr.models import Material
from apps.draw.utility import get_cache, get_font
from apps.text_map.convert_locale import to_ambr_top


def card(
    materials: List[Material],
    locale: discord.Locale | str,
    dark_mode: bool,
    type: str,
) -> io.BytesIO:
    font = get_font(locale, 50)
    fill = asset.primary_text if not dark_mode else asset.white

    locale = to_ambr_top(locale)
    reminder_card: Image.Image = Image.open(
        f"yelan/templates/remind/[{'dark' if dark_mode else 'light'}] {'Talent' if type =='talent_notification' else 'Weapon'} Notification Card.png"
    )
    icon_x, icon_y = 100, 100
    count = 1

    for mat in materials:
        icon = get_cache(mat.icon)
        icon.thumbnail((120, 120))
        if count == 2:
            icon_y += 210
        elif count == 3:
            icon_y += 220
        elif count == 4:
            icon_y += 220
            
        reminder_card.paste(icon, (icon_x, icon_y), icon)
        count += 1

        draw = ImageDraw.Draw(reminder_card)
        draw.text(
            (icon_x + 670, icon_y + 55), mat.name, fill=fill, font=font, anchor="mm"
        )
    reminder_card = reminder_card.convert("RGB")
    fp = io.BytesIO()
    reminder_card.save(fp, "JPEG", optimize=True)
    return fp