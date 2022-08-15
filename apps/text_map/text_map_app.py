import json
from typing import Literal

import discord
import yaml

from apps.text_map.convert_locale import to_ambr_top, to_paths, paths


class TextMap():
    def __init__(self):
        langs = paths.values()
        self.text_maps = {}
        for lang in langs:
            with open(f'text_maps/langs/{lang}.yaml', 'r', encoding='utf-8') as f:
                self.text_maps[str(lang)] = yaml.full_load(f)
        with open('text_maps/avatar.json', 'r', encoding='utf-8') as f:
            self.avatar = json.load(f)
        with open('text_maps/material.json', 'r', encoding='utf-8') as f:
            self.material = json.load(f)
        with open('text_maps/weapon.json', 'r', encoding='utf-8') as f:
            self.weapon = json.load(f)
        with open('text_maps/dailyDungeon.json', 'r', encoding='utf-8') as f:
            self.dailyDungeon = json.load(f)

    def get(self, textMapHash: int, locale: discord.Locale, user_locale: str = None) -> str:
        locale = user_locale or locale 
        path = to_paths(locale)
        text_map = self.text_maps[path]
        text = text_map.get(textMapHash)
        if text is None:
            print(f'text map hash not found: {textMapHash}')
        else:
            return text

    def get_character_name(self, character_id: int, locale: discord.Locale, user_locale: str = None) -> Literal[None, 'str']:
        avatarText = self.avatar.get(str(character_id))
        if avatarText is None:
            print(f'character not found: {character_id}')
            return character_id
        else:
            locale = user_locale or locale
            ambr_locale = to_ambr_top(str(locale))
            return avatarText[str(ambr_locale)]

    def get_material_name(self, material_id: int, locale: discord.Locale, user_locale: str = None):
        avatarText = self.material.get(str(material_id))
        if avatarText is None:
            if str(material_id).isnumeric():
                print(f'material not found: {material_id}')
            return material_id
        else:
            locale = user_locale or locale
            ambr_locale = to_ambr_top(str(locale))
            return avatarText[str(ambr_locale)]
        
    def get_material_id_with_name(self, material_name: str) -> str | int:
        for material_id, material_name_dict in self.material.items():
            for lang_code, material_lang_name in material_name_dict.items():
                if material_lang_name == material_name:
                    return int(material_id)
        return material_name

    def get_weapon_name(self, weapon_id: int, locale: discord.Locale, user_locale: str = None) -> (int | str):
        avatarText = self.weapon.get(str(weapon_id))
        if avatarText is None:
            print(f'weapon not found: {weapon_id}')
            return weapon_id
        else:
            locale = user_locale or locale
            ambr_locale = to_ambr_top(str(locale))
            return avatarText[str(ambr_locale)]

    def get_domain_name(self, dungeon_id: int, locale: discord.Locale, user_locale: str = None):
        dungeonText = self.dailyDungeon.get(str(dungeon_id))
        if dungeonText is None:
            print(f'dungeon not found: {dungeon_id}')
            return dungeon_id
        else:
            locale = user_locale or locale
            ambr_locale = to_ambr_top(str(locale))
            return dungeonText[str(ambr_locale)]

    def get_character_id_with_name(self, character_name: str) -> str | int:
        character_id: str
        for character_id, character_name_dict in self.avatar.items():
            for lang_code, character_lang_name in character_name_dict.items():
                if character_lang_name == character_name:
                    if not character_id.isnumeric():
                        return character_id
                    else:
                        return int(character_id)
        return character_name


# initialize the class first to load the text maps
text_map = TextMap()
