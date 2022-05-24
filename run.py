# shenhe-bot by seria

from datetime import datetime
from pathlib import Path
import aiosqlite

import discord
from discord.ext import commands
from cogs.flow import FlowCog
# from cogs.gvaway import GiveAwayCog
from utility.config import config
from utility.utils import log, openFile
from utility.db_utils import DbUtils

print("main or dev?")
user = input()
if user == "main":
    token = config.main
    prefix = ['!', '！']
    guild = 778804551972159489
    application_id = 956049912699715634
else:
    token = config.dev
    prefix = ['%']
    guild = 778804551972159489
    application_id = 957621570128449626

# 前綴, token, intents
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True


class ShenheBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=prefix,
            intents=intents,
            application_id=application_id,
            owner_ids=[289597294075183114, 410036441129943050]
        )

    async def setup_hook(self) -> None:
        self.db = await aiosqlite.connect('main.db')
        db_utils = DbUtils(self.db)
        check, cursor = await db_utils.table_exists('flow_accounts')
        if not check:
            now = datetime.now()
            default_time = datetime(
                year=now.year, month=now.month, day=now.day-1,
                hour=now.hour, minute=now.minute, second=now.second,
                microsecond=now.microsecond)
            await cursor.execute(f"CREATE TABLE flow_accounts(user_id INTEGER PRIMARY KEY, flow INTEGER DEFAULT 0, morning TEXT DEFAULT '{str(default_time)}', noon TEXT DEFAULT '{str(default_time)}', night TEXT DEFAULT '{str(default_time)}', last_trans TEXT DEFAULT '{str(now)}', find_free_trial INTEGER DEFAULT 0)")
            flow_users = openFile('flow')
            for user_id, value in flow_users.items():
                await cursor.execute('INSERT INTO flow_accounts (user_id, flow) VALUES (?, ?)', (user_id, value['flow']))
        check, cursor = await db_utils.table_exists('bank')
        if not check:
            bank = openFile('bank')
            await cursor.execute('CREATE TABLE bank(flow INTEGER)')
            await cursor.execute(f"INSERT INTO bank (flow) VALUES ({bank['flow']})")
        check, cursor = await db_utils.table_exists('flow_shop')
        if not check:
            shop = openFile('shop')
            await cursor.execute('CREATE TABLE flow_shop(name TEXT PRIMARY KEY, flow INTEGER, current INTEGER DEFAULT 0, max INTEGER)')
            for item_name, value in shop.items():
                await cursor.execute('INSERT INTO flow_shop (name, flow, current, max) VALUES (?, ?, ?, ?)',(item_name, value['flow'], value['current'], value['max']))
        check, cursor = await db_utils.table_exists('flow_shop_log')
        if not check:
            await cursor.execute('CREATE TABLE flow_shop_log(log_uuid TEXT PRIMARY KEY, flow INTEGER, item TEXT, buyer_id INTEGER)')
        check, cursor = await db_utils.table_exists('find')
        if not check:
            await cursor.execute('CREATE TABLE find(msg_id INTEGER, flow INTEGER, title TEXT, type INTEGER, author_id INTEGER, confirmer_id INTEGER)')
        check, cursor = await db_utils.table_exists('genshin_accounts')
        if not check:
            await cursor.execute('CREATE TABLE genshin_accounts(user_id INTEGER PRIMARY KEY, ltuid INTEGER, ltoken TEXT, uid INTEGER, resin_notification_toggle INTEGER DEFAULT 0, resin_threshold INTEGER DEFAULT 140, current_notif INTEGER DEFAULT 0, max_notif INTEGER DEFAULT 3)')
            accounts = openFile('accounts')
            for user_id, value in accounts.items():
                await cursor.execute('INSERT INTO genshin_accounts (user_id, uid) VALUES (?, ?)',(user_id, value['uid']))
                if 'ltuid' in value:
                    await cursor.execute('UPDATE genshin_accounts SET ltuid = ?, ltoken = ? WHERE user_id = ?', (value['ltuid'], value['ltoken'], user_id))
        check, cursor = await db_utils.table_exists('wish_history')
        if not check:
            await cursor.execute('CREATE TABLE wish_history(user_id INTEGER, wish_name TEXT, wish_rarity INTEGER, wish_time TEXT, wish_type TEXT, wish_banner_type INTEGER)')
            for filepath in Path('./data/wish_history').glob('**/*.yaml'):
                file_name = Path(filepath).stem
                wish_history = openFile(f'wish_history/{file_name}')
                for wish in wish_history:
                    await cursor.execute('INSERT INTO wish_history (user_id, wish_name, wish_rarity, wish_time, wish_type, wish_banner_type) VALUES (?, ?, ?, ?, ?, ?)', (file_name, wish.name, wish.rarity, f'{wish.time.year}-{wish.time.month}-{wish.time.day}', wish.type, wish.banner_type))
        check, cursor = await db_utils.table_exists('giveaway')
        if not check:
            await cursor.execute('CREATE TABLE giveaway(msg_id INTEGER, prize_name TEXT, goal INTEGER, ticket INTEGER, current INTEGER DEFAULT 0, role_id INTEGER, refund_mode_toggle INTEGER)')
        check, cursor = await db_utils.table_exists('giveaway_members')
        if not check:
            await cursor.execute('CREATE TABLE giveaway_members(user_id INTEGER, msg_id INTEGER)')
        check, cursor = await db_utils.table_exists('banners')
        if not check:
            await cursor.execute('CREATE TABLE banners(banner_name TEXT, image_url TEXT, big_prize TEXT)')
            await cursor.execute('INSERT INTO banners (banner_name, image_url, big_prize) VALUES (?, ?, ?)', ('星月交輝 - 限定祈願', 'https://i.imgur.com/q5q47o7.jpeg', '空月祝福 1個月'))
        check, cursor = await db_utils.table_exists('banner_prizes')
        if not check:
            await cursor.execute('CREATE TABLE banner_prizes (banner_name TEXT, prize_name TEXT, prize_weight INTEGER)')
            banners = openFile('roll')
            for prize_name, weight in banners['星月交輝 - 限定祈願']['prizes'].items():
                await cursor.execute('INSERT INTO banner_prizes (banner_name, prize_name, prize_weight) VALUES (?, ?, ?)', ('星月交輝 - 限定祈願', prize_name, weight))
        check, cursor = await db_utils.table_exists('user_roll_data')
        if not check:
            await cursor.execute('CREATE TABLE user_roll_data (user_id INTEGER, banner_name TEXT, prize_name TEXT, history INTEGER DEFAULT 0, guarantee INTEGER DEFAULT 0)')
            history = openFile('pull_history')
            for user_id, value in history.items():
                for prize_name, number in value['星月交輝 - 限定祈願'].items():
                    await cursor.execute('INSERT INTO user_roll_data (user_id, banner_name, prize_name, history, guarantee) VALUES (?, ?, ?, ?, ?)', (user_id, '星月交輝 - 限定祈願', prize_name, number, None))
            guarantee = openFile('pull_guarantee')
            for user_id, value in guarantee.items():
                for prize_name, number in value['星月交輝 - 限定祈願'].items():
                    await cursor.execute('INSERT INTO user_roll_data (user_id, banner_name, prize_name, guarantee, history) VALUES (?, ?, ?, ?, ?)', (user_id, '星月交輝 - 限定祈願', prize_name, number, None))
        check, cursor = await db_utils.table_exists('guild_members')
        if not check:
            await cursor.execute('CREATE TABLE guild_members (user_id INTEGER PRIMARY KEY)')
            guild_members = openFile('guild_members')
            for member, date in guild_members.items():
                await cursor.execute('INSERT INTO guild_members (user_id) VALUES (?)', (member,))
        await self.db.commit()
        

        await self.load_extension('jishaku')
        for filepath in Path('./cogs').glob('**/*.py'):
            cog_name = Path(filepath).stem
            await self.load_extension(f'cogs.{cog_name}')
            print(log(True, False, 'Cog', f'Loaded {cog_name}'))
        self.add_view(FlowCog.AcceptView(None, self.db))
        self.add_view(FlowCog.ConfirmView(None, self.db))
        # self.add_view(GiveAwayCog.GiveAwayView())

    async def on_ready(self):
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name=f'/help')
        )
        print(log(True, False, 'Bot', f'Logged in as {self.user}'))

    async def on_message(self, message):
        await self.process_commands(message)

    async def on_command_error(self, ctx: commands.Context, error):
        print(log(True, True, 'On Command Error', error))
        if isinstance(error, commands.CommandNotFound):
            pass

    async def close(self) -> None:
        await self.db.close()
        return await super().close()


bot = ShenheBot()
bot.run(token)
