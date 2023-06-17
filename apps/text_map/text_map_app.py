import json
from typing import Any, Dict, Optional, Union

import discord
import yaml

from .convert_locale import CROWDIN_LANGS, to_ambr_top


class TextMap:
    def __init__(self):
        self.langs = CROWDIN_LANGS.values()
        self.lang_maps: Dict[str, Dict[str, str]] = {}

        self.artifact: Dict[str, Dict[str, str]] = {}
        self.character: Dict[str, Dict[str, str]] = {}
        self.material: Dict[str, Dict[str, str]] = {}
        self.weapon: Dict[str, Dict[str, str]] = {}
        self.domain: Dict[str, Dict[str, str]] = {}
        self.item_name: Dict[str, str] = {}

        self.load()

    def load(self):
        for lang in self.langs:
            self.lang_maps[lang] = self._open_file(f"text_maps/langs/{lang}.yaml")

        self.character = self._open_file("text_maps/avatar.json")
        self.material = self._open_file("text_maps/material.json")
        self.weapon = self._open_file("text_maps/weapon.json")
        self.domain = self._open_file("text_maps/dailyDungeon.json")
        self.item_name = self._open_file("text_maps/item_name.json")
        self.artifact = self._open_file("text_maps/reliquary.json")

    def get(
        self,
        map_hash: int,
        lang: Union[discord.Locale, str] = "en-US",
        user_locale: Optional[str] = None,
    ) -> str:
        lang = str(user_locale or lang)
        path = CROWDIN_LANGS.get(lang, "en-US")
        lang_text_map = self.lang_maps[path]
        text = lang_text_map.get(str(map_hash), "")
        if not text:
            lang_text_map = self.lang_maps["en-US"]
            text = lang_text_map.get(str(map_hash), "")
        return text

    def get_id_from_name(self, name: str) -> Optional[int]:
        result = self.item_name.get(name)
        if result is None:
            return None
        return int(result)

    def get_character_name(
        self,
        character_id: str,
        lang: discord.Locale | str,
        user_locale: Optional[str] = None,
    ) -> Optional[str]:
        avatar_text = self.character.get(str(character_id))
        if avatar_text is None:
            return None
        lang = user_locale or lang
        ambr_locale = to_ambr_top(str(lang))
        return avatar_text[str(ambr_locale)]

    def get_material_name(
        self,
        material_id: int,
        lang: discord.Locale | str,
        user_locale: Optional[str] = None,
    ) -> str | int:
        material_text = self.material.get(str(material_id))
        if material_text is None:
            return material_id
        lang = user_locale or lang
        ambr_locale = to_ambr_top(str(lang))
        return material_text[str(ambr_locale)]

    def get_weapon_name(
        self,
        weapon_id: int,
        lang: discord.Locale | str,
        user_locale: Optional[str] = None,
    ) -> Optional[str]:
        avatar_text = self.weapon.get(str(weapon_id))
        if avatar_text is None:
            return None
        lang = user_locale or lang
        ambr_locale = to_ambr_top(str(lang))
        return avatar_text[str(ambr_locale)]

    def get_domain_name(
        self,
        dungeon_id: int,
        lang: discord.Locale | str,
        user_locale: Optional[str] = None,
    ) -> str:
        dungeon_text = self.domain.get(str(dungeon_id))
        if dungeon_text is None:
            return str(dungeon_id)
        lang = user_locale or lang
        ambr_locale = to_ambr_top(str(lang))
        return dungeon_text.get(str(ambr_locale), str(dungeon_id))

    def get_artifact_name(
        self,
        artifact_id: int,
        lang: discord.Locale | str,
        user_locale: Optional[str] = None,
    ):
        artifact_text = self.artifact.get(str(artifact_id))
        if artifact_text is None:
            return artifact_id
        lang = user_locale or lang
        ambr_locale = to_ambr_top(str(lang))
        return artifact_text[str(ambr_locale)]

    @staticmethod
    def _open_file(path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                if path.endswith(".json"):
                    return json.load(f)
                if path.endswith(".yaml"):
                    return yaml.full_load(f)  # type: ignore
                return {}
        except FileNotFoundError:
            return {}


# initialize the class first to load the text maps
text_map = TextMap()
