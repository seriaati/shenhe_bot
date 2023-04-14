# shenhe-bot by seria

import argparse
import asyncio
import json
import os
import platform
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
import aiohttp
import asyncpg
import discord
import sentry_sdk
from discord import app_commands
from discord.ext import commands
from discord.ext.prometheus import PrometheusLoggingHandler
from dotenv import load_dotenv

import dev.models as models
from apps.genshin import launch_browsers, launch_debug_browser
from apps.genshin_data.text_maps import load_text_maps
from apps.text_map import text_map
from dev.base_ui import (get_error_handle_embed, global_error_handler,
                         support_server_view)
from dev.exceptions import FeatureDisabled, Maintenance
from dev.models import BotModel
from utils import log, sentry_logging

load_dotenv()
log.getLogger().addHandler(PrometheusLoggingHandler())

parser = argparse.ArgumentParser()
parser.add_argument(
    "--env",
    choices=("production", "testing", "development"),
    required=True,
    help="The environment to run the application in",
)
args = parser.parse_args()

if args.env == 'production':
    token = os.getenv("SHENHE_BOT_TOKEN")
    debug = False
    databse_url = os.getenv("SHENHE_BOT_DATABASE_URL")
elif args.env == 'test':
    token = os.getenv("SHENHE_TEST_TOKEN")
    debug = False
    databse_url = os.getenv("SHENHE_BOT_DATABASE_URL")
elif args.env == 'development':
    token = os.getenv("YAE_TOKEN")
    debug = True
    databse_url = os.getenv("YAE_DATABASE_URL")
else:
    print('Invalid environment specified')
    exit(1)


class Translator(app_commands.Translator):
    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        _: app_commands.TranslationContext,
    ) -> Optional[str]:
        try:
            text = text_map.get(string.extras["hash"], locale)
            if len(text.split(" ")) == 1:
                return text.lower()
            if text == "":
                return None

            # hard code stuff
            if str(locale) == "vi" and string.extras["hash"] == 105:
                return "nhân-vật"

            return text
        except KeyError:
            return None


class ShenheCommandTree(app_commands.CommandTree):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(bot)

    async def sync(
        self, *, guild: Optional[discord.abc.Snowflake] = None
    ) -> List[app_commands.AppCommand]:
        synced = await super().sync(guild=guild)
        log.info(f"[System]sync: Synced {len(synced)} commands")
        if synced:
            command_map: Dict[str, int] = {}
            for command in synced:
                command_map[command.name] = command.id
            async with aiofiles.open("command_map.json", "w") as f:
                await f.write(json.dumps(command_map))

        return synced

    async def interaction_check(self, i: discord.Interaction, /) -> bool:
        client: BotModel = i.client  # type: ignore

        if i.guild is not None and not i.guild.chunked:
            await i.guild.chunk()

        if i.user.id in (410036441129943050,):
            return True
        if i.user.id in (188109365671100416, 738362958253522976, 753937213032628327):
            return False

        if isinstance(i.command, app_commands.Command):
            if i.command.parent:
                command_name = f"{i.command.parent.name} {i.command.name}"
            else:
                command_name = i.command.name
            if command_name in client.disabled_commands:
                embed = get_error_handle_embed(i.user, FeatureDisabled(), i.locale)
                try:
                    await i.response.send_message(
                        embed=embed, ephemeral=True, view=support_server_view(i.locale)
                    )
                except Exception:  # skipcq: PYL-W0703
                    pass
                return False

        if client.maintenance:
            embed = get_error_handle_embed(i.user, Maintenance(), i.locale)
            try:
                await i.response.send_message(
                    embed=embed, ephemeral=True, view=support_server_view(i.locale)
                )
            except Exception:  # skipcq: PYL-W0703
                pass
            return False
        return True

    async def on_error(
        self, i: discord.Interaction, e: app_commands.AppCommandError, /
    ) -> None:
        return await global_error_handler(i, e)  # type: ignore


class Shenhe(BotModel):
    def __init__(self, session: aiohttp.ClientSession, pool: asyncpg.Pool):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            chunk_guilds_at_startup=False,
            activity=discord.Game(name="/help | shenhe.bot.nu"),
            tree_cls=ShenheCommandTree,
        )

        self.session = session
        self.pool = pool
        self.debug = debug

    async def setup_hook(self) -> None:
        # load jishaku
        await self.load_extension("jishaku")

        # load cogs
        for filepath in Path("./cogs").glob("**/*.py"):
            cog_name = Path(filepath).stem
            try:
                await self.load_extension(f"cogs.{cog_name}")
            except Exception as e:  # skipcq: PYL-W0703
                log.warning(
                    f"[Cog Load Error]: [Cog name]{cog_name} [Exception]{e}", exc_info=e
                )

        self.gd_text_map = load_text_maps()

    async def on_ready(self):
        tree = self.tree
        await tree.set_translator(Translator())
        log.info(f"[System]on_ready: Logged in as {self.user}")
        log.info(f"[System]on_ready: Total {len(self.guilds)} servers connected")
        if not self.debug:
            try:
                self.browsers = await launch_browsers()
            except Exception as e:  # skipcq: PYL-W0703
                log.warning("[System]on_ready: Launch browsers failed", exc_info=e)
        if self.debug and self.launch_browser_in_debug:
            self.browsers = {"en-US": await launch_debug_browser()}

    async def on_message(self, message: discord.Message):
        if self.user is None:
            return
        if message.author.id == self.user.id:
            return
        await self.process_commands(message)

    async def on_command_error(self, ctx, error) -> None:
        if hasattr(ctx.command, "on_error"):
            return
        ignored = (
            commands.CommandNotFound,
            commands.NotOwner,
        )
        error = getattr(error, "original", error)
        if isinstance(error, ignored):
            return
        log.warning(f"[{ctx.author.id}]on_command_error: {error}", exc_info=error)

    async def close(self) -> None:
        await self.session.close()
        if hasattr(self, "browsers"):
            for browser in self.browsers.values():
                await browser.close()


sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"), integrations=[sentry_logging], traces_sample_rate=1.0
)

if platform.system() == "Linux":
    import uvloop  # type: ignore

    uvloop.install()


async def main() -> None:
    if not token:
        raise AssertionError

    try:
        pool = await asyncpg.create_pool(databse_url)
    except Exception as e:  # skipcq: PYL-W0703
        log.error("Failed to connect to database", exc_info=e)
        return
    if not pool:
        raise AssertionError

    session = aiohttp.ClientSession()
    bot = Shenhe(session=session, pool=pool)

    @bot.before_invoke
    async def before_invoke(ctx: commands.Context):
        if ctx.guild is not None and not ctx.guild.chunked:
            await ctx.guild.chunk()

    @bot.listen()
    async def on_message_edit(before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return
        if before.author.id != bot.owner_id:
            return
        return await bot.process_commands(after)

    @bot.listen()
    async def on_interaction(i: models.Inter):
        if i.command is None:
            return

        if isinstance(i.command, app_commands.Command):
            namespace_str = "" if not i.namespace.__dict__ else ": "
            for key, value in i.namespace.__dict__.items():
                namespace_str += f"[{key}] {value} "
            if i.command.parent is None:
                log.info(f"[Command][{i.user.id}][{i.command.name}]{namespace_str}")
            else:
                log.info(
                    f"[Command][{i.user.id}][{i.command.parent.name} {i.command.name}]{namespace_str}"
                )
        else:
            log.info(f"[Context Menu Command][{i.user.id}][{i.command.name}]")

    async with (session, bot, pool):
        try:
            await bot.start(token)
        except KeyboardInterrupt:
            return
        except Exception as e:  # skipcq: PYL-W0703
            log.error("Failed to start bot", exc_info=e)
            return


asyncio.run(main())
