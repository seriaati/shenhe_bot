import io
from typing import Optional

import discord
import genshin
from PIL import Image, ImageDraw

import asset
from apps.draw.utility import get_font, human_format
from apps.genshin.utils import convert_ar_to_wl, convert_wl_to_mora
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_month_name


def card(
    diary: genshin.models.Diary,
    user: genshin.models.PartialGenshinUserStats,
    locale: discord.Locale | str,
    month: int,
    dark_mode: bool,
    plot_io: Optional[io.BytesIO],
) -> io.BytesIO:
    im = Image.open(
        f"yelan/templates/diary/[{'light' if not dark_mode else 'dark'}] Diary.png"
    )
    draw = ImageDraw.Draw(im)

    font = get_font(locale, 43, "Bold")
    fill = asset.primary_text if not dark_mode else asset.white
    draw.text(
        (52, 45),
        f"{text_map.get(69, locale)} • {get_month_name(month, locale)}",
        font=font,
        fill=fill,
    )

    mora_count = convert_wl_to_mora(convert_ar_to_wl(user.info.level))
    data = [
        {diary.data.current_primogems: 663},
        {diary.data.current_primogems // 160: 664},
        {diary.data.current_mora: 665},
        {diary.data.current_mora // mora_count: 666},
    ]

    offset = (202, 162)
    col = 0
    for d in data:
        key = list(d.keys())[0]
        value = list(d.values())[0]
        col += 1
        if col == 1:
            key = f"{key:,}"
        elif col == 3:
            key = human_format(key)
        else:
            pass
        font = get_font(locale, 36)
        fill = asset.primary_text if not dark_mode else asset.white
        draw.text(offset, str(key), font=font, fill=fill)
        font = get_font(locale, 24)
        fill = asset.secondary_text if not dark_mode else asset.white
        draw.text(
            (offset[0], offset[1] + 55),
            text_map.get(value, locale),
            font=font,
            fill=fill,
        )
        offset = (offset[0] + 465, offset[1])

    x = [cat.name for cat in diary.data.categories]
    y = [val.amount for val in diary.data.categories]

    if plot_io is not None:
        plot = Image.open(plot_io)
        ratio = 550 / plot.width
        plot = plot.resize((550, int(plot.height * ratio)))
        im.paste(plot, (80, 391), plot)

    font = get_font(locale, 24)
    fill = asset.primary_text if not dark_mode else asset.white
    offset = (712, 425)
    for index, category in enumerate(x):
        draw.text(offset, f"{category} ({y[index]})", font=font, fill=fill)
        offset = (offset[0], offset[1] + 54)

    font = get_font(locale, 36, "Bold")
    draw.text((1171, 363), text_map.get(667, locale), font=font, fill=fill)

    font = get_font(locale, 34)
    draw.text((1296, 461), text_map.get(668, locale), font=font, fill=fill)
    draw.text((1296, 598), text_map.get(669, locale), font=font, fill=fill)

    font = get_font(locale, 25)
    fill = "#3D3D3D" if not dark_mode else asset.white
    draw.text(
        (1296, 511),
        f"{diary.data.last_primogems:,} > {diary.data.current_primogems:,}",
        font=font,
        fill=fill,
    )
    draw.text(
        (1296, 648),
        f"{human_format(diary.data.last_mora)} > {human_format(diary.data.current_mora)}",
        font=font,
        fill=fill,
    )

    font = get_font(locale, 36, "Medium")
    rates = [diary.data.primogems_rate, diary.data.mora_rate]
    offset = (1722, 486)
    for rate in rates:
        if rate > 200:
            continue
        draw.text(
            offset,
            f"{'+' if rate >= 0 else ''}{rate}%",
            font=font,
            fill="#7CBB6D" if rate >= 0 else "#E97070",
        )
        offset = (offset[0], offset[1] + 137)

    im = im.convert("RGB")
    fp = io.BytesIO()
    im.save(fp, "JPEG", optimize=True, quality=40)
    return fp
