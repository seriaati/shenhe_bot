import json
import os
import re
import yaml
from datetime import datetime
from enkanetwork import EnkaNetworkResponse
from enkanetwork.enum import EquipmentsType
from enkanetwork import model
import discord
import genshin
from pyppeteer.browser import Browser
from data.game.characters import characters_map
from data.game.consumables import consumables_map
from data.game.fight_prop import fight_prop
from data.game.talents import talents_map
from data.game.weapons import weapons_map
from data.game.artifacts import artifacts_map
from data.game.good_stats import good_stats
from data.game.GOModes import hitModes, reactionModes, infusionAuras
from dotenv import load_dotenv
from pyppeteer import launch

load_dotenv()


def defaultEmbed(title: str = '', message: str = ''):
    return discord.Embed(title=title, description=message, color=0xa68bd3)


def ayaakaaEmbed(title: str = '', message: str = ''):
    return discord.Embed(title=title, description=message, color=0xADC6E5)


def errEmbed(title: str = '', message: str = ''):
    return discord.Embed(title=title, description=message, color=0xfc5165)


def log(is_system: bool, is_error: bool, log_type: str, log_msg: str):
    now = datetime.now()
    today = datetime.today()
    current_date = today.strftime('%Y-%m-%d')
    current_time = now.strftime("%H:%M:%S")
    system = "SYSTEM"
    if not is_system:
        system = "USER"
    if not is_error:
        log_str = f"<{current_date} {current_time}> [{system}] ({log_type}) {log_msg}"
    else:
        log_str = f"<{current_date} {current_time}> [{system}] [ERROR] ({log_type}) {log_msg}"
    with open('log.txt', 'a+', encoding='utf-8') as f:
        f.write(f'{log_str}\n')
    return log_str


def getStatEmoji(propid: str):
    if propid not in fight_prop:
        raise ValueError(f'{propid} does not exist in fight_prop.py')
    return fight_prop[propid]['emoji']


def getClient():
    cookies = {"ltuid": os.getenv('ltuid'),
               "ltoken": os.getenv('ltoken')}
    client = genshin.Client(cookies)
    client.lang = "zh-tw"
    client.default_game = genshin.Game.GENSHIN
    client.uids[genshin.Game.GENSHIN] = 901211014
    return client


def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end


def calculateArtifactScore(substats: dict):
    tier_four_val = {
        'FIGHT_PROP_HP': 1196,
        'FIGHT_PROP_HP_PERCENT': 5.8,
        'FIGHT_PROP_ATTACK': 76,
        'FIGHT_PROP_ATTACK_PERCENT': 5.8,
        'FIGHT_PROP_DEFENSE': 92,
        'FIGHT_PROP_DEFENSE_PERCENT': 7.3,
        'FIGHT_PROP_CHARGE_EFFICIENCY': 6.5,
        'FIGHT_PROP_ELEMENT_MASTERY': 23,
        'FIGHT_PROP_CRITICAL': 3.9,
        'FIGHT_PROP_CRITICAL_HURT': 7.8
    }
    result = 0
    for sub, val in substats.items():
        result += val/tier_four_val.get(sub)*11
    return result


async def calculateDamage(data: EnkaNetworkResponse, browser: Browser, character_id: str, hitMode: str, member: discord.Member, reactionMode: str = '', infusionAura: str = '', team: list = []):
    chara_name = (getCharacter(character_id)['eng']).replace(' ', '')
    log(True, False, 'calculateDamage', f'Calculating damage for {chara_name}')
    talent_to_calculate = ['Normal Atk.', 'Charged Atk.',
                           'Plunging Atk.', 'Ele. Skill', 'Ele. Burst']
    no_ele_burst = ['Xiao', 'AratakiItto']
    no_ele_skill = ['Yoimiya']
    if chara_name in no_ele_burst:
        talent_to_calculate.remove('Ele. Burst')
    elif chara_name in no_ele_skill:
        talent_to_calculate.remove('Ele. Skill')
    if int(character_id) == 10000060: # calculating damage for Yelan
        for character in data.characters: # search for Yelan in characters
            if character.id == 10000060:
                if character.constellations_unlocked == 6: # yelan is C6
                    talent_to_calculate.remove('Normal Atk.') # don't calculate normal attack damage
    # browser = await launch({"headless": False, "args": ["--start-maximized"]})
    page = await browser.newPage()
    await page.setViewport({"width": 1440, "height": 900})
    await page.goto("https://frzyc.github.io/genshin-optimizer/#/setting")
    # upload button
    await page.waitForSelector('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-bch5q4 > div.MuiCardContent-root.css-10j5qql:nth-child(3) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1kbwkqu:nth-child(2) > div.MuiCardContent-root.css-10j5qql:nth-child(3) > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-2.css-isbt42 > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-1.css-1ekasd5:nth-child(1) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-lrcwtp > div.MuiCardContent-root.css-nph2fg:nth-child(3) > div.MuiBox-root.css-10egq61 > div.MuiBox-root.css-0:nth-child(2) > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-1.css-qqlytg:nth-child(2) > span.MuiButton-root.MuiButton-contained.MuiButton-containedInfo.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-fullWidth.MuiButtonBase-root.css-1garcay')
    await page.click('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-bch5q4 > div.MuiCardContent-root.css-10j5qql:nth-child(3) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1kbwkqu:nth-child(2) > div.MuiCardContent-root.css-10j5qql:nth-child(3) > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-2.css-isbt42 > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-1.css-1ekasd5:nth-child(1) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-lrcwtp > div.MuiCardContent-root.css-nph2fg:nth-child(3) > div.MuiBox-root.css-10egq61 > div.MuiBox-root.css-0:nth-child(2) > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-1.css-qqlytg:nth-child(2) > span.MuiButton-root.MuiButton-contained.MuiButton-containedInfo.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-fullWidth.MuiButtonBase-root.css-1garcay')
    # get good_json
    good_json, description, effect = await enkaToGOOD(data, character_id, hitMode, reactionMode, infusionAura, team)
    # text box
    await page.focus('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1kbwkqu > div.MuiCardContent-root.css-nph2fg:nth-child(2) > textarea.MuiBox-root.css-xkq1iw:nth-child(3)')
    # write in the json data
    await page.keyboard.sendCharacter(str(good_json))
    # replace database button
    await page.click('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1kbwkqu > div.MuiCardContent-root.css-2s1u6n:nth-child(4) > button.MuiButton-root.MuiButton-contained.MuiButton-containedSuccess.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButtonBase-root.css-1p356oi')
    # change language to CHT
    await page.click('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1kbwkqu:nth-child(1) > div.MuiCardContent-root.css-nph2fg:nth-child(3) > button#dropdownbtn.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-fullWidth.MuiButtonBase-root.css-z7p9wm')
    await page.waitForSelector('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiMenu-paper.MuiPaper-elevation8.MuiPopover-paper.css-ifhuam:nth-child(3) > ul.MuiList-root.MuiList-padding.MuiMenu-list.css-1ymv12a > li.MuiMenuItem-root.MuiMenuItem-gutters.MuiButtonBase-root.css-szd4wn:nth-child(2)')
    await page.click('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiMenu-paper.MuiPaper-elevation8.MuiPopover-paper.css-ifhuam:nth-child(3) > ul.MuiList-root.MuiList-padding.MuiMenu-list.css-1ymv12a > li.MuiMenuItem-root.MuiMenuItem-gutters.MuiButtonBase-root.css-szd4wn:nth-child(2)')
    await page.goto(f'https://frzyc.github.io/genshin-optimizer/#/characters/{chara_name}/equip')
    await page.waitForSelector('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(2) > div.MuiCardHeader-root.css-faujvq:nth-child(1) > div.MuiCardHeader-action.css-1bh09gn:nth-child(3) > span.css-t3oe3b > h6.MuiTypography-root.MuiTypography-subtitle2.css-1tv3e07')
    labels = await page.querySelectorAll('h6.MuiTypography-root.MuiTypography-subtitle2.css-1tv3e07')
    label_vals = []
    for l in labels:
        val = await (await l.getProperty("textContent")).jsonValue()
        label_vals.append(val)
    result = {}
    await page.waitForSelector(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(2) > div.MuiCardHeader-root.css-faujvq:nth-child(1) > div.MuiCardHeader-content.css-11qjisw:nth-child(2) > span.MuiTypography-root.MuiTypography-subtitle1.MuiCardHeader-title.css-slco8z > span')
    for t in talent_to_calculate:
        card_index = label_vals.index(t)
        talent_name = await page.querySelector(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({card_index}) > div.MuiCardHeader-root.css-faujvq:nth-child(1) > div.MuiCardHeader-content.css-11qjisw:nth-child(2) > span.MuiTypography-root.MuiTypography-subtitle1.MuiCardHeader-title.css-slco8z > span')
        talent_name = await (await talent_name.getProperty("textContent")).jsonValue()
        # print(talent_name)
        if t == 'Normal Atk.':
            talent_name = '普攻'
        elif t == 'Charged Atk.':
            talent_name = '重擊'
        elif t == 'Plunging Atk.':
            talent_name = '下落攻擊'
        result[talent_name] = {}
        talent_rows = await page.querySelectorAll(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({card_index}) > div.MuiCardContent-root.css-14gm9lj:nth-child(3) > ul.MuiList-root.MuiList-padding.css-1jrq055 > li.MuiListItem-root.MuiListItem-gutters.MuiListItem-padding.MuiBox-root.css-1n74xce')
        for row in talent_rows:
            row = await (await row.getProperty("textContent")).jsonValue()
            split_row = re.split(
                '([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[eE]([+-]?\d+))?', row)
            talent_label = split_row[0]  # 天星
            talent_damage = split_row[1]  # 3020.3
            result[talent_name][talent_label] = []
            try:
                result[talent_name][talent_label].append(talent_damage)
            except:
                pass
    await page.close()
    embed = parse_damage_embed(character_id, result, member, hitMode,
                               reactionMode, infusionAura, team, description, effect)
    return embed


async def enkaToGOOD(data: EnkaNetworkResponse, character_id: str, hitMode: str, reactionMode: str = '', infusionAura: str = '', team: list = []) -> str:
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
    for character in data.characters:
        burst_index = 3 if character.id == 10000041 or character.id == 10000002 else 2
        talent = {
            'auto': int(character.skills[0].level),
            'skill': int(character.skills[1].level),
            'burst': int(character.skills[burst_index].level),
        }
        # produce character team
        character_team = ['', '', '']
        if str(character.id) == character_id:
            for index, member_id in enumerate(team):
                character_team[index] = getCharacter(
                    member_id)['eng'].replace(' ', '')
        elif str(character.id) in team:
            for index, member_id in enumerate(team):
                if member_id == str(character.id):
                    continue
                character_team[index] = getCharacter(
                    member_id)['eng'].replace(' ', '')
            for index, member_id in enumerate(character_team):
                if member_id == '':
                    character_team[index] = getCharacter(
                        character_id)['eng'].replace(' ', '')
                    break
        character_team.sort(reverse=True)

        # get conditionals
        conditional = get_conditional.get(character)[0]
        if (str(character.id) == character_id) or (str(character.id) in team):
            description += get_conditional.get(character)[1]
            effect += get_conditional.get(character)[2]

        good_dict['characters'].append(
            {
                'key': character.name.replace(' ', ''),
                'level': character.level,
                'ascension': character.ascension,
                'hitMode': hitMode,
                'reactionMode': reactionMode,
                'conditional': {character.name.replace(' ', ''): conditional},
                'bonusStats': {},
                'enemyOverride': {},
                'talent': talent,
                'infusionAura': infusionAura,
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
                'location': (getCharacter(character.id)['eng']).replace(' ', ''),
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
                    'location': (getCharacter(character.id)['eng']).replace(' ', ''),
                    'exclude': False,
                    'lock': True
                }
            )
    good_json = json.dumps(good_dict)
    # print(good_json)
    return good_json, description, effect


def parse_damage_embed(character_id: int, damage_dict: dict, member: discord.Member, hitMode: str, reactionMode: str = '', infusionAura: str = '', team: list = [], description: str = '', effect: str = ''):
    damage_dict['重擊'], damage_dict['下落攻擊'] = damage_dict['下落攻擊'], damage_dict['重擊']
    infusion_str = f'({infusionAuras[infusionAura]})' if infusionAura != '' else ''
    embed = defaultEmbed(
        f"{getCharacter(character_id)['name']} - {reactionModes[reactionMode] if reactionMode != '' else ''}{hitModes[hitMode]} {infusion_str}")
    field_count = 0
    for talent, damages in damage_dict.items():
        field_count += 1
        value = ''
        for label, label_damages in damages.items():
            if label == '低空墜地衝擊傷害':
                label = '低空墜地傷害'
            elif label == '高空墜地衝擊傷害':
                label = '高空墜地傷害'
            value += f'{label} - {int(float(label_damages[0]))}\n'
        if talent == '重擊':
            talent = '下落攻擊'
        elif talent == '下落攻擊':
            talent = '重擊'
        embed.add_field(
            name=talent,
            value=value,
            inline=True
        )
    conditions = ''
    if len(team) != 0:
        team_str = ''
        for team_member in team:
            team_str += f'{getCharacter(team_member)["emoji"]} {getCharacter(team_member)["name"]}\n'
        embed.add_field(
            name='隊伍',
            value=team_str,
            inline=False
        )
    if description != '':
        conditions += description
    if conditions != '':
        embed.add_field(
            name='狀態',
            value=conditions,
            inline=False if len(team) == 0 else True
        )
    if effect != '':
        embed.add_field(
            name='目前效果',
            value=effect
        )
    embed.set_author(name=member, icon_url=member.avatar)
    embed.set_thumbnail(url=getCharacter(character_id)["icon"])
    return embed


class GetConditional():
    def __init__(self):
        with open(f'data/game/conditionals.yaml', 'r', encoding='utf-8') as f:
            self.conditionals = yaml.full_load(f)

    def get(self, character: model.character):
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


get_conditional = GetConditional()


def trimCookie(cookie: str) -> str:
    try:
        new_cookie = [
            int(re.search(
                r'\d+', (re.search('ltuid=[0-9]{3,}', cookie).group())).group()),
            re.search('[0-9A-Za-z]{20,}', cookie).group(),
            (re.search('cookie_token=[0-9A-Za-z]{20,}', cookie).group())[13:]
        ]
    except:
        new_cookie = None
    return new_cookie


def getWeekdayName(n: int) -> str:
    weekday_dict = {0: '週一', 1: '週二', 2: '週三',
                    3: '週四', 4: '週五', 5: '週六', 6: '週日'}
    return weekday_dict.get(n)


def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def getElement(element: str):
    elements = {
        '風': {'emoji': '<:WIND_ADD_HURT:982138235239137290>','eng': 'Anemo', 'name': '風'},
        '冰': {'emoji': '<:ICE_ADD_HURT:982138229140635648>','eng': 'Cryo', 'name': '冰'},
        '雷': {'emoji': '<:ELEC_ADD_HURT:982138220248711178>','eng': 'Electro', 'name': '雷'},
        '岩': {'emoji': '<:ROCK_ADD_HURT:982138232391237632>','eng': 'Geo', 'name': '岩'},
        '水': {'emoji': '<:WATER_ADD_HURT:982138233813098556>','eng': 'Hydro', 'name': '水'},
        '火': {'emoji': '<:FIRE_ADD_HURT:982138221569900585>','eng': 'Pyro', 'name': '火'}
    }
    for element_name, element_info in elements.items():
        if element_name == element or element_info['eng'] == element or element_info['eng'].lower() == element:
            return element_info


def getCharacter(id: int = '', name: str = '', eng: str = ''):
    for character_id, character_info in characters_map.items():
        if str(id) == character_id or character_info['name'] == name or character_info['eng'] == eng:
            return character_info
    # print(f'Invalid character {id}{name}')
    return {'name': f'{id}{name}{eng}', 'element': 'Cryo', 'rarity': 5, 'icon': 'https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png', 'emoji': '<:WARNING:992552271378386944>', 'eng': 'Unknown'}


def getWeapon(id: int = '', name: str = ''):
    for weapon_id, weapon_info in weapons_map.items():
        if weapon_id == str(id) or weapon_info['name'] == name:
            return weapon_info
    # print(f'Invalid weapon {id}{name}')
    return {'name': f'{id}{name}', 'emoji': '<:WARNING:992552271378386944>', 'rarity': 5, 'icon': 'https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png', 'eng': 'Unknown'}


def getConsumable(id: int = '', name: str = ''):
    for consumable_id, consumable_info in consumables_map.items():
        if consumable_id == str(id) or consumable_info['name'] == name:
            return consumable_info
    return {'name': '自訂素材', 'emoji': '<:white_star:982456919224615002>'}


def getTalent(id: int = '', name: str = ''):
    for talent_id, talent_info in talents_map.items():
        if talent_id == str(id) or talent_info['name'] == name:
            return talent_info
    return {'name': f'{id}{name}'}


def getArtifact(id: int = '', name: str = ''):
    for artifact_id, artifact_info in artifacts_map.items():
        if artifact_id == str(id) or name in artifact_info['artifacts'] or name == artifact_info['name']:
            return artifact_info
    raise ValueError(f'Unknwon artifact {id}{name}')


def getFightProp(id: str = '', name: str = ''):
    for fight_prop_id, fight_prop_info in fight_prop.items():
        if fight_prop_id == str(id) or name == fight_prop_info['name']:
            return fight_prop_info
    raise ValueError(f'Unknwon fight prop {id}{name}')


def getAreaEmoji(area_name: str):
    emoji_dict = {
        '蒙德': '<:Emblem_Mondstadt:982449412938809354>',
        '璃月': '<:Emblem_Liyue:982449411047165992>',
        '稻妻': '<:Emblem_Inazuma:982449409117806674>',
        '層岩巨淵': '<:Emblem_Chasm:982449404076249138>',
        '層岩巨淵·地下礦區': '<:Emblem_Chasm:982449404076249138>',
        '淵下宮': '<:Emblem_Enkanomiya:982449407469441045>',
        '龍脊雪山': '<:Emblem_Dragonspine:982449405883977749>'
    }
    emoji = emoji_dict.get(area_name)
    return emoji or ''
