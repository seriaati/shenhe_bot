import io
from typing import Dict, List

import genshin
from PIL import Image, ImageDraw

import dev.asset as asset
from dev.models import DynamicBackgroundInput
from utils import draw_dynamic_background, get_cache, get_font


def character_card(
    characters: List[genshin.models.Character],
    talents: Dict[str, str],
    pc_icon: Dict[str, str],
    dark_mode: bool,
) -> io.BytesIO:
    c_cards: Dict[str, Image.Image] = {}
    for character in characters:
        draw_small_chara_card(talents, dark_mode, c_cards, character)

    first_card = list(c_cards.values())[0]
    db_input = DynamicBackgroundInput(
        top_padding=35,
        bottom_padding=5,
        left_padding=5,
        right_padding=5,
        card_width=first_card.width,
        card_height=first_card.height,
        card_x_padding=5,
        card_y_padding=35,
        card_num=len(c_cards),
        background_color="#212121" if dark_mode else asset.light_theme_background,
        draw_title=False,
    )
    background, max_card_num = draw_dynamic_background(db_input)
    for index, card in enumerate(c_cards.values()):
        x = (index // max_card_num) * (
            db_input.card_width + db_input.card_x_padding
        ) + db_input.left_padding
        y = 0
        if isinstance(db_input.top_padding, int):
            y = (index % max_card_num) * (
                db_input.card_height + db_input.card_y_padding
            ) + db_input.top_padding
        background.paste(card, (x, y), card)
        character_id = list(c_cards.keys())[index]
        pc_icon_url = pc_icon.get(character_id)
        if pc_icon_url:
            icon = get_cache(pc_icon_url)
            icon = icon.resize((214, 214))
            background.paste(icon, (x, y - 29), icon)

    fp = io.BytesIO()
    background.save(fp, format="PNG", optimize=True)
    return fp


def draw_small_chara_card(talents, dark_mode, c_cards, character):
    im: Image.Image = Image.open(
        f"yelan/templates/character/{'dark' if dark_mode else 'light'}_{character.element}.png"
    )
    draw = ImageDraw.Draw(im)
    font = get_font("en-US", 31)
    color = (255, 255, 255, 204) if dark_mode else (0, 0, 0, 204)
    text = f"C{character.constellation}R{character.weapon.refinement}"
    draw.text((227, 32), text, font=font, fill=color)
    text = f"Lv.{character.level}"
    draw.text((227, 72), text, font=font, fill=color)

    font = get_font("en-US", 18)
    friend = str(character.friendship)
    draw.text((287, 154), friend, font=font, fill=color, anchor="mm")
    text = talents.get(str(character.id), "?/?/?")
    draw.text((368, 154), text, font=font, fill=color, anchor="mm")

    size = 4
    x_start = 287 + font.getlength(friend) // 2
    x_end = 360 - font.getlength(text) // 2
    x_avg = (x_start + x_end) // 2
    y_start = 156 - size
    draw.ellipse((x_avg, y_start, x_avg + size, y_start + size), fill=color)

    weapon_icon = get_cache(character.weapon.icon)
    weapon_icon = weapon_icon.resize((84, 84))
    im.paste(weapon_icon, (332, 30), weapon_icon)

    c_cards[str(character.id)] = im
