import io
from typing import List

from discord import Locale
from PIL import Image, ImageDraw

import dev.asset as asset
from apps.text_map import text_map
from utils import get_cache, get_font


def card(banner_image_urls: List[str], lang: Locale | str) -> io.BytesIO:
    im = Image.new("RGBA", (2180 if len(banner_image_urls) > 3 else 1080, 1908))
    draw = ImageDraw.Draw(im)

    # draw titles
    font = get_font(lang, 64, "Bold")
    draw.text(
        (540, 81), text_map.get(744, lang), fill=asset.white, anchor="mm", font=font
    )
    if len(banner_image_urls) > 3:
        draw.text(
            (1620, 81),
            text_map.get(745, lang),
            fill=asset.white,
            anchor="mm",
            font=font,
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
    im.save(fp, format="PNG", optimize=True)
    return fp
