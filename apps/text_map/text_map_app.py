import json
import re
from typing import Dict, Literal

import discord
import yaml
from apps.text_map.convert_locale import to_ambr_top, to_paths, paths
from utility.utils import log


class TextMap():
    def __init__(self):
        langs = paths.values()
        self.text_maps = {}
        for lang in langs:
            try:
                with open(f'text_maps/langs/{lang}.yaml', 'r', encoding='utf-8') as f:
                    self.text_maps[str(lang)] = yaml.full_load(f)
            except FileNotFoundError:
                self.text_maps[str(lang)] = {}
        try:
            with open('text_maps/avatar.json', 'r', encoding='utf-8') as f:
                self.avatar = json.load(f)
        except FileNotFoundError:
            self.avatar = {}
        try:
            with open('text_maps/material.json', 'r', encoding='utf-8') as f:
                self.material = json.load(f)
        except FileNotFoundError:
            self.material = {}
        try:
            with open('text_maps/weapon.json', 'r', encoding='utf-8') as f:
                self.weapon = json.load(f)
        except FileNotFoundError:
            self.weapon = {}
        try:
            with open('text_maps/dailyDungeon.json', 'r', encoding='utf-8') as f:
                self.dailyDungeon = json.load(f)
        except FileNotFoundError:
            self.dailyDungeon = {}

    def get(self, textMapHash: int, locale: discord.Locale, user_locale: str = None) -> str:
        locale = user_locale or locale 
        path = to_paths(locale)
        text_map: Dict = self.text_maps[path]
        text = text_map.get(str(textMapHash), '')
        if text == '':
            log.warning(f'[Text Map][{locale}][Hash not found]: [Hash]{textMapHash}')
            text_map = self.text_maps['en-US']
            text = text_map.get(str(textMapHash), '')
        text = re.sub(r"<[^\/][^>]*>", "", text)
        return text

    def get_character_name(self, character_id: int, locale: discord.Locale, user_locale: str = None) -> Literal[None, 'str']:
        avatar_text = self.avatar.get(str(character_id))
        if avatar_text is None:
            log.warning(f'[Exception][get_character_name][charcter_id not found]: [character_id]{character_id}')
            return character_id
        else:
            locale = user_locale or locale
            ambr_locale = to_ambr_top(str(locale))
            return avatar_text[str(ambr_locale)]

    def get_material_name(self, material_id: int, locale: discord.Locale, user_locale: str = None):
        material_text = self.material.get(str(material_id))
        if material_text is None:
            if str(material_id).isdigit():
                log.warning(f'[Exception][get_material_name][material_id not found]: [material_id]{material_id}')
            return material_id
        else:
            locale = user_locale or locale
            ambr_locale = to_ambr_top(str(locale))
            return material_text[str(ambr_locale)]
        
    def get_material_id_with_name(self, material_name: str) -> str | int:
        for material_id, material_name_dict in self.material.items():
            for _, material_lang_name in material_name_dict.items():
                if material_lang_name == material_name:
                    return int(material_id)
        log.warning(f'[Exception][get_material_id_with_name][material_name not found]: [material_name]{material_name}')
        return material_name

    def get_weapon_name(self, weapon_id: int, locale: discord.Locale, user_locale: str = None) -> (int | str):
        avatarText = self.weapon.get(str(weapon_id))
        if avatarText is None:
            log.warning(f'[Exception][get_weapon_name][charcter_id not found]: [weapon_id]{weapon_id}')
            return weapon_id
        else:
            locale = user_locale or locale
            ambr_locale = to_ambr_top(str(locale))
            return avatarText[str(ambr_locale)]
        
    def get_weapon_id_with_name(self, weapon_name: str) -> str | int:
        for weapon_id, weapon_name_dict in self.weapon.items():
            for _, weapon_lang_name in weapon_name_dict.items():
                if weapon_lang_name == weapon_name:
                    return int(weapon_id)
        log.warning(f'[Exception][get_weapon_id_with_name][weapon_name not found]: [weapon name]{weapon_name}')
        return weapon_name

    def get_domain_name(self, dungeon_id: int, locale: discord.Locale, user_locale: str = None):
        dungeonText = self.dailyDungeon.get(str(dungeon_id))
        if dungeonText is None:
            log.warning(f'[Exception][get_dungeon_name][charcter_id not found]: [dungeon_id]{dungeon_id}')
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
                    if not character_id.isdigit():
                        return character_id
                    else:
                        return int(character_id)
        log.warning(f'[Exception][get_character_id_with_name][character name not found]: [character_name]{character_name}')
        return character_name


# initialize the class first to load the text maps
text_map = TextMap()
