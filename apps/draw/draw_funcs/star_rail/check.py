from io import BytesIO

from genshin.models import StarRailNote
from PIL import Image, ImageDraw

from apps.text_map import text_map
from utils.draw import get_cache, get_font, seconds_to_hour_minute


def draw_check_card(notes: StarRailNote, dark_mode: bool, lang: str) -> BytesIO:
    path = "dark" if dark_mode else "light"
    primary_text = "#FFFFFF" if dark_mode else "#212121"
    expeds = notes.expeditions
    color = "#191919" if dark_mode else "#F0F3F6"
    height = (152 + len(expeds) * 88) * 2
    im = Image.new("RGBA", (646, height), color)

    stamina = Image.open(f"yelan/star_rail/check/{path}/stamina.png")
    draw = ImageDraw.Draw(stamina)
    current_stamina = notes.current_stamina
    max_stamina = notes.max_stamina
    font = get_font(lang, 60)
    draw.text(
        (564, 126),
        f"/{max_stamina}",
        font=font,
        fill=primary_text,
        anchor="rs",
    )
    text_length = draw.textlength(f"/{max_stamina}", font=font)
    font = get_font(lang, 80, "Medium")
    draw.text(
        (564 - text_length, 126),
        str(current_stamina),
        font=font,
        fill=primary_text,
        anchor="rs",
    )

    font = get_font(lang, 40)
    recover_time = notes.stamina_recover_time.total_seconds()
    text = "-" if recover_time == 0 else seconds_to_hour_minute(recover_time)
    draw.text((564, 180), text, font=font, fill=primary_text, anchor="rs")
    text_left_pos = 564 - draw.textlength(text, font=font)
    hour_glass = Image.open(f"yelan/star_rail/check/{path}/hour_glass.png")
    stamina.paste(hour_glass, (round(text_left_pos) - 40, 150), hour_glass)
    im.paste(stamina, (4, 24), stamina)

    for i, e in enumerate(expeds):
        exped = Image.open(f"yelan/star_rail/check/{path}/exped.png")
        draw = ImageDraw.Draw(exped)
        for j, a in enumerate(e.avatars):
            avatar = get_cache(a).resize((80, 80))
            exped.paste(avatar, (40 + j * 94, 28), avatar)
        remaining_time = e.remaining_time.total_seconds()
        text = (
            text_map.get(695, lang)
            if remaining_time == 0
            else seconds_to_hour_minute(remaining_time)
        )
        font = get_font(lang, 48)
        draw.text(
            (426, 68),
            text,
            font=font,
            fill=primary_text,
            anchor="mm",
        )
        im.paste(exped, (30, 304 + 176 * i), exped)

    fp = BytesIO()
    im.save(fp, format="WEBP", loseless=True)
    return fp
