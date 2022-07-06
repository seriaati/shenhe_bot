import ast
import asyncio
from datetime import datetime, timedelta
import genshin
import aiosqlite
from data.game.talent_books import talent_books
from dateutil import parser
from discord import Embed, User
from discord.ext import commands, tasks
from discord.utils import sleep_until
from utility.apps.FlowApp import FlowApp
from utility.apps.GenshinApp import GenshinApp
from utility.utils import defaultEmbed, getCharacter, log


class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.genshin_app = GenshinApp(self.bot.db, self.bot)
        self.flow_app = FlowApp(self.bot.db, self.bot)
        self.debug_toggle = self.bot.debug_toggle
        self.claim_reward.start()
        self.resin_notification.start()
        self.remove_flow_acc.start()
        self.talent_notification.start()

    def cog_unload(self):
        self.claim_reward.cancel()
        self.resin_notification.cancel()
        self.remove_flow_acc.cancel()
        self.talent_notification.cancel()

    @tasks.loop(hours=24)
    async def claim_reward(self):
        control_channel = self.bot.get_channel(979935065175904286)
        await control_channel.send(log(True, False, 'Claim Reward', 'Start'))
        count = 0
        c: aiosqlite.Cursor = await self.db.cursor()
        await c.execute('SELECT user_id FROM genshin_accounts WHERE ltuid IS NOT NULL')
        users = await c.fetchall()
        for index, tuple in enumerate(users):
            user_id = tuple[0]
            client, uid, only_uid, user = await self.genshin_app.getUserCookie(user_id)
            try:
                await client.claim_daily_reward()
            except genshin.errors.AlreadyClaimed:
                count += 1
            except genshin.errors.InvalidCookies:
                await c.execute('DELETE FROM genshin_accounts WHERE user_id = ?', (user_id,))
            except:
                continue
            else:
                count += 1
            await asyncio.sleep(3.0)
        await control_channel.send(log(True, False, 'Claim Reward', f'Ended, {count} success'))

    @tasks.loop(hours=2)
    async def resin_notification(self):
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT user_id, resin_threshold, current_notif, max_notif FROM genshin_accounts WHERE resin_notification_toggle = 1')
        users = await c.fetchall()
        count = 0
        for index, tuple in enumerate(users):
            user_id = tuple[0]
            resin_threshold = tuple[1]
            current_notif = tuple[2]
            max_notif = tuple[3]
            client, uid, only_uid, user = await self.genshin_app.getUserCookie(user_id)
            try:
                notes = await client.get_notes(uid)
            except genshin.errors.InvalidCookies:
                await c.execute('DELETE FROM genshin_accounts WHERE user_id = ?', (user_id,))
            except:
                await c.execute('UPDATE genshin_accounts SET resin_notification_toggle = 0 WHERE user_id = ?', (user_id,))
            else:
                resin = notes.current_resin
                count += 1
                if not resin >= resin_threshold and current_notif < max_notif:
                    remind_channel = self.bot.get_channel(
                        990237798617473064) if not self.bot.debug_toggle else self.bot.get_channel(909595117952856084)
                    user: User = self.bot.get_user(user_id)
                    embed = defaultEmbed(
                        message=f'目前樹脂: {resin}/160\n'
                        f'目前設定閥值: {resin_threshold}\n'
                        f'目前最大提醒值: {max_notif}\n\n'
                        '輸入`/remind`來更改設定')
                    embed.set_author(name='樹脂要滿出來啦!!', icon_url=user.avatar)
                    await remind_channel.send(content=user.mention, embed=embed)
                    await c.execute('UPDATE genshin_accounts SET current_notif = ? WHERE user_id = ?', (current_notif+1, user_id))
                if resin < resin_threshold:
                    await c.execute('UPDATE genshin_accounts SET current_notif = 0 WHERE user_id = ?', (user_id,))
            await asyncio.sleep(3.0)
        await self.bot.db.commit()

    @tasks.loop(hours=24)
    async def talent_notification(self):
        remind_channel = self.bot.get_channel(
            990237798617473064) if not self.bot.debug_toggle else self.bot.get_channel(909595117952856084)
        weekday = datetime.today().weekday()
        talent_book_icon = {
            '自由': 'https://static.wikia.nocookie.net/genshin-impact/images/d/dc/%E3%80%8C%E8%87%AA%E7%94%B1%E3%80%8D%E7%9A%84%E6%95%99%E5%B0%8E.png/revision/latest?cb=20201020014319&path-prefix=zh-tw',
            '繁榮': 'https://static.wikia.nocookie.net/genshin-impact/images/7/7b/%E3%80%8C%E7%B9%81%E6%A6%AE%E3%80%8D%E7%9A%84%E6%95%99%E5%B0%8E.png/revision/latest/scale-to-width-down/64?cb=20201020014317&path-prefix=zh-tw',
            '抗爭': 'https://static.wikia.nocookie.net/genshin-impact/images/9/9a/%E3%80%8C%E6%8A%97%E7%88%AD%E3%80%8D%E7%9A%84%E6%95%99%E5%B0%8E.png/revision/latest/scale-to-width-down/64?cb=20201020014321&path-prefix=zh-tw',
            '詩文': 'https://static.wikia.nocookie.net/genshin-impact/images/e/eb/%E3%80%8C%E8%A9%A9%E6%96%87%E3%80%8D%E7%9A%84%E6%95%99%E5%B0%8E.png/revision/latest/scale-to-width-down/64?cb=20201020014327&path-prefix=zh-tw',
            '勤勞': 'https://static.wikia.nocookie.net/genshin-impact/images/2/2c/%E3%80%8C%E5%8B%A4%E5%8B%9E%E3%80%8D%E7%9A%84%E6%95%99%E5%B0%8E.png/revision/latest/scale-to-width-down/64?cb=20201020014325&path-prefix=zh-tw',
            '風雅': 'https://static.wikia.nocookie.net/genshin-impact/images/f/f5/%E3%80%8C%E9%A2%A8%E9%9B%85%E3%80%8D%E7%9A%84%E6%95%99%E5%B0%8E.png/revision/latest/scale-to-width-down/64?cb=20211008100225&path-prefix=zh-tw',
            '天光': 'https://static.wikia.nocookie.net/genshin-impact/images/4/4e/%E3%80%8C%E5%A4%A9%E5%85%89%E3%80%8D%E7%9A%84%E6%95%99%E5%B0%8E.png/revision/latest/scale-to-width-down/64?cb=20211008100529&path-prefix=zh-tw',
            '浮世': 'https://static.wikia.nocookie.net/genshin-impact/images/8/8a/%E3%80%8C%E6%B5%AE%E4%B8%96%E3%80%8D%E7%9A%84%E6%95%99%E5%B0%8E.png/revision/latest/scale-to-width-down/64?cb=20211008095854&path-prefix=zh-tw',
            '黃金': 'https://static.wikia.nocookie.net/genshin-impact/images/3/3f/%E3%80%8C%E9%BB%83%E9%87%91%E3%80%8D%E7%9A%84%E6%95%99%E5%B0%8E.png/revision/latest/scale-to-width-down/64?cb=20201020014322&path-prefix=zh-tw'
        }
        if weekday == 6:
            c: aiosqlite = await self.bot.db.cursor()
            talent_book_list = [
                '自由', '繁榮', '浮世',
                '風雅', '抗爭', '勤勞',
                '詩文', '黃金', '天光'
            ]
            await c.execute("SELECT user_id, talent_notif_chara_list FROM genshin_accounts WHERE talent_notif_toggle = 1 AND talent_notif_chara_list != ''")
            data = await c.fetchall()
            for index, tuple in enumerate(data):
                user_id = tuple[0]
                chara_list = ast.literal_eval(tuple[1])
                for chara in chara_list:
                    embed = defaultEmbed(
                        message=f'該為{chara}刷「{book_name}」本啦!\n\n輸入 `/remind` 來更改設定')
                    embed.set_thumbnail(url=getCharacter(name=chara)['icon'])
                    embed.set_author(name=f'刷本啦!', icon_url=(
                        self.bot.get_user(user_id)).avatar)
                    await remind_channel.send(content=(self.bot.get_user(user_id).mention), embed=embed)
            await c.execute('SELECT user_id, item FROM todo')
            data = await c.fetchall()
            mentioned = {}
            for index, item in enumerate(data):
                user_id = item[0]
                if user_id not in mentioned:
                    mentioned[user_id] = []
                for talent_book in talent_book_list:
                    if talent_book in str(item[1]) and talent_book not in mentioned[user_id]:
                        mentioned[user_id].append(talent_book)
                        embed = defaultEmbed(message='這是根據你的代辦清單所發出的自動通知\n輸入 `/todo` 來查看你的代辦清單').set_author(
                            name=f'該刷「{talent_book}」本啦!', icon_url=self.bot.get_user(user_id).avatar)
                        embed.set_thumbnail(url=talent_book_icon[talent_book])
                        await remind_channel.send(content=(self.bot.get_user(user_id).mention), embed=embed)
        else:
            weekday_dict = {
                0: '週一、週四',
                1: '週二、週五',
                2: '週三、週六',
                3: '週一、週四',
                4: '週二、週五',
                5: '週三、週六'
            }
            talent_book_list = {
                0: ['自由', '繁榮', '浮世'],
                1: ['風雅', '抗爭', '勤勞'],
                2: ['詩文', '黃金', '天光'],
                3: ['自由', '繁榮', '浮世'],
                4: ['風雅', '抗爭', '勤勞'],
                5: ['詩文', '黃金', '天光']
            }
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute("SELECT user_id, talent_notif_chara_list FROM genshin_accounts WHERE talent_notif_toggle = 1 AND talent_notif_chara_list != ''")
            data = await c.fetchall()
            for index, tuple in enumerate(data):
                user_id = tuple[0]
                chara_list = ast.literal_eval(tuple[1])
                for chara in chara_list:
                    for book_name, characters in talent_books[weekday_dict[weekday]].items():
                        for character_name, element_name in characters.items():
                            if character_name == chara:
                                embed = defaultEmbed(
                                    message=f'該為{chara}刷「{book_name}」本啦!\n\n輸入 `/remind` 來更改設定')
                                embed.set_thumbnail(url=getCharacter(name=chara)['icon'])
                                embed.set_author(name=f'刷本啦!', icon_url=(
                                    self.bot.get_user(user_id)).avatar)
                                await remind_channel.send(content=(self.bot.get_user(user_id).mention), embed=embed)
            await c.execute('SELECT user_id, item FROM todo')
            data = await c.fetchall()
            mentioned = {}
            for index, item in enumerate(data):
                user_id = item[0]
                if user_id not in mentioned:
                    mentioned[user_id] = []
                for talent_book in talent_book_list[weekday]:
                    if talent_book in str(item[1]) and talent_book not in mentioned[user_id]:
                        mentioned[user_id].append(talent_book)
                        embed = defaultEmbed(message='這是根據你的代辦清單所發出的自動通知\n輸入 `/todo` 來查看你的代辦清單').set_author(
                            name=f'該刷「{talent_book}」本啦!', icon_url=self.bot.get_user(user_id).avatar)
                        embed.set_thumbnail(url=talent_book_icon[talent_book])
                        await remind_channel.send(content=(self.bot.get_user(user_id).mention), embed=embed)

    @tasks.loop(hours=24)
    async def remove_flow_acc(self):
        log(True, False, 'Remove Flow Acc', 'task start')
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT user_id, last_trans FROM flow_accounts')
        result = await c.fetchall()
        now = datetime.now()
        for index, tuple in enumerate(result):
            flow = await self.flow_app.get_user_flow(tuple[0])
            delta = now-parser.parse(tuple[1])
            if delta.days > 7 and flow <= 100:
                await self.flow_app.transaction(
                    tuple[0], flow, is_removing_account=True)
        log(True, False, 'Remove Flow Acc', 'task finished')

    @remove_flow_acc.before_loop
    async def before_loop(self):
        now = datetime.now().astimezone()
        next_run = now.replace(hour=1, minute=30, second=0)  # 等待到早上1點30
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)

    @claim_reward.before_loop
    async def before_claiming_reward(self):
        now = datetime.now().astimezone()
        next_run = now.replace(hour=1, minute=0, second=0)  # 等待到早上1點
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)

    @resin_notification.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @talent_notification.before_loop
    async def before_notif(self):
        await self.bot.wait_until_ready()
        now = datetime.now().astimezone()
        next_run = now.replace(hour=1, minute=20, second=0)  # 等待到早上1點20
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Schedule(bot))
