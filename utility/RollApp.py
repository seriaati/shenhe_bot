from utility.FlowApp import flow_app
from random import randint
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
    if type(prize) is list:
        for item in prize:
            if item == big_prize:
                result = gold_gif, gold_sleep
                break
            elif item == '100 flow幣':
                result = purple_gif, purple_sleep
                break
            else:
                result = blue_gif, blue_sleep
    else:
        if prize == air or prize == '10 flow幣':
            result = blue_gif, blue_sleep
        elif prize == '100 flow幣':
            result = purple_gif, purple_sleep
        elif prize == big_prize:
            result = gold_gif, gold_sleep
    return result


def pull_card(is_ten_pull: bool, state: int, banner: str):
    banners = openFile('roll')
    big_prize = banners[banner]['big_prize']
    prize_pool = banners[banner]['prizes']
    count = 0
    prize_pool_list = []
    for item, num in prize_pool.items():
        for i in range(int(num)):
            count += 1
            prize_pool_list.append(item)
    if state == 0:
        for i in range(1000-count):
            prize_pool_list.append(air)
    elif state == 1:
        for i in range(1000-count-44):
            prize_pool_list.append(air)
        for i in range(44):
            prize_pool_list.append(big_prize)
    elif state == 2:
        for i in range(1000-count-94):
            prize_pool_list.append(air)
        for i in range(94):
            prize_pool_list.append(big_prize)
    else:
        for i in range(1000-count):
            prize_pool_list.append(air)
    if not is_ten_pull:
        index = randint(0, 999)
        return prize_pool_list[index]
    else:
        result = []
        for i in range(10):
            index = randint(0, 999)
            result.append(prize_pool_list[index])
        return result


def give_money(user_id: int, prize):
    if type(prize) is list:
        for item in prize:
            if item == '10 flow幣':
                flow_app.transaction(
                    user_id=user_id, flow_for_user=10)
            elif item == '100 flow幣':
                flow_app.transaction(
                    user_id=user_id, flow_for_user=100)
            elif item == '1000 flow幣':
                flow_app.transaction(
                    user_id=user_id, flow_for_user=1000)
    else:
        if prize == '10 flow幣':
            flow_app.transaction(user_id=user_id, flow_for_user=10)
        elif prize == '100 flow幣':
            flow_app.transaction(
                user_id=user_id, flow_for_user=100)
        elif prize == '1000 flow幣':
            flow_app.transaction(
                user_id=user_id, flow_for_user=1000)


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


def gu_system(user_id: int, banner: str, is_ten_pull:bool, contribution_mode: bool = False):
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
            if type(prize) is not list:
                prize = big_prize
            else:
                prize[0] = big_prize
    else:
        if sum >= 99:
            prize = prize = pull_card(is_ten_pull, 3, banner)
            if type(prize) is not list:
                prize = big_prize
            else:
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
    if type(prize) is not list:
        if prize == big_prize:
            gu[user_id][banner] = {
                big_prize: 0,
                '10 flow幣': 0,
                '100 flow幣': 0,
                '1000 flow幣': 0,
                air: 0
            }
            print(log(True, False, 'Roll',
                      f'{user_id} got big_prize'))
            saveFile(gu, 'pull_guarantee')
            return True, msg
        else:
            return False, None
    else:
        if big_prize in prize:
            gu[user_id][banner] = {
                big_prize: 0,
                '10 flow幣': 0,
                '100 flow幣': 0,
                '1000 flow幣': 0,
                air: 0
            }
            print(log(True, False, 'Roll',
                      f'{user_id} got big_prize'))
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
    if type(prize) is not list:
        history[user_id][banner][prize] += 1
        if prize != big_prize:
            gu[user_id][banner][prize] += 1
    else:
        prizeStr = ''
        count = 0
        for item in prize:
            if item == air:
                count += 1
            history[user_id][banner][item] += 1
            if item != big_prize:
                gu[user_id][banner][item] += 1
            prizeStr += f'• {item}\n'
        prize = prizeStr
        if count == 10:
            prize = '10抽什麼都沒有, 太可惜了...'
    saveFile(history, 'pull_history')
    saveFile(gu, 'pull_guarantee')
    return prize
