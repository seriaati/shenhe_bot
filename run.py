# shenhe-bot by seria

import os
import sys
import traceback
from pathlib import Path
import getpass

import aiohttp
import aiosqlite
from discord import (Game, HTTPException, Intents, Interaction, Message,
                     Status, app_commands)
from discord.ext import commands
from dotenv import load_dotenv
from enkanetwork import EnkaNetworkAPI
from pyppeteer import launch

from cogs.gvaway import GiveAwayCog
from debug import DebugView
from utility.db_utils import DbUtils
from utility.utils import errEmbed, log

load_dotenv()

user_name = getpass.getuser()

if user_name == 'seria':
    token = os.getenv('DEV_TOKEN')
    debug = True
    application_id = os.getenv('DEV_APP_ID')
else:
    token = os.getenv('MAIN_TOKEN')
    debug = False
    application_id = os.getenv('MAIN_APP_ID')

prefix = ['?']
intents = Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True
intents.presences = True


class ShenheBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=prefix,
            intents=intents,
            application_id=application_id
        )

    async def setup_hook(self) -> None:
        # bot variables
        self.session = aiohttp.ClientSession()
        self.db = await aiosqlite.connect('main.db')
        self.browser = await launch({'headless': True, 'autoClose': False, "args": ['--proxy-server="direct://"', '--proxy-bypass-list=*', '--no-sandbox', '--start-maximized']})
        self.debug = debug
        self.enka_client = EnkaNetworkAPI(lang='cht')
        # load jishaku
        await self.load_extension('jishaku')
        # load cogs
        for filepath in Path('./cogs').glob('**/*.py'):
            cog_name = Path(filepath).stem
            await self.load_extension(f'cogs.{cog_name}')
        # load persistent views
        if not self.debug_toggle:
            self.add_view(GiveAwayCog.GiveAwayView(self.db, self))

    async def on_ready(self):
        await self.change_presence(
            status=Status.online,
            activity=Game(name=f'/help')
        )
        print(log(True, False, 'Bot', f'Logged in as {self.user}'))

    async def on_message(self, message: Message):
        if message.author.id == self.user.id:
            return
        await self.process_commands(message)

    async def on_command_error(self, ctx, error) -> None:
        if hasattr(ctx.command, 'on_error'):
            return
        ignored = (commands.CommandNotFound, )
        error = getattr(error, 'original', error)
        if isinstance(error, ignored):
            return
        else:
            print('Ignoring exception in command {}:'.format(
                ctx.command), file=sys.stderr)
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr)

    async def close(self) -> None:
        await self.db.close()
        await self.browser.close()
        await self.session.close()
        return await super().close()


bot = ShenheBot()


tree = bot.tree
@tree.error
async def err_handle(i: Interaction, e: app_commands.AppCommandError):
    traceback_message = traceback.format_exc()
    view = DebugView(traceback_message)
    embed = errEmbed('發生了未知的錯誤, 請至[申鶴的 issue 頁面](https://github.com/seriaati/shenhe_bot/issues)回報這個錯誤').set_author(
        name='未知錯誤', icon_url=i.user.avatar)
    await i.channel.send(embed=embed, view=view)
bot.run(token)
