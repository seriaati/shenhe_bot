from itertools import islice
import re
from datetime import datetime
from typing import Dict, List

import discord
from dateutil import parser
from discord.utils import format_dt


def default_embed(title: str = '', message: str = ''):
    embed = discord.Embed(title=title, description=message, color=0xa68bd3)
    return embed


def error_embed(title: str = '', message: str = ''):
    embed = discord.Embed(title=title, description=message, color=0xfc5165)
    return embed


def log(is_system: bool, is_error: bool, log_type: str, log_message: str, record: bool = True):
    now = datetime.now()
    today = datetime.today()
    current_date = today.strftime('%Y-%m-%d')
    current_time = now.strftime("%H:%M:%S")
    system = "SYSTEM"
    if not is_system:
        system = "USER"
    if not is_error:
        log_str = f"<{current_date} {current_time}> [{system}] ({log_type}) {log_message}"
    else:
        log_str = f"<{current_date} {current_time}> [{system}] [ERROR] ({log_type}) {log_message}"
    if record:
        with open('log.txt', 'a+', encoding='utf-8') as f:
            f.write(f'{log_str}\n')
    return log_str


def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end


def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def parse_HTML(HTML_string: str):
    HTML_string = HTML_string.replace('\\n', '\n')
    # replace tags with style attributes
    HTML_string = HTML_string.replace('</p>', '\n')
    HTML_string = HTML_string.replace('<strong>', '**')
    HTML_string = HTML_string.replace('</strong>', '**')

    # remove all HTML tags
    CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    HTML_string = re.sub(CLEANR, '', HTML_string)

    # remove time tags from mihoyo
    HTML_string = HTML_string.replace('t class="t_gl"', '')
    HTML_string = HTML_string.replace('t class="t_lc"', '')
    HTML_string = HTML_string.replace('/t', '')

    # turn date time string into discord timestamps
    matches = re.findall(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}', HTML_string)
    for match in matches:
        datetime_obj = parser.parse(match)
        HTML_string = HTML_string.replace(match, format_dt(datetime_obj))

    return HTML_string

def divide_dict(d: Dict, size: int):
    it = iter(d)
    for i in range(0, len(d), size):
        yield {k:d[k] for k in islice(it, size)}


def get_weekday_int_with_name(weekday_name: str) -> int:
    weekday_name_dict = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }
    return weekday_name_dict.get(weekday_name)


def split_text_and_number(text: str) -> List:
    list_text = list(text)
    letter_index = None
    number_index = None
    for index, letter in enumerate(list_text):
        if not letter.isdigit():
            letter_index = index
        else:
            if index - 1 == letter_index:
                number_index = index
                break
    return [text[:number_index], text[number_index:]]


def extract_integer_from_string(text: str) -> int:
    text = text.replace('-', ' ')
    text = [int(character)
            for character in text.split() if character.isdigit()]
    return int(text[0])
