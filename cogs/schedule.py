import ast
import asyncio
from datetime import datetime, timedelta

import aiosqlite
from data.game.talents import talents
from dateutil import parser
from discord import Embed, User
from discord.ext import commands, tasks
from discord.utils import sleep_until
from utility.apps.FlowApp import FlowApp
from utility.apps.GenshinApp import GenshinApp
from utility.utils import defaultEmbed, getCharaIdWithName, getCharacterIcon, log


class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.genshin_app = GenshinApp(self.bot.db)
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
        count = 0
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT user_id FROM genshin_accounts')
        users = await c.fetchall()
        count = 0
        for index, tuple in enumerate(users):
            user_id = tuple[0]
            await self.genshin_app.claimDailyReward(user_id)
            count += 1
            await asyncio.sleep(3.0)

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
            resin = await self.genshin_app.getRealTimeNotes(user_id, True)
            count += 1
            if resin is not Embed and resin >= resin_threshold and current_notif < max_notif:
                remind_channel = self.bot.get_channel(
                    990237798617473064) if not self.bot.debug_toggle else self.bot.get_channel(909595117952856084)
                user: User = self.bot.get_user(user_id)
                embed = defaultEmbed(
                    message=f'目前樹脂: {resin}/160\n'
                    f'目前設定閥值: {resin_threshold}\n'
                    f'目前最大提醒值: {max_notif}\n\n'
                    '輸入`/remind`來更改設定')
                embed.set_author(name='樹脂要滿出來了啦!!', icon_url=user.avatar)
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
        weekday_dict = {
            0: '週一、週四',
            1: '週二、週五',
            2: '週三、週六',
            3: '週一、週四',
            4: '週二、週五',
            5: '週三、週六'
        }
        
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute("SELECT user_id, talent_notif_chara_list FROM genshin_accounts WHERE talent_notif_toggle = 1 AND talent_notif_chara_list != ''")
        data = await c.fetchall()
        for index, tuple in enumerate(data):
            user_id = tuple[0]
            chara_list = ast.literal_eval(tuple[1])
            for chara in chara_list:
                for book_name, characters in talents[weekday_dict[weekday]].items():
                    for character_name, element_name in characters.items():
                        if character_name == chara:
                            embed = defaultEmbed(message=f'該為{chara}刷「{book_name}」本啦!')
                            embed.set_thumbnail(url=getCharacterIcon(getCharaIdWithName(chara)))
                            embed.set_author(name=f'刷本啦!', icon_url=(self.bot.get_user(user_id)).avatar)
                            await remind_channel.send(content=(self.bot.get_user(user_id).mention),embed=embed)

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
