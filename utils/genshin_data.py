from typing import Dict

from apps.text_map import ENKA_LANGS


def get_text(text_map: Dict[str, Dict[str, str]], lang: str, text_id: int) -> str:
    genshin_db_lang = ENKA_LANGS.get(lang, "en").upper()
    return text_map[genshin_db_lang].get(str(text_id), "Unknown")
