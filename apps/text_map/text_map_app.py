import json
import typing

import yaml
from discord import Locale

from dev.enum import LangType, TextMapType

from .convert_locale import CROWDIN_FILE_PATHS, to_ambr_top, to_paths


class TextMap:
    def __init__(self):
        self.langs = CROWDIN_FILE_PATHS.values()
        self.lang_maps = {}

        self.artifact = {}
        self.avatar = {}
        self.material = {}
        self.weapon = {}
        self.domain = {}
        self.item_name = {}

        self.load()

    def load(self):
        for lang in LangType:
            self.lang_maps[str(lang)] = self._open_file(TextMapType.LANG, lang)

        self.avatar = self._open_file(TextMapType.CHARACTER)
        self.material = self._open_file(TextMapType.MATERIAL)
        self.weapon = self._open_file(TextMapType.WEAPON)
        self.domain = self._open_file(TextMapType.DOMAIN)
        self.item_name = self._open_file(TextMapType.ITEM_NAME)
        self.artifact = self._open_file(TextMapType.ARTIFACT)

    def get(
        self,
        map_hash: int,
        locale: typing.Union[Locale, str] = "en-US",
        user_locale: typing.Optional[str] = None,
    ) -> str:
        locale = user_locale or locale
        path = to_paths(locale)
        lang_text_map: typing.Dict[str, str] = self.lang_maps[path]
        text = lang_text_map.get(str(map_hash), "")
        if not text:
            lang_text_map = self.lang_maps["en-US"]
            text = lang_text_map.get(str(map_hash), "")
        return text

    def get_id_from_name(self, name: str) -> typing.Optional[int]:
        result = self.item_name.get(name)
        if result is None:
            return None
        return int(result)

    def get_character_name(
        self,
        character_id: str,
        locale: typing.Union[Locale, str],
        user_locale: typing.Optional[str] = None,
    ) -> typing.Optional[str]:
        avatar_text = self.avatar.get(str(character_id))
        if avatar_text is None:
            return None
        locale = user_locale or locale
        ambr_locale = to_ambr_top(str(locale))
        return avatar_text[str(ambr_locale)]

    def get_material_name(
        self,
        material_id: int,
        locale: typing.Union[Locale, str],
        user_locale: typing.Optional[str] = None,
    ) -> str | int:
        material_text = self.material.get(str(material_id))
        if material_text is None:
            return material_id
        locale = user_locale or locale
        ambr_locale = to_ambr_top(str(locale))
        return material_text[str(ambr_locale)]

    def get_weapon_name(
        self,
        weapon_id: int,
        locale: typing.Union[Locale, str],
        user_locale: typing.Optional[str] = None,
    ) -> typing.Optional[str]:
        avatar_text = self.weapon.get(str(weapon_id))
        if avatar_text is None:
            return None
        locale = user_locale or locale
        ambr_locale = to_ambr_top(str(locale))
        return avatar_text[str(ambr_locale)]

    def get_domain_name(
        self,
        dungeon_id: int,
        locale: typing.Union[Locale, str],
        user_locale: typing.Optional[str] = None,
    ) -> str:
        dungeon_text = self.domain.get(str(dungeon_id))
        if dungeon_text is None:
            return str(dungeon_id)
        locale = user_locale or locale
        ambr_locale = to_ambr_top(str(locale))
        return dungeon_text.get(str(ambr_locale), str(dungeon_id))

    def get_artifact_name(
        self,
        artifact_id: int,
        locale: typing.Union[Locale, str],
        user_locale: typing.Optional[str] = None,
    ):
        artifact_text = self.artifact.get(str(artifact_id))
        if artifact_text is None:
            return artifact_id
        locale = user_locale or locale
        ambr_locale = to_ambr_top(str(locale))
        return artifact_text[str(ambr_locale)]

    @staticmethod
    def _open_file(
        map_type: TextMapType, lang_type: LangType = LangType.EN_US
    ) -> typing.Dict[str, typing.Any]:
        is_yaml = map_type is TextMapType.LANG
        ext = ".yaml" if is_yaml else ".json"

        path = "text_maps/"
        if map_type is TextMapType.LANG:
            path += f"{map_type.value}/{lang_type.value}"
        else:
            path += map_type.value
        path += ext

        try:
            with open(path, "r", encoding="utf-8") as f:
                if is_yaml:
                    return yaml.safe_load(f)  # type: ignore
                return json.load(f)
        except FileNotFoundError:
            return {}


# initialize the class first to load the text maps
text_map = TextMap()
