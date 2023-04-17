from typing import List, Union

import discord
from PIL import Image, ImageDraw

import dev.asset as asset
from ambr import Character
from apps.text_map import text_map
from dev.models import RunLeaderboardUser, SingleStrikeLeaderboardUser
from utils import (circular_crop, get_cache, get_font, global_write,
                   shorten_text)


def board(
    dark_mode: bool,
    users: Union[List[SingleStrikeLeaderboardUser], List[RunLeaderboardUser]],
    current_uid: int,
    title_hash: int,
    column_hashes: List[int],
    locale: discord.Locale | str,
) -> Image.Image:
    current_user = None
    user_above = None
    user_below = None
    for index, u in enumerate(users):
        user_above = users[index - 1] if index > 0 else None
        user_below = users[index + 1] if index < len(users) - 1 else None
        if u.uid == current_uid:
            current_user = u
            break

    l_type = 2 if current_user is not None and current_user.rank >= 10 else 1

    im: Image.Image = Image.open(
        f"yelan/templates/leaderboard/[{'dark' if dark_mode else 'light'}] leaderboard_{l_type}.png"
    )
    draw = ImageDraw.Draw(im)

    # draw the user cards
    offset = (63, 299)
    for u in users:
        if u.rank == 8 and l_type == 2:
            break
        if u.rank == 11 and l_type == 1:
            break

        current = u == current_user
        if isinstance(u, SingleStrikeLeaderboardUser):
            user_card = ss_user_card(dark_mode, u, current)
        else:
            user_card = run_user_card(dark_mode, u, current)
        im.paste(user_card, offset, user_card)
        offset = (offset[0], offset[1] + 220)

    if l_type == 2:
        offset = (63, 1958)
        users_to_draw = (user_above, current_user, user_below)
        for u in users_to_draw:
            if u is not None:
                current = u == current_user
                if isinstance(u, SingleStrikeLeaderboardUser):
                    user_card = ss_user_card(dark_mode, u, current)
                else:
                    user_card = run_user_card(dark_mode, u, current)
                im.paste(user_card, offset, user_card)
                offset = (offset[0], offset[1] + 220)

    # write title
    fill = asset.primary_text if not dark_mode else asset.white
    font = get_font(locale, 75, "Bold")
    draw.text((63, 36), text_map.get(title_hash, locale), fill=fill, font=font)

    # write column titles
    fill = asset.secondary_text if not dark_mode else asset.white
    font = get_font(locale, 36, "Bold")
    col_pos = (128, 460, 865, 1123, 1380)
    for index, c_hash in enumerate(column_hashes):
        draw.text(
            (col_pos[index], 220),
            text_map.get(c_hash, locale),
            fill=fill,
            font=font,
            anchor="mm",
        )

    return im


def default_user_card(dark_mode: bool, rank: int, current: bool) -> Image.Image:
    """Draw default leaderboard user card."""
    im = Image.open(
        f"yelan/templates/leaderboard/[{'light' if not dark_mode else 'dark'}] elevation_{2 if current else 1}.png"
    )
    draw = ImageDraw.Draw(im)

    # write rank text
    if dark_mode:
        rank_colors = {
            1: "#565445",
            2: "#594f43",
            3: "#574848",
        }
    else:
        rank_colors = {
            1: "#FFF6C4",
            2: "#FFDDB6",
            3: "#FFCACA",
        }
    if rank <= 3:
        draw.rounded_rectangle((0, 0, 1490, 170), 10, fill=rank_colors[rank])
    if current:
        draw.rounded_rectangle(
            (0, 0, 1490, 170),
            10,
            outline=asset.primary_text if not dark_mode else asset.white,
            width=2,
        )
    return im


def run_user_card(
    dark_mode: bool,
    user_data: RunLeaderboardUser,
    current: bool,
) -> Image.Image:
    """Draw runs taken leaderboard user card."""
    im = default_user_card(dark_mode, user_data.rank, current)
    draw = ImageDraw.Draw(im)

    # write rank text
    font = get_font("en-US", 80, "Bold")
    fill = asset.primary_text if not dark_mode else asset.white
    draw.text((66, 84), str(user_data.rank), font=font, fill=fill, anchor="mm")

    # draw character icon
    character_icon = get_cache(user_data.icon_url)
    character_icon = character_icon.resize((115, 115))
    character_icon = circular_crop(character_icon)
    im.paste(character_icon, (216, 27), character_icon)

    # write user name
    text = shorten_text(user_data.user_name, 580, font)
    global_write(draw, (350, 27), text, 48, fill, "Bold")

    # write player info
    font = get_font("en-US", 36)
    fill = asset.secondary_text if not dark_mode else asset.white
    draw.text(
        (350, 92),
        f"AR {user_data.level}",
        font=font,
        fill=fill,
    )

    # write win/runs
    font = get_font("en-US", 48, "Medium")
    fill = asset.primary_text if not dark_mode else asset.white
    draw.text(
        (800, 84), f"{user_data.wins_slash_runs}", font=font, fill=fill, anchor="mm"
    )

    # write win percentage
    draw.text(
        (1061, 84), user_data.win_percentage + "%", font=font, fill=fill, anchor="mm"
    )

    # write stars collected
    draw.text(
        (1317, 84), str(user_data.stars_collected), font=font, fill=fill, anchor="mm"
    )

    return im


def ss_user_card(
    dark_mode: bool, user_data: SingleStrikeLeaderboardUser, current: bool
) -> Image.Image:
    """Draw single strike leaderboard user card."""
    im = default_user_card(dark_mode, user_data.rank, current)
    draw = ImageDraw.Draw(im)

    # write rank text
    font = get_font("en-US", 80, "Bold")
    fill = asset.primary_text if not dark_mode else asset.white
    draw.text((66, 84), str(user_data.rank), font=font, fill=fill, anchor="mm")

    # draw character icon
    character_icon = get_cache(user_data.character.icon)
    character_icon = character_icon.resize((115, 115))
    character_icon = circular_crop(character_icon)
    im.paste(character_icon, (216, 27), character_icon)

    # write user name
    text = shorten_text(user_data.user_name, 580, font)
    global_write(draw, (350, 27), text, 48, fill, "Bold")

    # write character info
    font = get_font("en-US", 36)
    fill = asset.secondary_text if not dark_mode else asset.white
    character = user_data.character
    draw.text(
        (350, 92),
        f"C{character.constellation}R{character.refinement} Lv.{character.level}",
        font=font,
        fill=fill,
    )

    # write single strike
    font = get_font("en-US", 48, "Medium")
    fill = asset.primary_text if not dark_mode else asset.white
    draw.text(
        (800, 84), f"{user_data.single_strike:,}", font=font, fill=fill, anchor="mm"
    )

    # write floor
    draw.text((1061, 84), user_data.floor, font=font, fill=fill, anchor="mm")

    # write abyss phase
    draw.text(
        (1317, 84), str(user_data.season), font=font, fill=fill, anchor="mm"
    )

    return im


def c_usage_card(
    character: Character,
    usage_num: int,
    percentage: float,
    dark_mode: bool,
    locale: str | discord.Locale,
) -> Image.Image:
    # card
    im = Image.open(
        f"yelan/templates/character/[{'light' if not dark_mode else 'dark'}] card.png"
    )
    draw = ImageDraw.Draw(im)

    # character icon
    icon = get_cache(character.icon)
    icon = circular_crop(icon)
    icon = icon.resize((95, 95))
    im.paste(icon, (17, 23), icon)

    # character name
    font = get_font(locale, 40, "Medium")
    fill = asset.primary_text if not dark_mode else asset.white
    text = shorten_text(character.name, 321, font)
    draw.text((127, 23), text, font=font, fill=fill)

    # number of usage
    font = get_font(locale, 25)
    fill = asset.secondary_text if not dark_mode else asset.white
    draw.text(
        (127, 77),
        text_map.get(612, locale).format(num=usage_num),
        font=font,
        fill=fill,
    )

    # percentage
    font = get_font(locale, 36, "Medium")
    fill = asset.primary_text if not dark_mode else asset.white
    text = f"{percentage:.1f}%"
    draw.text((620 - font.getlength(text), 46), text, font=font, fill=fill)

    return im
