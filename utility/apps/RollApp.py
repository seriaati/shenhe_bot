import random

import aiosqlite
from data.roll.banner import banner
from data.roll.cutscenes import cutscenes
from utility.apps.FlowApp import FlowApp


class RollApp:
    def __init__(self, db: aiosqlite.Connection) -> None:
        self.db = db
        self.flow_app = FlowApp(self.db)

    def choose_animation(self, prizes: list[str]):
        big_prize = banner['big_prize']
        for prize in prizes:
            if prize == big_prize:
                return cutscenes['gold']['url'], cutscenes['gold']['sleep']
            elif prize == '100 flow幣':
                return cutscenes['purple']['url'], cutscenes['purple']['sleep']
            else:
                result = cutscenes['blue']['url'], cutscenes['blue']['sleep']
        return result

    def populate_prize_pool(self, item_dict, total_weight):
        score = random.randint(1, total_weight)
        range_max = 0
        for item_key, weight in item_dict.items():
            range_max += weight
            if score <= range_max:
                return item_key

    def pull(self, item_dict, times):
        total_weight = 0
        for value in item_dict.values():
            total_weight += value
        pulls = []
        for i in range(times):
            pulls.append(self.populate_prize_pool(item_dict, total_weight))
        return pulls

    def pull_card(self, is_ten_pull: bool, state: int):
        prize_pool = {}
        big_prize = banner['big_prize']['name']
        prize_pool[big_prize] = banner['big_prize']['chance']*100
        for other_prize, probability in banner['other_prizes'].items():
            prize_pool[other_prize] = probability*100
        times = 10 if is_ten_pull else 1
        if state == 1:
            prize_pool[big_prize] = banner['big_prize_guarantee'][0]['new_chance']*100
        elif state == 2:
            prize_pool[big_prize] = banner['big_prize_guarantee'][0]['new_chance']*100
        prize_pool['再接再厲!'] = 10000-len(prize_pool)
        return self.pull(prize_pool, times)

    async def give_money(self, user_id: int, prizes: list[str]):
        for prize in prizes:
            if prize == '10 flow 幣':
                await self.flow_app.transaction(user_id, 10)
            elif prize == '100 flow 幣':
                await self.flow_app.transaction(user_id, 100)

    async def gu_system(self, user_id: int, is_ten_pull: bool):
        c = await self.db.cursor()
        await c.execute('SELECT SUM(count) FROM roll_guarantee WHERE user_id = ?', (user_id,))
        sum = (await c.fetchone())[0] or 0
        if sum < 70:
            prizes = self.pull_card(is_ten_pull, 0)
        elif 70 <= sum < 80:
            prizes = self.pull_card(is_ten_pull, 1)
        elif 80 <= sum < 89:
            prizes = self.pull_card(is_ten_pull, 2)
        elif sum >= 89:
            prizes = self.pull_card(is_ten_pull, 3)
            prizes[0] = banner['big_prize']['name']
        return prizes

    async def check_big_prize(self, user_id: int, prizes: list[str]):
        if banner['big_prize']['name'] in prizes:
            c = await self.db.cursor()
            await c.execute('UPDATE roll_guarantee SET count = 0 WHERE user_id = ?', (user_id,))
            await self.db.commit()
            return True
        else:
            return False

    async def write_history_and_gu(self, user_id: int, prizes: list[str]):
        c = await self.db.cursor()
        prize_str = ''
        air_count = 0
        for prize in prizes:
            await c.execute('INSERT INTO roll_history (user_id, prize, count) VALUES (?, ?, 1) ON CONFLICT (user_id, prize) DO UPDATE SET count = count + 1 WHERE user_id = ?', (user_id, prize, user_id))
            if prize == '再接再厲!':
                air_count += 1
            if prize != banner['big_prize']['name']:
                await c.execute('INSERT INTO roll_guarantee (user_id, prize, count) VALUES (?, ?, 1) ON CONFLICT (user_id, prize) DO UPDATE SET count = count + 1 WHERE user_id = ?', (user_id, prize, user_id))
            prize_str += f'• {prize}\n'
        if air_count == 10:
            prize_str = '10抽什麼都沒有, 太可惜了...'
        await self.db.commit()
        return prize_str
