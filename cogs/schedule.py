import ast
import asyncio
from datetime import datetime, timedelta

import aiosqlite
from apps.genshin.genshin_app import GenshinApp
from apps.genshin.utils import get_character, get_farm_dict, get_material
from apps.text_map.convert_locale import to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from discord import Forbidden, User
from discord.ext import commands, tasks
from discord.utils import format_dt, sleep_until
from utility.utils import default_embed, log

import genshin


class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.genshin_app = GenshinApp(self.bot.db, self.bot)
        self.debug = self.bot.debug
        self.claim_reward.start()
        self.resin_notification.start()
        self.talent_notification.start()

    def cog_unload(self):
        self.claim_reward.cancel()
        self.resin_notification.cancel()
        self.talent_notification.cancel()

    @tasks.loop(hours=24)
    async def claim_reward(self):
        log(True, False, 'Claim Reward', 'Start')
        count = 0
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT user_id FROM genshin_accounts')
        users = await c.fetchall()
        for index, tuple in enumerate(users):
            user_id = tuple[0]
            client, uid, user, user_locale = await self.genshin_app.get_user_data(user_id)
            client.lang = to_genshin_py(user_locale)
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
        await self.bot.db.commit()
        log(True, False, 'Claim Reward', f'Ended, {count} success')

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
            client, uid, user, user_locale = await self.genshin_app.get_user_data(user_id)
            try:
                notes = await client.get_notes(uid)
            except genshin.errors.InvalidCookies:
                await c.execute('DELETE FROM genshin_accounts WHERE user_id = ?', (user_id,))
            except:
                await c.execute('UPDATE genshin_accounts SET resin_notification_toggle = 0 WHERE user_id = ?', (user_id,))
            else:
                resin = notes.current_resin
                count += 1
                if resin >= resin_threshold and current_notif < max_notif:
                    user: User = self.bot.get_user(user_id)
                    embed = default_embed(
                        message=f'{text_map.get(303, "zh-TW", user_locale)}: {notes.current_resin}/{notes.max_resin}\n'
                        f'{text_map.get(15, "zh-TW", user_locale)}: {format_dt(notes.resin_recovery_time, "R")}\n'
                        f'{text_map.get(302, "zh-TW", user_locale)}: {resin_threshold}\n'
                        f'{text_map.get(304, "zh-TW", user_locale)}: {max_notif}')
                    embed.set_footer(text=text_map.get(
                        305, "zh-TW", user_locale))
                    embed.set_author(name=text_map.get(
                        306, "zh-TW", user_locale), icon_url=user.avatar)
                    try:
                        await user.send(embed=embed)
                    except Forbidden:
                        await c.execute('UPDATE genshin_accounts SET resin_notification_toggle = 0 WHERE user_id = ?', (user_id,))
                    await c.execute('UPDATE genshin_accounts SET current_notif = ? WHERE user_id = ?', (current_notif+1, user_id))
                if resin < resin_threshold:
                    await c.execute('UPDATE genshin_accounts SET current_notif = 0 WHERE user_id = ?', (user_id,))
            await asyncio.sleep(3.0)
        await self.bot.db.commit()

    @tasks.loop(hours=24)
    async def talent_notification(self):
        today_weekday = datetime.today().weekday()
        farm_dict = (await get_farm_dict(self.bot.session, 'zh-TW'))[0]
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT user_id, talent_notif_chara_list FROM genshin_accounts WHERE talent_notif_toggle = 1')
        users = await c.fetchall()
        for index, tuple in enumerate(users):
            user_id = tuple[0]
            user = self.bot.get_user(user_id)
            user_locale = await get_user_locale(user_id, self.bot.db)
            user_notification_list = ast.literal_eval(tuple[1])
            notified = {}
            for character_id in user_notification_list:
                for item_id, item_info in farm_dict['avatar'][character_id].items():
                    if today_weekday in item_info['weekday']:
                        if character_id not in notified:
                            notified[character_id] = []
                        if item_id not in notified[character_id]:
                            notified[character_id].append(item_id)
            for character_id, materials in notified.items():
                embed = default_embed()
                embed.set_author(
                    name=f"{text_map.get(312, 'zh-TW', user_locale)} {text_map.get_character_name(character_id, 'zh-TW', user_locale)} {text_map.get(313, 'zh-TW', user_locale)}", icon_url=user.avatar)
                embed.set_thumbnail(url=get_character(character_id)["icon"])
                value = ''
                for material in materials:
                    value += f"{get_material(material)['emoji']} {text_map.get_material_name(material, 'zh-TW', user_locale)}\n"
                embed.add_field(name=text_map.get(
                    314, 'zh-TW', user_locale), value=value)
                await user.send(embed=embed)

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
