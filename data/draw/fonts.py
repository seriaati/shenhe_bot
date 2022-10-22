from typing import Literal


FONTS = {
    "de": {"extension": "ttf", "name": "NotoSans"},
    "en-US": {"extension": "ttf", "name": "NotoSans"},
    "es-ES": {"extension": "ttf", "name": "NotoSans"},
    "fr": {"extension": "ttf", "name": "NotoSans"},
    "ja": {"extension": "otf", "name": "NotoSansJP"},
    "ko": {"extension": "otf", "name": "NotoSansKR"},
    "pt-BR": {"extension": "ttf", "name": "NotoSans"},
    "ru": {"extension": "ttf", "name": "NotoSans"},
    "th": {"extension": "ttf", "name": "NotoSansThai"},
    "vi": {"extension": "ttf", "name": "NotoSans"},
    "zh-CN": {"extension": "otf", "name": "NotoSansSC"},
    "zh-TW": {"extension": "otf", "name": "NotoSansTC"},
}


def get_font(
    locale, variation: Literal["Bold", "Light", "Thin", "Black", "Medium"] = "Regular"
) -> str:
    path = "resources/fonts/"
    return (
        path
        + FONTS.get(str(locale), f"NotoSans")["name"]
        + "-"
        + variation
        + "."
        + FONTS.get(str(locale), "ttf")["extension"]
    )
