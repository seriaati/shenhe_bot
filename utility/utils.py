import os
from datetime import datetime
import discord
import genshin
from dotenv import load_dotenv

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


def getWeekdayName(n: int) -> str:
    weekday_dict = {0: '週一', 1: '週二', 2: '週三',
                    3: '週四', 4: '週五', 5: '週六', 6: '週日'}
    return weekday_dict.get(n)


def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]
