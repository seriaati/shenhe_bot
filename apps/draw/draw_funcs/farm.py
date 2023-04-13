import io
from typing import List

from discord import Locale
from PIL import Image, ImageDraw

from apps.draw.utils import get_cache, get_font
from apps.genshin.utility import get_domain_title
from dev.models import FarmData


def draw_domain_card(
    farm_data: List[FarmData],
    locale: Locale | str,
    dark_mode: bool,
) -> io.BytesIO:
    app_mode = "dark" if dark_mode else "light"
    city_id_dict = {
        1: "mondstat",
        2: "liyue",
        3: "inazuma",
        4: "sumeru",
    }
    basic_cards: List[Image.Image] = []

    for data in farm_data:
        basic_card = Image.open(f"yelan/templates/farm/[{app_mode}] basic_card.png")

        item_per_row = 9
        height_per_row = 199
        new_height = basic_card.height + height_per_row * (
            len(data.characters + data.weapons) // (item_per_row + 1)
        )
        basic_card = basic_card.resize((basic_card.width, new_height))

        lid = Image.open(
            f"yelan/templates/farm/[light] {city_id_dict.get(data.domain.city.id, 'unknown')}.png"
        )
        basic_card.paste(lid, (0, 0), lid)

        font = get_font(locale, 48, "Medium")
        draw = ImageDraw.Draw(basic_card)
        draw.text(
            (32, 23),
            get_domain_title(data.domain, locale),
            font=font,
            fill="#FFFFFF",
        )

        for index, reward in enumerate(data.domain.rewards):
            if len(str(reward.id)) == 6:
                icon = get_cache(reward.icon)
                icon = icon.resize((82, 82))
                basic_card.paste(icon, (1286 + (-85) * index, 17), icon)

        starting_pos = (50, 154)
        dist_between_items = 148
        next_row_y_up = 152
        for index, item in enumerate(data.characters + data.weapons):
            if index % item_per_row == 0 and index != 0:
                starting_pos = (50, starting_pos[1] + next_row_y_up)
            icon = get_cache(item.icon)
            icon = icon.resize((114, 114))
            basic_card.paste(icon, starting_pos, icon)
            starting_pos = (starting_pos[0] + dist_between_items, starting_pos[1])

        basic_cards.append(basic_card)

    background_color = "#F2F2F2" if not dark_mode else "#323232"
    top_bot_margin = 44
    right_left_margin = 56
    x_padding_between_cards = 80
    y_padding_between_cards = 60
    card_width_offset = -124
    card_per_column = 4
    col_num = (
        len(basic_cards) // card_per_column + 1
        if len(basic_cards) % card_per_column != 0
        else len(basic_cards) // card_per_column
    )

    background_width = (
        right_left_margin * 2
        + (basic_cards[0].width + card_width_offset) * col_num
        + x_padding_between_cards * (col_num - 1)
    )

    background_height = top_bot_margin * 2
    card_heights = [card.height for card in basic_cards]
    max_card_height = max(card_heights)
    max_card_height_col = card_heights.index(max_card_height) // 4
    for card in basic_cards[max_card_height_col * 4 : (max_card_height_col + 1) * 4]:
        item_row_num = (card.height - 437) // 199 + 1
        card_height_offset = -114 + (-55 * (item_row_num - 1))
        background_height += card.height + card_height_offset + y_padding_between_cards

    background = Image.new(
        "RGB", (background_width, background_height), background_color  # type: ignore
    )

    x = right_left_margin
    y = top_bot_margin
    for index, card in enumerate(basic_cards):
        item_row_num = (card.height - 437) // 199 + 1
        card_height_offset = -114 + (-55 * (item_row_num - 1))
        if index % card_per_column == 0 and index != 0:
            x += (
                basic_cards[index - 1].width
                + card_width_offset
                + x_padding_between_cards
            )
            y = top_bot_margin
        background.paste(card, (x, y), card)
        y += card.height + card_height_offset + y_padding_between_cards

    fp = io.BytesIO()
    background.save(fp, format="JPEG", quality=100, optimize=True)
    return fp
