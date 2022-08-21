# shenhe-bot by seria

import getpass
import os
import sys
import traceback
from pathlib import Path
from typing import Optional

import aiohttp
import aiosqlite
from discord import (Forbidden, Game, Intents, Interaction, Locale, Message, Status,
                     app_commands)
from discord.app_commands import TranslationContext, locale_str
from discord.ext import commands
from dotenv import load_dotenv
from enkanetwork import EnkaNetworkAPI
from pyppeteer import launch

from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from debug import DebugView
from UI_elements.others import Roles
from utility.utils import error_embed, log

load_dotenv()

user_name = getpass.getuser()

if user_name == 'seria':
    token = os.getenv('YAE_TOKEN')
    debug = True
    application_id = os.getenv('YAE_APP_ID')
else:
    token = os.getenv('SHENHE_BOT_TOKEN')
    debug = False
    application_id = os.getenv('SHENHE_BOT_APP_ID')

prefix = ['?']
intents = Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True
intents.presences = True


class Translator(app_commands.Translator):
    async def translate(self, string: locale_str, locale: Locale, context: TranslationContext) -> Optional[str]:
        try:
            return text_map.get(string.extras['hash'], locale)
        except KeyError:
            return None


class ShenheBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=prefix,
            intents=intents,
            application_id=application_id
        )

    async def setup_hook(self) -> None:
        user = getpass.getuser()
        
        # bot variables
        self.session = aiohttp.ClientSession()
        self.db = await aiosqlite.connect('shenhe.db')
        self.main_db = await aiosqlite.connect(f"C:/Users/{user}/shenhe_main/main.db")
        self.browser = await launch({'headless': True, 'autoClose': False, "args": ['--proxy-server="direct://"', '--proxy-bypass-list=*', '--no-sandbox', '--start-maximized']})
        self.debug = debug
        self.enka_client = EnkaNetworkAPI()
        
        # load jishaku
        await self.load_extension('jishaku')
        
        # load cogs
        for filepath in Path('./cogs').glob('**/*.py'):
            cog_name = Path(filepath).stem
            await self.load_extension(f'cogs.{cog_name}')
            
        # load persistent views
        self.add_view(Roles.View())

    async def on_ready(self):
        await self.change_presence(
            status=Status.online,
            activity=Game(name=f'/help')
        )
        tree = self.tree
        await tree.set_translator(Translator())
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
        await self.main_db.close()
        await self.browser.close()
        await self.session.close()
        return await super().close()


bot = ShenheBot()
tree = bot.tree


@tree.error
async def err_handle(i: Interaction, e: app_commands.AppCommandError):
    user_locale = await get_user_locale(i.user.id, bot.db)
    embed = error_embed(message=text_map.get(
        513, i.locale, user_locale))
    embed.set_author(name=text_map.get(
        135, i.locale, user_locale), icon_url=i.user.avatar)
    traceback_message = traceback.format_exc()
    view = DebugView(traceback_message)
    seria = bot.get_user(410036441129943050)
    try:
        await i.channel.send(embed=embed, view=view)
    except Forbidden:
        pass
    
    embed.set_footer(text=f'{i.user.name}#{i.user.discriminator} {i.user.id}')
    await seria.send(embed=embed, view=view)

bot.run(token)
