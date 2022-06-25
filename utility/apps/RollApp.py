import random

import aiosqlite
from utility.apps.FlowApp import FlowApp
from utility.utils import defaultEmbed, log

global blue_gif, purple_gif, gold_gif, air, blue_sleep, purple_sleep, gold_sleep, big_prize
blue_gif = 'https://media.discordapp.net/attachments/968783693814587423/970226962650001418/IMG_0482.gif'
purple_gif = 'https://media.discordapp.net/attachments/968783693814587423/970226962356391966/IMG_0477.gif'
gold_gif = 'https://c.tenor.com/Nc7Fgo43GLwAAAAC/genshin-gold-genshin-wish.gif'
air = '再接再厲!'
blue_sleep = 6.0
purple_sleep = 5.6
gold_sleep = 5.3


class RollApp:
    def __init__(self, db: aiosqlite.Connection, bot) -> None:
        self.db = db
        self.flow_app = FlowApp(self.db, bot)

    async def get_banner_big_prize(self, banner: str):
        c = await self.db.cursor()
        await c.execute('SELECT big_prize FROM banners WHERE banner_name = ?', (banner,))
        big_prize = await c.fetchone()
        return big_prize[0]

    async def animation_chooser(self, prize, banner: str):
        big_prize = await self.get_banner_big_prize(banner)
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

    def lottery(self, item_dic, total_weight):
        score = random.randint(1, total_weight)
        range_max = 0
        for item_key, weight in item_dic.items():
            range_max += weight
            if score <= range_max:
                return item_key

    def gacha(self, item_dic, times):
        total_weight = 0
        for value in item_dic.values():
            total_weight += value
        results = []
        for i in range(times):
            results.append(self.lottery(item_dic, total_weight))
        return results

    async def pull_card(self, is_ten_pull: bool, state: int, banner: str):
        c = await self.db.cursor()
        big_prize = await self.get_banner_big_prize(banner)
        await c.execute('SELECT prize_name, prize_weight FROM banner_prizes WHERE banner_name = ?', (banner,))
        prizes = await c.fetchall()
        prize_pool = {}
        for index, tuple in enumerate(prizes):
            prize_name = tuple[0]
            weight = tuple[1]
            prize_pool[prize_name] = weight
        times = 1 if not is_ten_pull else 10
        if state == 0 or state > 2:
            result = self.gacha(prize_pool, times)
        elif state == 1:
            new_probability = 5
            prize_pool[big_prize] = new_probability
            prize_pool[air] -= new_probability
            result = self.gacha(prize_pool, times)
        elif state == 2:
            new_probability = 10
            prize_pool[big_prize] = new_probability
            prize_pool[air] -= new_probability
            result = self.gacha(prize_pool, times)
        return result

    async def give_money(self, user_id: int, prize):
        for item in prize:
            if item == '10 flow幣':
                await self.flow_app.transaction(
                    user_id=user_id, flow_for_user=10)
            elif item == '100 flow幣':
                await self.flow_app.transaction(
                    user_id=user_id, flow_for_user=100)

    async def gu_system(self, user_id: int, banner: str, is_ten_pull: bool):
        big_prize = await self.get_banner_big_prize(banner)
        c = await self.db.cursor()
        await c.execute('SELECT SUM(guarantee) FROM user_roll_data WHERE user_id = ? AND banner_name = ? AND history IS NULL', (user_id, banner))
        sum = await c.fetchone()
        if sum is None:
            sum = 0
        else:
            sum = sum[0]
        if sum < 70:
            prize = await self.pull_card(is_ten_pull, 0, banner)
        elif 70 <= sum < 80:
            prize = await self.pull_card(is_ten_pull, 1, banner)
        elif 80 <= sum < 89:
            prize = await self.pull_card(is_ten_pull, 2, banner)
        elif sum >= 89:
            prize = await self.pull_card(is_ten_pull, 3, banner)
            prize[0] = big_prize
        return prize

    async def check_big_prize(self, user_id: int, prize, banner: str):
        big_prize = await self.get_banner_big_prize(banner)
        if big_prize in prize:
            c = await self.db.cursor()
            await c.execute('UPDATE user_roll_data SET guarantee = 0 WHERE user_id = ? AND banner_name = ? AND history IS NULL', (user_id, banner))
            await self.db.commit()
            msg = defaultEmbed(
                '有人抽到大獎了!',
                f'ID: {user_id}\n'
                '按ctrl+k並貼上ID即可查看使用者')
            return True, msg
        else:
            return False, None

    async def write_history_and_gu(self, user_id: int, prize, banner: str):
        big_prize = await self.get_banner_big_prize(banner)
        c = await self.db.cursor()
        prize_str = ''
        air_count = 0
        for item in prize:
            await c.execute('SELECT * FROM user_roll_data WHERE user_id = ? AND banner_name = ? AND prize_name = ?', (user_id, banner, item))
            result = await c.fetchone()
            if result is None:
                await c.execute('INSERT INTO user_roll_data (user_id, banner_name, prize_name) VALUES (?, ?, ?)', (user_id, banner, item))
            await c.execute('SELECT history FROM user_roll_data WHERE user_id = ? AND banner_name = ? AND prize_name = ? AND guarantee IS NULL', (user_id, banner, item))
            history = await c.fetchone()
            history = history[0]
            await c.execute('UPDATE user_roll_data SET history = ? WHERE user_id = ? AND banner_name = ? AND prize_name = ? AND guarantee IS NULL', (history+1, user_id, banner, item))
            if item == air:
                air_count += 1
            if item != big_prize:
                await c.execute('SELECT guarantee FROM user_roll_data WHERE user_id = ? AND banner_name = ? AND prize_name = ? AND history IS NULL', (user_id, banner, item))
                guarantee = await c.fetchone()
                guarantee = guarantee[0]
                await c.execute('UPDATE user_roll_data SET guarantee = ? WHERE user_id = ? AND banner_name = ? AND prize_name =  ? AND history IS NULL', (guarantee+1, user_id, banner, item))
            prize_str += f'• {item}\n'
        if air_count == 10:
            prize_str = '10抽什麼都沒有, 太可惜了...'
        await self.db.commit()
        return prize_str
