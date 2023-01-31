import io
from typing import List

from discord import Locale
from PIL import Image, ImageDraw

import asset
from apps.draw.utility import get_cache, get_font
from apps.text_map.text_map_app import text_map


def card(banner_image_urls: List[str], locale: Locale | str) -> io.BytesIO:
    im = Image.new("RGB", (2180, 1908))
    draw = ImageDraw.Draw(im)

    # draw titles
    font = get_font(locale, 64, "Bold")
    draw.text(
        (540, 81), text_map.get(744, locale), fill=asset.white, anchor="mm", font=font
    )
    draw.text(
        (1620, 81), text_map.get(745, locale), fill=asset.white, anchor="mm", font=font
    )

    # draw banners
    offset = (0, 161)
    padding = 74
    for i, url in enumerate(banner_image_urls):
        banner = get_cache(url)
        banner = banner.resize((1080, 533))
        im.paste(banner, offset)
        if i == 2:
            offset = (1080, 161)
        else:
            offset = (offset[0], offset[1] + banner.height + padding)

    fp = io.BytesIO()
    im.save(fp, format="JPEG", quality=100, optimize=True)
    return fp
