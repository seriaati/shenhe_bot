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

    def getName(self, id: int, eng: bool = False) -> str:
        textMap = self.en if eng else self.tw
        return textMap.get(id) or id

    def getNameTextHash(self, text_hash: int, eng: bool = False) -> str:
        textMap = self.full_en if eng else self.full_tw
        return textMap.get(text_hash) or text_hash


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


async def calculateDamage(enka_data, chara_name: str, browser):
    talent_to_calculate = ['Normal Atk.', 'Charged Atk.', 'Plunging Atk.', 'Ele. Skill', 'Ele. Burst']
    # browser = await launch({"headless": True, "args": ["--start-maximized"]})
    page = await browser.newPage()
    await page.setViewport({"width": 1440, "height": 900})
    await page.goto("https://frzyc.github.io/genshin-optimizer/#/setting")
    await page.waitForSelector('div.MuiCardContent-root')
    await page.click('button.MuiButton-root.MuiButton-contained.MuiButton-containedError.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButtonBase-root.css-1312m7x')
    result = await convert(enka_data)
    json_object = json.dumps(result)
    await page.focus('textarea.MuiBox-root')
    await page.keyboard.sendCharacter(str(json_object))
    await page.click('button.MuiButton-root.MuiButton-contained.MuiButton-containedSuccess.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButtonBase-root.css-1p356oi')
    await page.click('button#dropdownbtn')
    await page.waitForSelector('ul.MuiList-root.MuiList-padding.MuiMenu-list.css-1ymv12a')
    await page.click('li.MuiMenuItem-root.MuiMenuItem-gutters.MuiButtonBase-root.css-szd4wn:nth-child(n+2)')
    await page.goto(f"https://frzyc.github.io/genshin-optimizer/#/characters/{chara_name}/equip")
    await page.waitForSelector('span.css-t3oe3b')
    labels = await page.querySelectorAll('h6.MuiTypography-root.MuiTypography-subtitle2.css-1tv3e07')
    label_vals = []
    for l in labels:
        val = await (await l.getProperty("textContent")).jsonValue()
        label_vals.append(val)
    result = {}
    normal_attack_name = '<普通攻擊名稱>'
    dmg_type = ['avgHit', 'hit', 'critHit']
    for dmg in range(0, 3):
        await page.click(f'button[value="{dmg_type[dmg]}"]')
        for t in talent_to_calculate:
            index = label_vals.index(t)
            talent_name = await page.querySelector(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({index})>div.MuiCardHeader-root.css-faujvq>div.MuiCardHeader-content.css-11qjisw')
            talent_name = await (await talent_name.getProperty("textContent")).jsonValue()
            if talent_to_calculate.index(t) == 0:
                normal_attack_name = talent_name
                talent_name = f'普攻'
            elif talent_to_calculate.index(t) == 1:
                talent_name = f'重擊'
            elif talent_to_calculate.index(t) == 2:
                talent_name = f'下落攻擊'
            if dmg == 0:
                result[talent_name] = {}
            talent_labels = await page.querySelectorAll(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({index})>div.MuiCardContent-root.css-nph2fg>div.MuiBox-root.css-1tvhq2w>p.MuiTypography-root.MuiTypography-body1:nth-child(1)')
            talent_numbers = await page.querySelectorAll(f'div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation0.MuiCard-root.css-1vbu9gx:nth-child({index})>div.MuiCardContent-root.css-nph2fg>div.MuiBox-root.css-1tvhq2w>p.MuiTypography-root.MuiTypography-body1:nth-child(2)')
            for i in range(0, len(talent_labels)):
                label = await (await talent_labels[i].getProperty("textContent")).jsonValue()
                damage = await (await talent_numbers[i].getProperty("textContent")).jsonValue()
                if dmg == 0:
                    result[talent_name][label] = []
                result[talent_name][label].append(damage)
    await page.close()
    # await browser.close()
    return result, normal_attack_name


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
