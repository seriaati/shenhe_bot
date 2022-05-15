import random
from utility.FlowApp import flow_app
from utility.utils import defaultEmbed, log, openFile, saveFile

global blue_gif, purple_gif, gold_gif, air, blue_sleep, purple_sleep, gold_sleep, big_prize
blue_gif = 'https://media.discordapp.net/attachments/968783693814587423/970226962650001418/IMG_0482.gif'
purple_gif = 'https://media.discordapp.net/attachments/968783693814587423/970226962356391966/IMG_0477.gif'
gold_gif = 'https://c.tenor.com/Nc7Fgo43GLwAAAAC/genshin-gold-genshin-wish.gif'
air = '再接再厲!'
blue_sleep = 6.0
purple_sleep = 5.6
gold_sleep = 5.3


def animation_chooser(prize, banner: str):
    banners = openFile('roll')
    big_prize = banners[banner]['big_prize']
    for item in prize:
        if item == big_prize:
            result = gold_gif, gold_sleep
            break
        elif item == '100 flow幣':
            result = purple_gif, purple_sleep
            break
        else:
            result = blue_gif, blue_sleep
    return result


def lottery(item_dic, total_weight):
    score = random.randint(1, total_weight)
    range_max = 0
    for item_key, weight in item_dic.items():
        range_max += weight
        if score <= range_max:
            return item_key


def gacha(item_dic, times):
    total_weight = 0
    for value in item_dic.values():
        total_weight += value
    results = []
    for i in range(times):
        results.append(lottery(item_dic, total_weight))
    return results


def pull_card(is_ten_pull: bool, state: int, banner: str):
    banners = openFile('roll')
    big_prize = banners[banner]['big_prize']
    prize_pool = banners[banner]['prizes']
    times = 1 if not is_ten_pull else 10
    if state == 0 or state > 2:
        result = gacha(prize_pool, times)
    elif state == 1:
        new_probability = 5
        prize_pool[big_prize] = new_probability
        prize_pool[air] -= new_probability
        result = gacha(prize_pool, times)
    elif state == 2:
        new_probability = 10
        prize_pool[big_prize] = new_probability
        prize_pool[air] -= new_probability
        result = gacha(prize_pool, times)
    return result


def give_money(user_id: int, prize):
    for item in prize:
        if item == '10 flow幣':
            flow_app.transaction(
                user_id=user_id, flow_for_user=10)
        elif item == '100 flow幣':
            flow_app.transaction(
                user_id=user_id, flow_for_user=100)


def check_user_data(user_id: int, banner: str, contribution_mode: bool = False):
    if contribution_mode == True:
        user_id = 'all'
    banners = openFile('roll')
    history = openFile('pull_history')
    gu = openFile('pull_guarantee')
    if user_id not in history:
        history[user_id] = {}
    if user_id not in gu:
        gu[user_id] = {}
    if banner not in history[user_id]:
        history[user_id][banner] = {}
        for item, count in banners[banner]['prizes'].items():
            history[user_id][banner][item] = 0
        history[user_id][banner][air] = 0
    if banner not in gu[user_id]:
        gu[user_id][banner] = {}
        for item, count in banners[banner]['prizes'].items():
            gu[user_id][banner][item] = 0
        gu[user_id][banner][air] = 0
    saveFile(history, 'pull_history')
    saveFile(gu, 'pull_guarantee')


def gu_system(user_id: int, banner: str, is_ten_pull: bool, contribution_mode: bool = False):
    if contribution_mode == True:
        user_id = 'all'
    gu = openFile('pull_guarantee')
    banners = openFile('roll')
    big_prize = banners[banner]['big_prize']
    sum = 0
    for item, count in gu[user_id][banner].items():
        sum += count
    if contribution_mode == False:
        if sum < 70:
            prize = pull_card(is_ten_pull, 0, banner)
        elif 70 <= sum < 80:
            prize = pull_card(is_ten_pull, 1, banner)
        elif 80 <= sum < 89:
            prize = pull_card(is_ten_pull, 2, banner)
        elif sum >= 89:
            prize = pull_card(is_ten_pull, 3, banner)
            prize[0] = big_prize
    else:
        if sum >= 99:
            prize = prize = pull_card(is_ten_pull, 3, banner)
            prize[0] = big_prize
        else:
            prize = pull_card(is_ten_pull, 0, banner)
    return prize


def check_big_prize(user_id: int, prize, banner: str, contribution_mode: bool = False):
    if contribution_mode == True:
        user_id = 'all'
    gu = openFile('pull_guarantee')
    banners = openFile('roll')
    big_prize = banners[banner]['big_prize']
    msg = defaultEmbed(
        '有人抽到大獎了!',
        f'ID: {user_id}\n'
        '按ctrl+k並貼上ID即可查看使用者')
    if big_prize in prize:
        gu[user_id][banner] = {
            big_prize: 0,
            '10 flow幣': 0,
            '100 flow幣': 0,
            '1000 flow幣': 0,
            air: 0
        }
        print(log(True, False, 'Roll',
                  f'{user_id} got big_prize in {banner}'))
        saveFile(gu, 'pull_guarantee')
        return True, msg
    else:
        return False, None


def write_history_and_gu(user_id: int, prize, banner: str, contribution_mode: bool = False):
    if contribution_mode == True:
        user_id = 'all'
    banners = openFile('roll')
    history = openFile('pull_history')
    gu = openFile('pull_guarantee')
    big_prize = banners[banner]['big_prize']
    prizeStr = ''
    air_count = 0
    for item in prize:
        history[user_id][banner][item] += 1
        if item == air:
            air_count += 1
        if item != big_prize:
            gu[user_id][banner][item] += 1
        prizeStr += f'• {item}\n'
    if air_count == 10:
        prizeStr = '10抽什麼都沒有, 太可惜了...'
    saveFile(history, 'pull_history')
    saveFile(gu, 'pull_guarantee')
    return prizeStr
