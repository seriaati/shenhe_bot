# shenhe-bot by seria

import getpass
import os
from pathlib import Path
from typing import Optional
import aiohttp
import aiosqlite
import sentry_sdk
from discord import Game, Intents, Interaction, Locale, Message, Status, app_commands
from discord.app_commands import TranslationContext, locale_str
from discord.ext import commands
from dotenv import load_dotenv
from pyppeteer import launch

from apps.text_map.text_map_app import text_map
from UI_elements.others import Roles
from utility.utils import log, sentry_logging

load_dotenv()

user_name = getpass.getuser()

if user_name == "seria":
    token = os.getenv("YAE_TOKEN")
    debug = True
    application_id = os.getenv("YAE_APP_ID")
else:
    token = os.getenv("SHENHE_BOT_TOKEN")
    debug = False
    application_id = os.getenv("SHENHE_BOT_APP_ID")

prefix = ["?"]
intents = Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True
intents.presences = True


class Translator(app_commands.Translator):
    async def translate(
        self, string: locale_str, locale: Locale, context: TranslationContext
    ) -> Optional[str]:
        try:
            return text_map.get(string.extras["hash"], locale)
        except KeyError:
            return None


class ShenheBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=prefix, intents=intents, application_id=application_id
        )

    async def setup_hook(self) -> None:
        user = getpass.getuser()

        # bot variables
        self.session = aiohttp.ClientSession()
        self.db = await aiosqlite.connect("shenhe.db")
        self.main_db = await aiosqlite.connect(f"C:/Users/{user}/shenhe_main/main.db")
        self.browser = await launch(
            {
                "headless": True,
                "autoClose": False,
                "args": [
                    '--proxy-server="direct://"',
                    "--proxy-bypass-list=*",
                    "--no-sandbox",
                    "--start-maximized",
                ],
            }
        )
        self.debug = debug

        # load jishaku
        await self.load_extension("jishaku")

        # load cogs
        for filepath in Path("./cogs").glob("**/*.py"):
            cog_name = Path(filepath).stem
            await self.load_extension(f"cogs.{cog_name}")

        # load persistent views
        self.add_view(Roles.View())

    async def on_ready(self):
        await self.change_presence(status=Status.online, activity=Game(name=f"/help"))
        tree = self.tree
        await tree.set_translator(Translator())
        log.info(f"[INFO][System]on_ready: You have logged in as {self.user}")
        log.info(f"[INFO][System]on_ready: Total {len(self.guilds)} servers connected")

    async def on_message(self, message: Message):
        if message.author.id == self.user.id:
            return
        await self.process_commands(message)

    async def on_command_error(self, ctx, error) -> None:
        if hasattr(ctx.command, "on_error"):
            return
        ignored = (commands.CommandNotFound, app_commands.errors.CheckFailure)
        error = getattr(error, "original", error)
        if isinstance(error, ignored):
            return
        else:
            log.warning(f"[EXCEPTION][{ctx.author.id}]on_command_error: {error}")
            sentry_sdk.capture_exception(error)

    async def close(self) -> None:
        await self.db.close()
        await self.main_db.close()
        await self.browser.close()
        await self.session.close()


sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"), integrations=[sentry_logging], traces_sample_rate=1.0
)

bot = ShenheBot()
tree = bot.tree


@tree.error
async def on_error(i: Interaction, e: app_commands.AppCommandError):
    log.warning(f"[EXCEPTION][{i.user.id}]{type(e)}: {e}")
    sentry_sdk.capture_exception(e)


bot.run(token)
