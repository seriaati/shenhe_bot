from pprint import pprint
from typing import Dict, Literal, Tuple

import aiosqlite
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.game.standard_characters import get_standard_characters
from discord import Embed, Interaction
from utility.utils import error_embed


async def check_user_wish_data(user_id: int, i: Interaction, db: aiosqlite.Connection) -> Tuple[bool, Embed]:
    c = await db.cursor()
    user_locale = await get_user_locale(user_id, db)
    await c.execute('SELECT wish_name FROM wish_history WHERE user_id = ?', (user_id,))
    result = await c.fetchone()
    embed = error_embed(message=text_map.get(368, i.locale, user_locale)).set_author(
        name=text_map.get(367, i.locale, user_locale), icon_url=i.user.avatar)
    if result is None:
        return False, embed
    else:
        return True, None


async def get_user_event_wish(user_id: int, db: aiosqlite.Connection) -> Tuple[int, int, int, Literal[0, 1]]:
    """Gets a users's event wish data

    Args:
        user_id (int): the discord user id
        db (aiosqlite.Connection): the shenhe database that contains user wish data

    Returns:
        Tuple[int, int, int, Literal[0, 1]]: Returns get_num(number of five stars), left_pull(number of pulls from the last five star), use_pull(total number of pulls), up_guarantee(whether the user has a big pity, 1 is yes, 0 is no)
    """
    c = await db.cursor()
    await c.execute("SELECT wish_name, wish_rarity, wish_time FROM wish_history WHERE user_id = ? AND (wish_banner_type = 301 OR wish_banner_type = 400)", (user_id,))
    user_wish_history = await c.fetchall()
    user_wish_history.sort(key=lambda index: index[2], reverse=True)

    get_num = 0  # 抽到了幾個5星
    left_pull = 0  # 墊了幾抽
    use_pull = len(user_wish_history)  # 共抽了幾抽
    found_last_five_star = False
    up_guarantee = 0  # 有無大保底, 1 代表有
    standard_num = 0 # 抽到的常駐角色數量

    standard_characters = get_standard_characters()

    for index, tuple in enumerate(user_wish_history):
        wish_name = tuple[0]
        wish_rarity = tuple[1]
        if wish_rarity == 5:
            get_num += 1
            if wish_name in standard_characters:
                standard_num += 1
            if not found_last_five_star:
                found_last_five_star = True
                if wish_name in standard_characters:  # 最後一個抽到的五星是常駐
                    up_guarantee = 1  # 所以有大保底
                else:
                    up_guarantee = 0
        else:
            if not found_last_five_star:  # 在找到最後一個抽到的五星之前都算墊的
                left_pull += 1
                
    up_five_star_num = get_num - standard_num

    return get_num, left_pull, use_pull, up_guarantee, up_five_star_num


async def get_user_weapon_wish(user_id: int, db: aiosqlite.Connection) -> Tuple[str, int]:
    """Gets a user's weapon wish data

    Args:
        user_id (int): the discord user id
        db (aiosqlite.Connection): the shenhe database that contains user wish data

    Returns:
        Tuple[str, int]: Returns last_name (the last weapon name), and pull_state(number of pulls from the last five star)
    """
    c = await db.cursor()
    await c.execute("SELECT wish_name, wish_rarity, wish_time FROM wish_history WHERE user_id = ? AND wish_banner_type = 302 AND wish_type = '武器'", (user_id,))
    user_wish_history = await c.fetchall()
    user_wish_history.sort(key=lambda index: index[2], reverse=True)

    last_name = ''  # 最後一個抽到的武器的名字
    pull_state = 0  # 墊了幾抽

    for index, tuple in enumerate(user_wish_history):
        wish_name = tuple[0]
        wish_rarity = tuple[1]
        if wish_rarity != 5:
            pull_state += 1
        else:
            last_name = wish_name
            break

    return last_name, pull_state


async def get_user_wish_overview(user_id: int, db: aiosqlite.Connection) -> Dict[int, Dict[str, int]]:
    c = await db.cursor()

    # 200 - permanent wish
    # 301 - character event wish
    # 400 - character event wish
    # 302 - weapon event wish
    banner_ids = [200, 301, 302]
    
    standard_characters = get_standard_characters()

    result = {}

    for banner_id in banner_ids:
        if banner_id == 301:
            await c.execute('SELECT wish_rarity, wish_name, wish_time FROM wish_history WHERE user_id = ? AND (wish_banner_type = ? OR wish_banner_type = 400)', (user_id, banner_id))
        else:
            await c.execute('SELECT wish_rarity, wish_name, wish_time FROM wish_history WHERE user_id = ? AND wish_banner_type = ?', (user_id, banner_id))
        user_wish_history = await c.fetchall()
        user_wish_history.sort(key=lambda index: index[2], reverse=True)
        
        total = len(user_wish_history)  # 總抽
        left_pull = 0  # 墊抽
        std = 0 # 常駐
        for index, tuple in enumerate(user_wish_history):
            wish_rarity = tuple[0]
            wish_name = tuple[1]
            if wish_name in standard_characters:
                std += 1
            if wish_rarity == 5:
                break
            else:  # 不是五星墊抽＋1
                left_pull += 1

        five_star = 0
        four_star = 0
        if banner_id == 301:
            await c.execute('SELECT COUNT (wish_id) FROM wish_history WHERE user_id = ? AND (wish_banner_type = ? OR wish_banner_type = 400) AND wish_rarity = 5', (user_id, banner_id))
        else:
            await c.execute('SELECT COUNT (wish_id) FROM wish_history WHERE user_id = ? AND wish_banner_type = ? AND wish_rarity = 5', (user_id, banner_id))
        five_star = (await c.fetchone())[0]
        if banner_id == 301:
            await c.execute('SELECT COUNT (wish_id) FROM wish_history WHERE user_id = ? AND (wish_banner_type = ? OR wish_banner_type = 400) AND wish_rarity = 4', (user_id, banner_id))
        else:
            await c.execute('SELECT COUNT (wish_id) FROM wish_history WHERE user_id = ? AND wish_banner_type = ? AND wish_rarity = 4', (user_id, banner_id))
        four_star = (await c.fetchone())[0]

        result[banner_id] = {
            'total': total,
            'five_star': five_star,
            'four_star': four_star,
            'left_pull': left_pull,
            'std': std
        }

    # pprint(result)
    return result
