# shenhe-bot by seria

import asyncio
import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import aiofiles
import json

import aiohttp
import asyncpg
import sentry_sdk
from cachetools import TTLCache
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.prometheus import PrometheusLoggingHandler
from dotenv import load_dotenv

from apps.genshin.browser import launch_browsers
from apps.genshin_data.text_maps import load_text_maps
from apps.text_map.text_map_app import text_map
from UI_base_models import global_error_handler
from utility.utils import ErrorEmbed, log, sentry_logging

load_dotenv()
log.getLogger().addHandler(PrometheusLoggingHandler())

if platform.system() == "Windows":
    token = os.getenv("YAE_TOKEN")
    debug = True
    application_id = os.getenv("YAE_APP_ID")
else:
    token = os.getenv("SHENHE_BOT_TOKEN")
    debug = False
    application_id = os.getenv("SHENHE_BOT_APP_ID")


class Translator(app_commands.Translator):
    async def translate(
        self, string: app_commands.locale_str, locale: discord.Locale, _: app_commands.TranslationContext
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
    
    async def sync(self, *, guild: Optional[discord.abc.Snowflake] = None) -> List[app_commands.AppCommand]:
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
        if i.guild is not None and not i.guild.chunked:
            await i.guild.chunk()
        
        if i.user.id == 410036441129943050:
            return True
        else:
            if i.client.maintenance: # type: ignore
                await i.response.send_message(
                    embed=ErrorEmbed(
                        "申鶴正在維護中\nShenhe is under maintenance",
                        f"預計將在 {i.client.maintenance_time} 恢復服務\nEstimated to be back online {i.client.maintenance_time}", # type: ignore
                    ).set_thumbnail(
                        url=i.client.user.avatar.url # type: ignore
                    ),
                    ephemeral=True,
                )
                return False
            else:
                return True
    
    async def on_error(self, i: discord.Interaction, e: app_commands.AppCommandError, /) -> None:
        return await global_error_handler(i, e)

class Shenhe(commands.AutoShardedBot):
    def __init__(self, session: aiohttp.ClientSession, pool: asyncpg.Pool):
        intents = discord.Intents.default()
        intents.members = True
        
        self.session = session
        self.pool = pool
        
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            application_id=application_id,
            chunk_guilds_at_startup=False,
            activity=discord.Game(name="/help | shenhe.bot.nu"),
            tree_cls=ShenheCommandTree,
        )

    async def setup_hook(self) -> None:
        # cache
        self.stats_card_cache = TTLCache(maxsize=512, ttl=120)
        self.area_card_cache = TTLCache(maxsize=512, ttl=120)
        self.abyss_overview_card_cache = TTLCache(maxsize=512, ttl=120)
        self.abyss_floor_card_cache = TTLCache(maxsize=512, ttl=120)
        self.abyss_one_page_cache = TTLCache(maxsize=512, ttl=120)

        # bot variables
        self.maintenance = False
        self.maintenance_time = ""
        self.launch_time = datetime.utcnow()
        self.debug = debug
        self.gd_text_map = load_text_maps()

        # load jishaku
        await self.load_extension("jishaku")

        # load cogs
        for filepath in Path("./cogs").glob("**/*.py"):
            cog_name = Path(filepath).stem
            try:
                await self.load_extension(f"cogs.{cog_name}")
            except Exception as e:
                log.warning(f"[Cog Load Error]: [Cog name]{cog_name} [Exception]{e}")
                sentry_sdk.capture_exception(e)

    async def on_ready(self):
        tree = self.tree
        await tree.set_translator(Translator())
        log.info(f"[System]on_ready: Logged in as {self.user}")
        log.info(f"[System]on_ready: Total {len(self.guilds)} servers connected")
        if not self.debug:
            try:
                self.browsers = await launch_browsers()
            except Exception as e:
                log.warning("[System]on_ready: Launch browsers failed", exc_info=e)

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
        else:
            log.warning(f"[{ctx.author.id}]on_command_error: {error}")
            sentry_sdk.capture_exception(error)
    
    async def close(self) -> None:
        await self.session.close()
        if not self.debug:
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
    assert token
    
    try:
        pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
    except Exception as e:
        log.error("Failed to connect to database", exc_info=e)
        return
    assert pool

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
    async def on_interaction(i: discord.Interaction):
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
        except Exception as e:
            log.error("Failed to start bot", exc_info=e)
            return

asyncio.run(main())
