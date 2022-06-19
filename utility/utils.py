import re
from datetime import datetime

import discord
import genshin
import yaml
import json
from pyppeteer import launch
from utility.enkaToGOOD import convert
from utility.stat_emojis import stat_emojis


class GetName():
    def __init__(self) -> None:
        with open(f"GenshinData/EN_simple_textMap.yaml", "r", encoding="utf-8") as file:
            self.en = yaml.full_load(file)
        with open(f"GenshinData/TW_simple_textMap.yaml", "r", encoding="utf-8") as file:
            self.tw = yaml.full_load(file)
        with open(f"GenshinData/EN_full_textMap.json", "r", encoding="utf-8") as file:
            self.full_en = json.load(file)
        with open(f"GenshinData/TW_full_textMap.json", "r", encoding="utf-8") as file:
            self.full_tw = json.load(file)
        with open('GenshinData/wiki_materials.yaml', 'r', encoding='utf-8') as f:
            self.wiki_materials = yaml.full_load(f)

    def getName(self, id: int, eng: bool = False) -> str:
        textMap = self.en if eng else self.tw
        return textMap.get(id) or id

    def getNameTextHash(self, text_hash: int, eng: bool = False) -> str:
        textMap = self.full_en if eng else self.full_tw
        return textMap.get(text_hash) or text_hash

    def getWikiMaterialName(self, id: int) -> str:
        return self.wiki_materials.get(id) or id


get_name = GetName()


def defaultEmbed(title: str, message: str = ''):
    return discord.Embed(title=title, description=message, color=0xa68bd3)


def ayaakaaEmbed(title: str, message: str = ''):
    return discord.Embed(title=title, description=message, color=0xADC6E5)


def errEmbed(title: str, message: str = ''):
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


def getCharacterIcon(id: int):
    with open("GenshinData/chara_icon.yaml", "r") as file:
        chara_icon = yaml.full_load(file)
    return chara_icon.get(id)


def getStatEmoji(propid: str):
    emoji = stat_emojis.get(propid)
    return emoji if emoji != None else propid


def getClient():
    cookies = {"ltuid": 7368957,
               "ltoken": 'X5VJAbNxdKpMp96s7VGpyIBhSnEJr556d5fFMcT5'}
    client = genshin.Client(cookies)
    client.lang = "zh-tw"
    client.default_game = genshin.Game.GENSHIN
    client.uids[genshin.Game.GENSHIN] = 901211014
    return client


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


async def calculateDamage(enka_data, chara_name: str, browser, dmg: int):
    log(True, False, 'calculateDamage', f'Calculating damage for {chara_name}')
    talent_to_calculate = ['Normal Atk.', 'Charged Atk.',
                           'Plunging Atk.', 'Ele. Skill', 'Ele. Burst']
    no_ele_burst = ['Xiao', 'AratakiItto']
    no_ele_skill = ['Yoimiya']
    if chara_name in no_ele_burst:
        talent_to_calculate.remove('Ele. Burst')
    elif chara_name in no_ele_skill:
        talent_to_calculate.remove('Ele. Skill')
    # browser = await launch({"headless": True, "args": ["--start-maximized"]})
    page = await browser.newPage()
    await page.setViewport({"width": 1440, "height": 900})
    await page.goto("https://frzyc.github.io/genshin-optimizer/#/setting")
    yield(defaultEmbed('<a:LOADER:982128111904776242> 正在匯入角色資料 (2/6)'))
    await page.waitForSelector('div.MuiCardContent-root')
    await page.click('button.MuiButton-root.MuiButton-contained.MuiButton-containedError.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButtonBase-root.css-1312m7x')
    good_format = await convert(enka_data)
    good_json = json.dumps(good_format)
    await page.focus('textarea.MuiBox-root')
    await page.keyboard.sendCharacter(str(good_json))
    await page.click('button.MuiButton-root.MuiButton-contained.MuiButton-containedSuccess.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButtonBase-root.css-1p356oi')
    await page.click('button#dropdownbtn')
    await page.waitForSelector('ul.MuiList-root.MuiList-padding.MuiMenu-list.css-1ymv12a')
    await page.click('li.MuiMenuItem-root.MuiMenuItem-gutters.MuiButtonBase-root.css-szd4wn:nth-child(n+2)')
    yield(defaultEmbed('<a:LOADER:982128111904776242> 正在確認有無特殊天賦 (3/6)'))
    if chara_name == 'Xiao':
        await page.goto(f'https://frzyc.github.io/genshin-optimizer/#/characters/Xiao/talent')
        await page.waitForSelector('div.MuiCardContent-root.css-182b5p1 > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu:nth-child(6) > div.MuiGrid-root.MuiGrid-container.MuiGrid-item.MuiGrid-spacing-xs-1.MuiGrid-grid-xs-12.MuiGrid-grid-md-12.MuiGrid-grid-lg-9.css-1x7fo23:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-sm-6.MuiGrid-grid-md-4.css-1twzmnh:nth-child(3) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-38r5pq > div.MuiCardContent-root.css-nph2fg:nth-child(2) > div.MuiBox-root.css-1821gv5:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(3) > div.MuiCardContent-root.css-14gm9lj > button.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeSmall.MuiButton-containedSizeSmall.MuiButton-fullWidth.MuiButtonBase-root.css-ayzgrw')
        await page.click('div.MuiCardContent-root.css-182b5p1 > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu:nth-child(6) > div.MuiGrid-root.MuiGrid-container.MuiGrid-item.MuiGrid-spacing-xs-1.MuiGrid-grid-xs-12.MuiGrid-grid-md-12.MuiGrid-grid-lg-9.css-1x7fo23:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-sm-6.MuiGrid-grid-md-4.css-1twzmnh:nth-child(3) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-38r5pq > div.MuiCardContent-root.css-nph2fg:nth-child(2) > div.MuiBox-root.css-1821gv5:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(3) > div.MuiCardContent-root.css-14gm9lj > button.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeSmall.MuiButton-containedSizeSmall.MuiButton-fullWidth.MuiButtonBase-root.css-ayzgrw')
    elif chara_name == 'RaidenShogun':
        await page.goto('https://frzyc.github.io/genshin-optimizer/#/characters/RaidenShogun/talent')
        await page.waitForSelector('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-38r5pq > div.MuiCardContent-root.css-nph2fg:nth-child(2) > div.MuiBox-root.css-1821gv5:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(3) > div.MuiCardContent-root.css-14gm9lj > button.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeSmall.MuiButton-containedSizeSmall.MuiButton-fullWidth.MuiButtonBase-root.css-ayzgrw')  # eye of stormy judgement
        await page.click('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-38r5pq > div.MuiCardContent-root.css-nph2fg:nth-child(2) > div.MuiBox-root.css-1821gv5:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(3) > div.MuiCardContent-root.css-14gm9lj > button.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeSmall.MuiButton-containedSizeSmall.MuiButton-fullWidth.MuiButtonBase-root.css-ayzgrw')  # eye of stormy judgement
        await page.click('div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-sm-6.MuiGrid-grid-md-4.css-1twzmnh:nth-child(3) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-38r5pq > div.MuiCardContent-root.css-nph2fg:nth-child(2) > div.MuiBox-root.css-1821gv5:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(3) > div.MuiCardContent-root.css-14gm9lj > button#dropdownbtn.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeSmall.MuiButton-containedSizeSmall.MuiButton-fullWidth.MuiButtonBase-root.css-ayzgrw')  # resolve stacks
        await page.waitForSelector('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiMenu-paper.MuiPaper-elevation8.MuiPopover-paper.css-ifhuam:nth-child(3) > ul.MuiList-root.MuiList-padding.MuiMenu-list.css-1ymv12a > li.MuiMenuItem-root.MuiMenuItem-gutters.MuiButtonBase-root.css-szd4wn:nth-child(7)')  # 50 stack
        await page.click('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiMenu-paper.MuiPaper-elevation8.MuiPopover-paper.css-ifhuam:nth-child(3) > ul.MuiList-root.MuiList-padding.MuiMenu-list.css-1ymv12a > li.MuiMenuItem-root.MuiMenuItem-gutters.MuiButtonBase-root.css-szd4wn:nth-child(7)')  # 50 stack
    elif chara_name == 'KamisatoAyaka':
        await page.goto('https://frzyc.github.io/genshin-optimizer/#/characters/KamisatoAyaka/talent')
        await page.waitForSelector('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx > div.MuiCardContent-root.css-182b5p1 > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu:nth-child(6) > div.MuiGrid-root.MuiGrid-container.MuiGrid-item.MuiGrid-spacing-xs-1.MuiGrid-grid-xs-12.MuiGrid-grid-md-12.MuiGrid-grid-lg-9.css-1x7fo23:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-sm-6.MuiGrid-grid-md-4.css-1twzmnh:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-38r5pq > div.MuiCardContent-root.css-nph2fg:nth-child(2) > div.MuiBox-root.css-1821gv5:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(3) > div.MuiCardContent-root.css-14gm9lj:nth-child(3) > button.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeSmall.MuiButton-containedSizeSmall.MuiButton-fullWidth.MuiButtonBase-root.css-ayzgrw')  # After using ele. skill
        await page.click('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx > div.MuiCardContent-root.css-182b5p1 > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu:nth-child(6) > div.MuiGrid-root.MuiGrid-container.MuiGrid-item.MuiGrid-spacing-xs-1.MuiGrid-grid-xs-12.MuiGrid-grid-md-12.MuiGrid-grid-lg-9.css-1x7fo23:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-sm-6.MuiGrid-grid-md-4.css-1twzmnh:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-38r5pq > div.MuiCardContent-root.css-nph2fg:nth-child(2) > div.MuiBox-root.css-1821gv5:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(3) > div.MuiCardContent-root.css-14gm9lj:nth-child(3) > button.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeSmall.MuiButton-containedSizeSmall.MuiButton-fullWidth.MuiButtonBase-root.css-ayzgrw')  # After using ele. skill
        await page.click('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx > div.MuiCardContent-root.css-182b5p1 > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu:nth-child(6) > div.MuiGrid-root.MuiGrid-container.MuiGrid-item.MuiGrid-spacing-xs-1.MuiGrid-grid-xs-12.MuiGrid-grid-md-12.MuiGrid-grid-lg-9.css-1x7fo23:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-sm-6.MuiGrid-grid-md-4.css-1twzmnh:nth-child(4) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-38r5pq > div.MuiCardContent-root.css-nph2fg > div.MuiBox-root.css-1821gv5:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(4) > div.MuiCardContent-root.css-14gm9lj:nth-child(3) > button.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeSmall.MuiButton-containedSizeSmall.MuiButton-fullWidth.MuiButtonBase-root.css-ayzgrw')  # sprint touches enemy
    elif chara_name == 'HuTao':
        await page.goto('https://frzyc.github.io/genshin-optimizer/#/characters/HuTao/talent')
        await page.waitForSelector('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx > div.MuiCardContent-root.css-182b5p1 > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu:nth-child(6) > div.MuiGrid-root.MuiGrid-container.MuiGrid-item.MuiGrid-spacing-xs-1.MuiGrid-grid-xs-12.MuiGrid-grid-md-12.MuiGrid-grid-lg-9.css-1x7fo23:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-sm-6.MuiGrid-grid-md-4.css-1twzmnh:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-38r5pq > div.MuiCardContent-root.css-nph2fg:nth-child(2) > div.MuiBox-root.css-1821gv5:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(3) > div.MuiCardContent-root.css-14gm9lj > button.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeSmall.MuiButton-containedSizeSmall.MuiButton-fullWidth.MuiButtonBase-root.css-ayzgrw')  # ele. skill
        await page.click('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx > div.MuiCardContent-root.css-182b5p1 > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu:nth-child(6) > div.MuiGrid-root.MuiGrid-container.MuiGrid-item.MuiGrid-spacing-xs-1.MuiGrid-grid-xs-12.MuiGrid-grid-md-12.MuiGrid-grid-lg-9.css-1x7fo23:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-sm-6.MuiGrid-grid-md-4.css-1twzmnh:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-38r5pq > div.MuiCardContent-root.css-nph2fg:nth-child(2) > div.MuiBox-root.css-1821gv5:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(3) > div.MuiCardContent-root.css-14gm9lj > button.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeSmall.MuiButton-containedSizeSmall.MuiButton-fullWidth.MuiButtonBase-root.css-ayzgrw')  # ele.skill
        await page.click('div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx > div.MuiCardContent-root.css-182b5p1 > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu:nth-child(6) > div.MuiGrid-root.MuiGrid-container.MuiGrid-item.MuiGrid-spacing-xs-1.MuiGrid-grid-xs-12.MuiGrid-grid-md-12.MuiGrid-grid-lg-9.css-1x7fo23:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-sm-6.MuiGrid-grid-md-4.css-1twzmnh:nth-child(5) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-38r5pq > div.MuiCardContent-root.css-nph2fg > div.MuiBox-root.css-1821gv5:nth-child(2) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(2) > div.MuiCardContent-root.css-14gm9lj > button.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeSmall.MuiButton-containedSizeSmall.MuiButton-fullWidth.MuiButtonBase-root.css-ayzgrw')
    yield(defaultEmbed('<a:LOADER:982128111904776242> 計算傷害中 (4/6)'))
    await page.goto(f"https://frzyc.github.io/genshin-optimizer/#/characters/{chara_name}/equip")
    await page.waitForSelector('span.css-t3oe3b')
    yield(defaultEmbed('<a:LOADER:982128111904776242> 正在確認有無特殊武器 (5/6)'))
    for w in good_format['weapons']:
        if w['key'] == 'MistsplitterReforged' and w['location'] == chara_name:
            # Mistsplitter's Edge
            selector = 'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx > div.MuiCardContent-root.css-182b5p1 > div.MuiBox-root.css-1821gv5:nth-child(5) > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu:nth-child(2) > div.MuiGrid-root.MuiGrid-container.MuiGrid-item.MuiGrid-spacing-xs-1.MuiGrid-grid-xs-12.MuiGrid-grid-md-12.MuiGrid-grid-xl-3.css-gew0gq:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-md-6.MuiGrid-grid-lg-4.css-170ukis:nth-child(1) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1kbwkqu > div.MuiCardContent-root.css-nph2fg > div.MuiBox-root.css-1821gv5 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(2) > div.MuiCardContent-root.css-14gm9lj:nth-child(3) > button#dropdownbtn.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeSmall.MuiButton-containedSizeSmall.MuiButton-fullWidth.MuiButtonBase-root.css-ayzgrw'
            await page.waitForSelector(selector)
            await page.click(selector)
            # 3 stacks
            selector = 'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiMenu-paper.MuiPaper-elevation8.MuiPopover-paper.css-ifhuam:nth-child(3) > ul.MuiList-root.MuiList-padding.MuiMenu-list.css-1ymv12a > li.MuiMenuItem-root.MuiMenuItem-gutters.MuiButtonBase-root.css-szd4wn:nth-child(5)'
            await page.waitForSelector(selector)
            await page.click(selector)
            break
        elif w['key'] == 'StaffOfHoma' and w['location'] == 'HuTao' and chara_name == 'HuTao':
            # Reckless Cinnabar, HP less than 50%
            selector = 'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx > div.MuiCardContent-root.css-182b5p1 > div.MuiBox-root.css-1821gv5:nth-child(5) > div.MuiGrid-root.MuiGrid-container.MuiGrid-spacing-xs-1.css-tuxzvu:nth-child(2) > div.MuiGrid-root.MuiGrid-container.MuiGrid-item.MuiGrid-spacing-xs-1.MuiGrid-grid-xs-12.MuiGrid-grid-md-12.MuiGrid-grid-xl-3.css-gew0gq:nth-child(2) > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-12.MuiGrid-grid-md-6.MuiGrid-grid-lg-4.css-170ukis:nth-child(1) > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1kbwkqu > div.MuiCardContent-root.css-nph2fg > div.MuiBox-root.css-1821gv5 > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child(2) > div.MuiCardContent-root.css-14gm9lj:nth-child(3) > button.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary.MuiButton-sizeSmall.MuiButton-containedSizeSmall.MuiButton-fullWidth.MuiButtonBase-root.css-ayzgrw'
            await page.waitForSelector(selector)
            await page.click(selector)
            break
    # Ele. Skill
    yield(defaultEmbed('<a:LOADER:982128111904776242> 正在蒐集傷害數字 (6/6)'))
    labels = await page.querySelectorAll('h6.MuiTypography-root.MuiTypography-subtitle2.css-1tv3e07')
    label_vals = []
    for l in labels:
        val = await (await l.getProperty("textContent")).jsonValue()
        label_vals.append(val)
    result = {}
    normal_attack_name = '<普通攻擊名稱>'
    dmg_type = ['avgHit', 'hit', 'critHit']
    await page.click(f'button[value="{dmg_type[dmg]}"]')  # Avg. DMG
    for t in talent_to_calculate:
        card_index = label_vals.index(t)
        talent_name = await page.querySelector(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({card_index}) > div.MuiCardHeader-root.css-faujvq:nth-child(1) > div.MuiCardHeader-content.css-11qjisw:nth-child(2) > span.MuiTypography-root.MuiTypography-subtitle1.MuiCardHeader-title.css-slco8z > span')
        talent_name = await (await talent_name.getProperty("textContent")).jsonValue()
        # print(talent_name)
        if talent_to_calculate.index(t) == 0:
            normal_attack_name = talent_name
            talent_name = f'普攻'
        elif talent_to_calculate.index(t) == 1:
            talent_name = f'重擊'
        elif talent_to_calculate.index(t) == 2:
            talent_name = f'下落攻擊'
        result[talent_name] = {}
        talent_rows = await page.querySelectorAll(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({card_index}) > div.MuiCardContent-root.css-14gm9lj:nth-child(3) > ul.MuiList-root.MuiList-padding.css-1jrq055 > li.MuiListItem-root.MuiListItem-gutters.MuiListItem-padding.MuiBox-root.css-1n74xce')
        for row in talent_rows:
            # 天星3020.3
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
    yield [result, normal_attack_name]


def trimCookie(cookie: str) -> str:
    try:
        new_cookie = ' '.join([
            re.search('ltoken=[0-9A-Za-z]{20,}', cookie).group(),
            re.search('ltuid=[0-9]{3,}', cookie).group(),
            re.search('cookie_token=[0-9A-Za-z]{20,}', cookie).group(),
            re.search('account_id=[0-9]{3,}', cookie).group(),
            re.search('cookie_token=[0-9A-Za-z]{20,}', cookie).group()
        ])
    except:
        new_cookie = None
    return new_cookie


weekday_dict = {0: '週一', 1: '週二', 2: '週三', 3: '週四', 4: '週五', 5: '週六', 6: '週日'}


def getWeekdayName(n: int) -> str:
    return weekday_dict.get(n)


def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]
