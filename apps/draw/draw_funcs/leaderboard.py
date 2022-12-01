from PIL import Image, ImageDraw
from ambr.models import Character
from apps.draw.utility import circular_crop, get_cache, get_font, shorten_text
from apps.text_map.convert_locale import convert_langdetect
import discord
import asset
from apps.genshin.custom_model import AbyssLeaderboardUser
import langdetect
from apps.text_map.text_map_app import text_map

def l_user_card(
    dark_mode: bool,
    elevation: int,
    user_data: AbyssLeaderboardUser,
) -> Image.Image:
    im = Image.open(
        f"yelan/templates/leaderboard/[{'light' if not dark_mode else 'dark'}] elevation_{elevation}.png"
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
    if user_data.rank <= 3:
        draw.rounded_rectangle((0, 0, 1490, 170), 10, fill=rank_colors[user_data.rank])
    if user_data.current:
        draw.rounded_rectangle(
            (0, 0, 1490, 170),
            10,
            outline=asset.primary_text if not dark_mode else asset.white,
            width=2,
        )
    font = get_font("en-US", 80, "Bold")
    fill = asset.primary_text if not dark_mode else asset.white
    draw.text((63, 84), str(user_data.rank), font=font, fill=fill, anchor="mm")

    # draw character icon
    character_icon = get_cache(user_data.character.icon)
    character_icon = character_icon.resize((115, 115))
    character_icon = circular_crop(character_icon)
    im.paste(character_icon, (216, 27), character_icon)

    # write user name
    langdetect.DetectorFactory.seed = 0
    font = get_font(convert_langdetect(langdetect.detect(user_data.user_name)), 48, "Bold")
    text = shorten_text(user_data.user_name, 221, font)
    draw.text((350, 27), text, font=font, fill=fill)

    # write character info
    font = get_font("en-US", 36)
    fill = asset.secondary_text if not dark_mode else asset.white
    character = user_data.character
    draw.text(
        (350, 92),
        f"C{character.constellation}R{character.weapon.refinement} Lv.{character.level}",
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

    # write stars collected
    draw.text(
        (1317, 84), str(user_data.stars_collected), font=font, fill=fill, anchor="mm"
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