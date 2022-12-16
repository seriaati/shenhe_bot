import json
from pathlib import Path
import aiohttp

BASE_URL = (
    "https://sg-hk4e-api-static.hoyoverse.com/event/e20221205drawcard/card_config?lang="
)

# English, Simplified Chinese, Traditional Chinese, Japanese, Korean, Indonesian, Thai, Vietnamese, German, French, Portuguese, Spanish, Russian.
ALL_LANGUAGES = [
    "en-us",
    "zh-cn",
    "zh-tw",
    "ja-jp",
    "ko-kr",
    "id-id",
    "th-th",
    "vi-vn",
    "de-de",
    "fr-fr",
    "pt-pt",
    "es-es",
    "ru-ru",
]


async def fetch_cards(session: aiohttp.ClientSession):
    i18n_data = {}

    for lang in ALL_LANGUAGES:
        async with session.get(BASE_URL + lang) as resp:
            card_config = await resp.read()
        assert len(card_config) > 0

        data = json.loads(card_config.decode("utf-8"))["data"]
        assert data["role_card_infos"][0]["name"]

        i18n_data[lang] = data

    return i18n_data


def json_traverse(data, path=""):
    """
    Traverse all nodes in the JSON data and yield them.
    """

    if isinstance(data, dict):
        for key, value in sorted(data.items()):
            if isinstance(value, str):
                yield f"{path}.{key}", value
            yield from json_traverse(value, f"{path}.{key}")
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            yield from json_traverse(item, f"{path}.{idx}")


def process_i18n(data):
    i18n = {}

    for lang in ALL_LANGUAGES:
        i18n[lang] = {}

        for (_, i), (_, j) in zip(
            json_traverse(data["en-us"]), json_traverse(data[lang])
        ):
            if i != j:
                if i in i18n[lang] and i18n[lang][i] != j:
                    raise ValueError(
                        f"Duplicate translation for {i}: {i18n[lang][i]} and {j}"
                    )

                i18n[lang][i] = j

    return data["en-us"], i18n