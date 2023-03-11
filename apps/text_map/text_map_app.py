import json
from typing import Dict, Optional

import discord
import yaml
from apps.text_map.convert_locale import to_ambr_top, to_paths, CROWDIN_FILE_PATHS
from utility.utils import log


class TextMap:
    def __init__(self):
        langs = CROWDIN_FILE_PATHS.values()
        self.text_maps = {}
        for lang in langs:
            try:
                with open(f"text_maps/langs/{lang}.yaml", "r", encoding="utf-8") as f:
                    self.text_maps[str(lang)] = yaml.full_load(f)
            except FileNotFoundError:
                self.text_maps[str(lang)] = {}
        try:
            with open("text_maps/avatar.json", "r", encoding="utf-8") as f:
                self.avatar = json.load(f)
        except FileNotFoundError:
            self.avatar = {}
        try:
            with open("text_maps/material.json", "r", encoding="utf-8") as f:
                self.material = json.load(f)
        except FileNotFoundError:
            self.material = {}
        try:
            with open("text_maps/weapon.json", "r", encoding="utf-8") as f:
                self.weapon = json.load(f)
        except FileNotFoundError:
            self.weapon = {}
        try:
            with open("text_maps/dailyDungeon.json", "r", encoding="utf-8") as f:
                self.dailyDungeon = json.load(f)
        except FileNotFoundError:
            self.dailyDungeon = {}
        try:
            with open("text_maps/item_name.json", "r", encoding="utf-8") as f:
                self.item_name_text_map = json.load(f)
        except FileNotFoundError:
            self.item_name_text_map = {}
        try:
            with open("text_maps/reliquary.json", "r", encoding="utf-8") as f:
                self.artifact = json.load(f)
        except FileNotFoundError:
            self.artifact = {}

    def get(
        self,
        map_hash: int,
        locale: discord.Locale | str = "en-US",
        user_locale: Optional[str] = None,
    ) -> str:
        locale = user_locale or locale
        path = to_paths(locale)
        lang_text_map: Dict[str, str] = self.text_maps[path]
        text = lang_text_map.get(str(map_hash), "")
        if not text:
            log.warning(
                f"[Text Map][{locale}][map_hash not found]: [map_hash]{map_hash}"
            )
            lang_text_map = self.text_maps["en-US"]
            text = lang_text_map.get(str(map_hash), "")
        return text

    def get_id_from_name(self, name: str) -> Optional[int]:
        result = self.item_name_text_map.get(name)
        if result is None:
            return None
        return int(result)

    def get_character_name(
        self,
        character_id: str,
        locale: discord.Locale | str,
        user_locale: Optional[str] = None,
    ) -> Optional[str]:
        avatar_text = self.avatar.get(str(character_id))
        if avatar_text is None:
            return None
        locale = user_locale or locale
        ambr_locale = to_ambr_top(str(locale))
        return avatar_text[str(ambr_locale)]

    def get_material_name(
        self,
        material_id: int,
        locale: discord.Locale | str,
        user_locale: Optional[str] = None,
    ) -> str | int:
        material_text = self.material.get(str(material_id))
        if material_text is None:
            if str(material_id).isdigit():
                log.warning(
                    f"[Exception][get_material_name][material_id not found]: [material_id]{material_id}"
                )
            return material_id
        locale = user_locale or locale
        ambr_locale = to_ambr_top(str(locale))
        return material_text[str(ambr_locale)]

    def get_material_id_with_name(self, material_name: str) -> str | int:
        for material_id, material_name_dict in self.material.items():
            for _, material_lang_name in material_name_dict.items():
                if material_lang_name == material_name:
                    return int(material_id)
        log.warning(
            f"[Exception][get_material_id_with_name][material_name not found]: [material_name]{material_name}"
        )
        return material_name

    def get_weapon_name(
        self,
        weapon_id: int,
        locale: discord.Locale | str,
        user_locale: Optional[str] = None,
    ) -> Optional[str]:
        avatarText = self.weapon.get(str(weapon_id))
        if avatarText is None:
            return None
        locale = user_locale or locale
        ambr_locale = to_ambr_top(str(locale))
        return avatarText[str(ambr_locale)]

    def get_domain_name(
        self,
        dungeon_id: int,
        locale: discord.Locale | str,
        user_locale: Optional[str] = None,
    ) -> str:
        dungeonText = self.dailyDungeon.get(str(dungeon_id))
        if dungeonText is None:
            return str(dungeon_id)
        locale = user_locale or locale
        ambr_locale = to_ambr_top(str(locale))
        return dungeonText.get(str(ambr_locale), str(dungeon_id))

    def get_artifact_name(
        self,
        artifact_id: int,
        locale: discord.Locale | str,
        user_locale: Optional[str] = None,
    ):
        artifact_text = self.artifact.get(str(artifact_id))
        if artifact_text is None:
            log.warning(
                f"[Exception][get_artifact_name][artifact_id not found]: [artifact_id]{artifact_id}"
            )
            return artifact_id
        locale = user_locale or locale
        ambr_locale = to_ambr_top(str(locale))
        return artifact_text[str(ambr_locale)]


# initialize the class first to load the text maps
text_map = TextMap()
