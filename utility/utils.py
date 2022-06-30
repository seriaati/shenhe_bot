import json
import re
from datetime import datetime

import discord
import genshin
import yaml
from data.game.characters import characters_map
from data.game.consumables import consumables_map
from data.game.stat_emojis import stat_emojis
from data.game.talents import talents_map
from data.game.weapons import weapons_map
from pyppeteer import launch


class GetNameTextMapHash():
    def __init__(self) -> None:
        with open(f"GenshinData/EN_full_textMap.json", "r", encoding="utf-8") as file:
            self.en = json.load(file)
        with open(f"GenshinData/TW_full_textMap.json", "r", encoding="utf-8") as file:
            self.tw = json.load(file)

    def getNameTextMapHash(self, textMapHash: int, eng: bool = False) -> str:
        textMap = self.en if eng else self.tw
        if textMap.get(textMapHash) is not None:
            return textMap.get(textMapHash)
        else:
            raise ValueError(f'找不到 {textMapHash} 的 textMapHash')


get_name_text_map_hash = GetNameTextMapHash()


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
    good_format = await enkaToGOOD(enka_data)
    good_json = json.dumps(good_format)
    await page.focus('textarea.MuiBox-root')
    await page.keyboard.sendCharacter(str(good_json))
    await page.click('button.MuiButton-root.MuiButton-contained.MuiButton-containedSuccess.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButtonBase-root.css-1p356oi')
    await page.click('button#dropdownbtn')
    await page.waitForSelector('ul.MuiList-root.MuiList-padding.MuiMenu-list.css-1ymv12a')
    await page.click('li.MuiMenuItem-root.MuiMenuItem-gutters.MuiButtonBase-root.css-szd4wn:nth-child(n+2)')
    yield(defaultEmbed('<a:LOADER:982128111904776242> 正在調整天賦 (3/6)'))
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
    yield(defaultEmbed('<a:LOADER:982128111904776242> 正在調整武器 (5/6)'))
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


def getWeekdayName(n: int) -> str:
    weekday_dict = {0: '週一', 1: '週二', 2: '週三',
                    3: '週四', 4: '週五', 5: '週六', 6: '週日'}
    return weekday_dict.get(n)


def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def getElementEmoji(element: str):
    element_emojis = {
        'Anemo': '<:WIND_ADD_HURT:982138235239137290>',
        'Cryo': '<:ICE_ADD_HURT:982138229140635648>',
        'Electro': '<:ELEC_ADD_HURT:982138220248711178>',
        'Geo': '<:ROCK_ADD_HURT:982138232391237632>',
        'Hydro': '<:WATER_ADD_HURT:982138233813098556>',
        'Pyro': '<:FIRE_ADD_HURT:982138221569900585>'
    }
    return element_emojis.get(element) or element


def getCharacter(id: int = '', name: str = ''):
    for character_id, character_info in characters_map.items():
        if character_id == str(id) or character_info['name'] == name:
            return character_info
    raise ValueError(f'未知角色: {id}{name}')


def getWeapon(id: int = '', name: str = ''):
    for weapon_id, weapon_info in weapons_map.items():
        if weapon_id == str(id) or weapon_info['name'] == name:
            return weapon_info
    raise ValueError(f'未知武器: {id}{name}')


def getConsumable(id: int = '', name: str = ''):
    for consumable_id, consumable_info in consumables_map.items():
        if consumable_id == str(id) or consumable_info['name'] == name:
            return consumable_info
    return {'name': '自訂素材', 'emoji': '<:white_star:982456919224615002>'}


def getTalent(id: int = '', name: str = ''):
    for talent_id, talent_info in talents_map.items():
        if talent_id == str(id) or talent_info['name'] == name:
            return talent_info
    raise ValueError(f'未知角色: {id}{name}')

async def enkaToGOOD(enka_data):
    good_dict = {
        'format': 'GOOD',
        'version': 1,
        'source': '申鶴 • 忘玄',
        'weapons': [],
        'artifacts': [],
        'characters': []
    }
    weapon_id = 0
    art_id = 0
    for chara in enka_data['avatarInfoList']:
        id = chara['avatarId']
        chara_key = (getCharacter(id)['eng']).replace(' ', '') or chara_key
        level = chara['propMap']['4001']['ival']
        constellation = 0 if 'talentIdList' not in chara else len(
            chara['talentIdList'])
        ascention = chara['propMap']['1002']['ival']
        talents = chara['skillLevelMap']
        if id == 10000002:  # 神里綾華
            talent = {
                'auto': int(talents['10024']),
                'skill': int(talents['10018']),
                'burst': int(talents['10019'])
            }
        elif id == 10000041:  # 莫娜
            talent = {
                'auto': int(talents['10411']),
                'skill': int(talents['10412']),
                'burst': int(talents['10415'])
            }
        else:
            talent = {
                'auto': int(list(talents.values())[0]),
                'skill': int(list(talents.values())[1]),
                'burst': int(list(talents.values())[2]),
            }
        good_dict['characters'].append(
            {
                'key': chara_key,
                'level': int(level),
                'constellation': int(constellation),
                'ascention': int(ascention),
                'talent': talent
            }
        )
        for e in chara['equipList']:
            if 'weapon' in e:
                weapon_id += 1
                key = (get_name_text_map_hash.getNameTextMapHash(e['flat']['nameTextMapHash'], True)).replace("'", '').title().replace(' ','').replace('-','') or e['flat']['nameTextMapHash']
                level = e['weapon']['level']
                ascension = e['weapon']['promoteLevel'] if 'promoteLevel' in e['weapon'] else 0
                refinement = list(e['weapon']['affixMap'].values())[0]+1 if 'affixMap' in e['weapon'] else 0
                location = chara_key
                good_dict['weapons'].append(
                    {
                        'key': key,
                        'level': level,
                        'ascension': ascension,
                        'refinement': refinement,
                        'location': location,
                        'id': weapon_id
                    }
                )
            else:
                art_id += 1
                artifact_pos = {
                    'EQUIP_BRACER': 'flower',
                    'EQUIP_NECKLACE': 'plume',
                    'EQUIP_SHOES': 'sands',
                    'EQUIP_RING': 'goblet',
                    'EQUIP_DRESS': 'circlet'
                }
                stats = {
                    'FIGHT_PROP_HP': 'hp',
                    'FIGHT_PROP_HP_PERCENT': 'hp_',
                    'FIGHT_PROP_ATTACK': 'atk',
                    'FIGHT_PROP_ATTACK_PERCENT': 'atk_',
                    'FIGHT_PROP_DEFENSE': 'def',
                    'FIGHT_PROP_DEFENSE_PERCENT': 'def_',
                    'FIGHT_PROP_CHARGE_EFFICIENCY': 'enerRech_',
                    'FIGHT_PROP_ELEMENT_MASTERY': 'eleMas',
                    'FIGHT_PROP_CRITICAL': 'critRate_',
                    'FIGHT_PROP_CRITICAL_HURT': 'critDMG_',
                    'FIGHT_PROP_HEAL_ADD': 'heal_',
                    'FIGHT_PROP_FIRE_ADD_HURT': 'pyro_dmg_',
                    'FIGHT_PROP_ELEC_ADD_HURT': 'electro_dmg_',
                    'FIGHT_PROP_ICE_ADD_HURT': 'cryo_dmg_',
                    'FIGHT_PROP_WATER_ADD_HURT': 'hydro_dmg_',
                    'FIGHT_PROP_WIND_ADD_HURT': 'anemo_dmg_',
                    'FIGHT_PROP_ROCK_ADD_HURT': 'geo_dmg_',
                    'FIGHT_PROP_GRASS_ADD_HURT': 'dendro_dmg_',
                    'FIGHT_PROP_PHYSICAL_ADD_HURT': 'physical_dmg_'
                }
                setKey = get_name_text_map_hash.getNameTextMapHash(e['flat']['setNameTextMapHash'], True).replace("'", '').title().replace(' ', '').replace('-','') or e['flat']['setNameTextMapHash']
                slotKey = artifact_pos.get(e['flat']['equipType'])
                rarity = e['flat']['rankLevel']
                mainStatKey = stats.get(
                    e['flat']['reliquaryMainstat']['mainPropId'])
                level = e['reliquary']['level']-1
                substats = []
                for sub_stat in e['flat']['reliquarySubstats']:
                    substats.append({
                        'key': stats.get(sub_stat['appendPropId']),
                        'value': sub_stat['statValue']
                    })
                good_dict['artifacts'].append(
                    {
                        'setKey': setKey,
                        'slotKey': slotKey,
                        'rarity': rarity,
                        'mainStatKey': mainStatKey,
                        'level': level,
                        'substats': substats,
                        'location': chara_key,
                        'lock': True,
                        'id': art_id
                    }
                )
    return good_dict
