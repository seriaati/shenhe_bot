from typing import Any, Dict, List

import aiohttp

BASE_URL = "https://genshin-db-api.vercel.app/api/{folder}?query=names&matchCategories=true&verboseCategories=true"

FOLDERS = [
    "tcgactioncards",
    "tcgcharactercards",
    "tcgsummons",
    "tcgcardbacks",
    "tcgcardboxes",
    "tcgstatuseffects",
]

LANGUAGE_URL = "https://genshin-db-api.vercel.app/api/languages"


async def fetch_cards(
    session: aiohttp.ClientSession,
) -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = {}

    async with session.get(LANGUAGE_URL) as resp:
        languages = await resp.json()

    for lang in languages:
        if lang not in result:
            result[lang] = []

        for folder in FOLDERS:
            async with session.get(
                BASE_URL.format(folder=folder) + f"&resultLanguage={lang}"
            ) as resp:
                cards: List[Dict[str, Any]] = await resp.json()
                for card in cards:
                    card["cardType"] = folder
                    result[lang].append(card)

    return result
