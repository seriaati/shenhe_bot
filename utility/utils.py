import re
from datetime import datetime

import discord
import genshin

from utility.character_name import character_names
from utility.stat_emojis import stat_emojis


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


def getCharacterName(character: genshin.models.BaseCharacter) -> str:
    chinese_name = character_names.get(character.id)
    return chinese_name if chinese_name != None else character.name

def getCharacterNameWithID(id: int) -> str:
    chinese_name = character_names.get(id)
    return chinese_name

async def getCharacterIcon(id: int):
    client = getClient()
    charas = await client.get_calculator_characters()
    for c in charas:
        if c.id == id:
            return c.icon

async def getTalentNames(id: int):
    client = getClient()
    talents = await client.get_character_talents(int(id))
    result = {}
    for t in talents:
        result[t.id] = t.name
    return result

async def getWeaponName(id: int):
    client = getClient()
    weapons = await client.get_calculator_weapons()
    for w in weapons:
        if w.id == id:
            return w.name

async def getArtifactNames(id: int):
    client = getClient()
    if (id//10)%10 == 5:
        artifacts = await client.get_complete_artifact_set((id//10)-1)
    else:
        artifacts = await client.get_complete_artifact_set((id//10)+1)
    for artifact in artifacts:
        if artifact.id == id//10:
            result = artifact.name
    return result

def getStatEmoji(propid: str):
    emoji = stat_emojis.get(propid)
    return emoji if emoji != None else propid

def getClient():
    cookies = {"ltuid": 7368957, "ltoken": 'X5VJAbNxdKpMp96s7VGpyIBhSnEJr556d5fFMcT5'}
    client = genshin.Client(cookies)
    client.lang = "zh-tw"
    client.default_game = genshin.Game.GENSHIN
    client.uids[genshin.Game.GENSHIN] = 901211014
    return client

def trimCookie(cookie: str) -> str:
    try:
        new_cookie = ' '.join([
            re.search('ltoken=[0-9A-Za-z]{20,}', cookie).group(),
            re.search('ltuid=[0-9]{3,}', cookie).group(),
            re.search('cookie_token=[0-9A-Za-z]{20,}', cookie).group(),
            re.search('account_id=[0-9]{3,}', cookie).group()
        ])
    except:
        new_cookie = None
    return new_cookie


weekday_dict = {0: '週一', 1: '週二', 2: '週三', 3: '週四', 4: '週五', 5: '週六', 6: '週日'}


def getWeekdayName(n: int) -> str:
    return weekday_dict.get(n)
