import json
import re
from typing import Dict, Tuple

import discord
import yaml
from apps.genshin.utils import get_character
from apps.text_map.convert_locale import to_go
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.game.GO_modes import (hit_mode_texts, hit_modes, infusion_aura_texts,
                                infusion_auras, reaction_mode_texts,
                                reaction_modes)
from data.game.good_stats import good_stats
from enkanetwork import EnkaNetworkResponse, model
from enkanetwork.enum import EquipmentsType
from pyppeteer.browser import Browser
from utility.utils import default_embed, log, split_text_and_number


class DamageCalculator:
    def __init__(self, character_name: str, data: EnkaNetworkResponse, browser: Browser, character_id: str, locale: discord.Locale | str, hit_mode: str, member: discord.Member, reaction_mode: str = '', infusion_aura: str = '', team: list = []):
        self.data = data
        self.browser = browser
        self.character_id = character_id
        self.locale = locale
        self.hit_mode = hit_mode
        self.member = member
        self.reaction_mode = reaction_mode
        self.infusion_aura = infusion_aura
        self.team = team
        self.character_name = character_name
        self.current_character = None
        for character in data.characters:
            if str(character.id) == character_id:
                self.current_character = character
                break

    async def run(self) -> discord.Embed:
        damage_dict, description, effect = await self.calculate_damage()
        embed = self.parse_damage_embed(
            damage_dict, description, effect, self.member)
        return embed

    async def calculate_damage(self) -> Tuple[Dict, str, str]:
        character_name = self.current_character.name.replace(' ', '')
        log(True, False, 'calculateDamage',
            f'Calculating damage for {character_name}')
        talents_to_calculate = ['Normal Atk.', 'Charged Atk.',
                                'Plunging Atk.', 'Ele. Skill', 'Ele. Burst']
        no_ele_burst = ['Xiao', 'AratakiItto']
        no_ele_skill = ['Yoimiya']
        if character_name in no_ele_burst:
            talents_to_calculate.remove('Ele. Burst')
        elif character_name in no_ele_skill:
            talents_to_calculate.remove('Ele. Skill')

        if self.current_character.id == 10000060 and self.current_character.constellations_unlocked == 6:  # yelan is C6
            # don't calculate normal attack damage
            talents_to_calculate.remove('Normal Atk.')

        page = await self.browser.newPage()
        await page.setViewport({"width": 1440, "height": 900})
        await page.goto("https://frzyc.github.io/genshin-optimizer/#/setting")
        # click the upload button
        await page.waitForSelector('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-bch5q4 > div.MuiCardContent-root.css-10j5qql:nth-child(3) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1kbwkqu:nth-child(2) > div.MuiCardContent-root.css-10j5qql:nth-child(3) > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-2.css-isbt42 > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-1.css-1ekasd5:nth-child(1) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-lrcwtp > div.MuiCardContent-root.css-nph2fg:nth-child(3) > div.MuiBox-root.css-10egq61 > div.MuiBox-root.css-0:nth-child(2) > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-1.css-qqlytg:nth-child(2) > span.MuiButton-root.MuiButton-contained.MuiButton-containedInfo.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-fullWidth.MuiButtonBase-root.css-1garcay')
        await page.click('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-bch5q4 > div.MuiCardContent-root.css-10j5qql:nth-child(3) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1kbwkqu:nth-child(2) > div.MuiCardContent-root.css-10j5qql:nth-child(3) > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-2.css-isbt42 > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-1.css-1ekasd5:nth-child(1) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-lrcwtp > div.MuiCardContent-root.css-nph2fg:nth-child(3) > div.MuiBox-root.css-10egq61 > div.MuiBox-root.css-0:nth-child(2) > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-1.css-qqlytg:nth-child(2) > span.MuiButton-root.MuiButton-contained.MuiButton-containedInfo.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-fullWidth.MuiButtonBase-root.css-1garcay')
        # get good_json
        good_json, description, effect = await self.convert_to_GOOD_format()
        # focus in the text box
        await page.focus('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1kbwkqu > div.MuiCardContent-root.css-nph2fg:nth-child(2) > textarea.MuiBox-root.css-xkq1iw:nth-child(3)')
        # write in the json data
        await page.keyboard.sendCharacter(str(good_json))
        # replace database button
        await page.click('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1kbwkqu > div.MuiCardContent-root.css-2s1u6n:nth-child(4) > button.MuiButton-root.MuiButton-contained.MuiButton-containedSuccess.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButtonBase-root.css-1p356oi')
        # change language according to locale
        await page.click('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1kbwkqu:nth-child(1) > div.MuiCardContent-root.css-nph2fg:nth-child(3) > button#dropdownbtn.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-fullWidth.MuiButtonBase-root.css-z7p9wm')
        await page.waitForSelector('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiMenu-paper.MuiPaper-elevation8.MuiPopover-paper.css-ifhuam:nth-child(3) > ul.MuiList-root.MuiList-padding.MuiMenu-list.css-1ymv12a > li.MuiMenuItem-root.MuiMenuItem-gutters.MuiButtonBase-root.css-szd4wn:nth-child(2)')
        langauge_num = to_go(self.locale)
        await page.click(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiMenu-paper.MuiPaper-elevation8.MuiPopover-paper.css-ifhuam:nth-child(3) > ul.MuiList-root.MuiList-padding.MuiMenu-list.css-1ymv12a > li.MuiMenuItem-root.MuiMenuItem-gutters.MuiButtonBase-root.css-szd4wn:nth-child({langauge_num})')

        # go to the character's overview page
        await page.goto(f'https://frzyc.github.io/genshin-optimizer/#/characters/{character_name}')
        # wait until the first label appears
        await page.waitForSelector('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(3) > div.MuiBox-root.css-q2n2qf:nth-child(1) > span.MuiTypography-root.MuiTypography-caption.css-5twvz:nth-child(3) > span.css-103d8rc')
        # get all the labels
        label_elements = await page.querySelectorAll('span.css-103d8rc')
        labels = []
        # get the texts of the labels
        for element in label_elements:
            val = await (await element.getProperty("textContent")).jsonValue()
            has_numbers = any(char.isdigit() for char in val)
            if not has_numbers:
                labels.append(val)

        result = {}
        for talent in talents_to_calculate:
            card_index = labels.index(talent)+3
            talent_name = await page.querySelector(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({card_index}) > div.MuiBox-root.css-q2n2qf:nth-child(1) > h6.MuiTypography-root.MuiTypography-subtitle1.css-8ysn2z:nth-child(2) > span')
            talent_name = await (await talent_name.getProperty("textContent")).jsonValue()

            # renaming the talent names for attacks
            if talent == 'Normal Atk.':
                talent_name = text_map.get(326, self.locale)
            elif talent == 'Charged Atk.':
                talent_name = text_map.get(327, self.locale)
            elif talent == 'Plunging Atk.':
                talent_name = text_map.get(328, self.locale)
            result[talent_name] = []

            damage_rows = await page.querySelectorAll(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({card_index}) > ul.MuiList-root.MuiList-padding.css-1jrq055:nth-child(3) > li.MuiListItem-root.MuiListItem-gutters.MuiListItem-padding.MuiBox-root.css-1n74xce')
            index = 1
            for row in damage_rows:
                damage = await page.querySelector(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({card_index}) > ul.MuiList-root.MuiList-padding.css-1jrq055:nth-child(3) > li.MuiListItem-root.MuiListItem-gutters.MuiListItem-padding.MuiBox-root.css-1n74xce:nth-child({index})')
                damage = await (await damage.getProperty("textContent")).jsonValue()
                result[talent_name].append(damage)
                index += 1

        await page.close()
        return result, description, effect

    async def convert_to_GOOD_format(self) -> Tuple[str, str, str]:
        good_dict = {
            'format': 'GOOD',
            'dbVersion': 19,
            'source': 'Genshin Optimizer',
            'version': 1,
            'characters': [],
            'artifacts': [],
            'weapons': []
        }
        description = ''
        effect = ''
        for character in self.data.characters:
            burst_index = 3 if character.id == 10000041 or character.id == 10000002 else 2
            talent = {
                'auto': int(character.skills[0].level),
                'skill': int(character.skills[1].level),
                'burst': int(character.skills[burst_index].level),
            }
            # produce character team
            character_team = ['', '', '']
            if str(character.id) == self.character_id:
                for index, member_id in enumerate(self.team):
                    character_team[index] = get_character(
                        member_id)['eng'].replace(' ', '')
            elif str(character.id) in self.team:
                for index, member_id in enumerate(self.team):
                    if member_id == str(character.id):
                        continue
                    character_team[index] = get_character(
                        member_id)['eng'].replace(' ', '')
                for index, member_id in enumerate(character_team):
                    if member_id == '':
                        character_team[index] = get_character(
                            self.character_id)['eng'].replace(' ', '')
                        break
            character_team.sort(reverse=True)

            # get conditionals
            conditional = conditionals.get(character)[0]
            if (str(character.id) == self.character_id) or (str(character.id) in self.team):
                description += conditionals.get(character)[1]
                effect += conditionals.get(character)[2]

            good_dict['characters'].append(
                {
                    'key': character.name.replace(' ', ''),
                    'level': character.level,
                    'ascension': character.ascension,
                    'hitMode': self.hit_mode,
                    'reaction': self.reaction_mode,
                    'conditional': {character.name.replace(' ', ''): conditional},
                    'bonusStats': {},
                    'enemyOverride': {},
                    'talent': talent,
                    'infusionAura': self.infusion_aura,
                    'constellation': character.constellations_unlocked,
                    'team': character_team,
                    'compareData': False
                }
            )
            weapon = character.equipments[-1]
            weapon_key = 'TheCatch' if weapon.detail.name == '"The Catch"' else weapon.detail.name.replace(
                "'", '').title().replace(' ', '').replace('-', '')
            good_dict['weapons'].append(
                {
                    'key': weapon_key,
                    'level': weapon.level,
                    'ascension': weapon.ascension,
                    'refinement': weapon.refinement,
                    'location': (get_character(character.id)['eng']).replace(' ', ''),
                    'lock': True
                }
            )
            for artifact in filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments):
                substats = []
                for substat in artifact.detail.substats:
                    substats.append({
                        'key': good_stats.get(substat.prop_id),
                        'value': substat.value
                    })
                good_dict['artifacts'].append(
                    {
                        'setKey': artifact.detail.artifact_name_set.replace("'", '').title().replace(' ', '').replace('-', ''),
                        'rarity': artifact.detail.rarity,
                        'level': artifact.level,
                        'slotKey': 'plume' if artifact.detail.artifact_type.lower() == 'feather' else artifact.detail.artifact_type.lower(),
                        'mainStatKey': good_stats.get(artifact.detail.mainstats.prop_id),
                        'substats': substats,
                        'location': (get_character(character.id)['eng']).replace(' ', ''),
                        'exclude': False,
                        'lock': True
                    }
                )
        good_json = json.dumps(good_dict)
        return good_json, description, effect

    def parse_damage_embed(self, damage_dict: dict, description: str, effect: str, member: discord.Member) -> discord.Embed:
        infusion_str = f'({text_map.get(infusion_aura_texts[self.infusion_aura], self.locale)})' if self.infusion_aura != '' else ''
        reaction_mode_str = f'({text_map.get(reaction_mode_texts[self.reaction_mode], self.locale)})' if self.reaction_mode != '' else ''
        embed = default_embed(
            f"{self.character_name} {text_map.get(hit_mode_texts[self.hit_mode], self.locale)} {infusion_str} {reaction_mode_str}")
        field_count = 0
        for talent, damages in damage_dict.items():
            field_count += 1
            value = ''
            for damage in damages:
                value += f'{split_text_and_number(damage)[0]} - {split_text_and_number(damage)[1]}\n'
            embed.add_field(
                name=talent,
                value=value,
                inline=False
            )
        conditions = ''
        if len(self.team) != 0:
            team_str = ''
            for team_member in self.team:
                team_str += f'{get_character(team_member)["emoji"]} {get_character(team_member)["name"]}\n'
            embed.add_field(
                name=text_map.get(345, self.locale),
                value=team_str,
                inline=False
            )
        if description != '':
            conditions += description
        if conditions != '':
            embed.add_field(
                name=text_map.get(346, self.locale),
                value=conditions,
                inline=False if len(self.team) == 0 else True
            )
        if effect != '':
            embed.add_field(
                name=text_map.get(347, self.locale),
                value=effect
            )
        embed.set_author(name=member.display_name, icon_url=member.avatar)
        embed.set_thumbnail(url=get_character(self.character_id)["icon"])
        embed.set_footer(text=text_map.get(349, self.locale))
        return embed


class Conditional():
    def __init__(self):
        with open(f'data/game/conditionals.yaml', 'r', encoding='utf-8') as f:
            self.conditionals = yaml.full_load(f)

    def get(self, character: model.character) -> Tuple[Dict, str, str]:
        result = {}
        description_str = ''
        effect_str = ''
        for conditional in self.conditionals:
            if conditional['name'] == character.name.replace(' ', ''):
                if (conditional['ascension'] is not None and int(character.ascension) >= int(conditional['ascension'])) or (conditional['constellation'] is not None and int(character.constellations_unlocked) >= int(conditional['constellation'])) or (conditional['ascension'] is None and conditional['constellation'] is None):
                    result[conditional['key']] = conditional['value']
                    description_str += f'• {conditional["description"]}\n'
                    effect_str += f"• {conditional['effect']}\n"
        return result, description_str, effect_str


conditionals = Conditional()


async def return_damage(i: discord.Interaction, view):
    user_locale = await get_user_locale(i.user.id, view.enka_view.db)
    calculator = view.calculator
    for item in view.children:
        item.disabled = True
    view.children[0].disabled = False
    await i.response.edit_message(embed=default_embed(f'<a:LOADER:982128111904776242> {text_map.get(329, i.locale, user_locale)}', text_map.get(330, i.locale, user_locale)), view=view)
    embed = await calculator.run()
    for item in view.children:
        item.disabled = False
    reaction_mode_disabled = True
    character_element = str(calculator.current_character.element)
    reaction_mode_elements = ['Pyro', 'Cryo', 'Hydro', 'pyro', 'cryo']
    if character_element in reaction_mode_elements or calculator.infusion_aura in reaction_mode_elements:
        reaction_mode_disabled = False
    view.children[4].disabled = reaction_mode_disabled
    await i.edit_original_message(embed=embed, view=view)
