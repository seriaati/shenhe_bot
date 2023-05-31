from typing import Dict, Union

from discord import Locale

from apps.text_map import to_enka


def get_text(
    text_map: Dict[str, Dict[str, str]], lang: Union[Locale, str], text_id: int
) -> str:
    lang = to_enka(lang).upper()
    return text_map[lang].get(str(text_id), "Unknown")
