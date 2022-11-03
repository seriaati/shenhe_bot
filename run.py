# shenhe-bot by seria

import asyncio
import getpass
import os
from pathlib import Path
from typing import Optional
import aiohttp
import aiosqlite
import genshin
import sentry_sdk
from cachetools import TTLCache
from discord import Intents, Interaction, Locale, Message, app_commands
from discord.app_commands import TranslationContext, locale_str
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv
from typing import Dict

from discord import WebhookMessage, app_commands
from discord.ext import commands

from logingateway import HuTaoLoginAPI
from logingateway.model import Player, Ready, LoginMethod
from UI_elements.others.ManageAccounts import return_accounts

from apps.text_map.text_map_app import text_map
from UI_base_models import global_error_handler
from utility.utils import default_embed, error_embed, log, sentry_logging

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


class Translator(app_commands.Translator):
    async def translate(
        self, string: locale_str, locale: Locale, context: TranslationContext
    ) -> Optional[str]:
        try:
            text = text_map.get(string.extras["hash"], locale)
            if text == "":
                return None
            if len(text.split(" ")) == 1:  # is a word
                return text.lower()
            else:  # is a setence
                return text
        except KeyError:
            return None


class ShenheBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            application_id=application_id,
            chunk_guilds_at_startup=False,
        )

    async def setup_hook(self) -> None:
        # cache
        self.enka_card_cache = TTLCache(maxsize=512, ttl=120)
        self.stats_card_cache = TTLCache(maxsize=512, ttl=120)
        self.area_card_cache = TTLCache(maxsize=512, ttl=120)
        self.abyss_overview_card_cache = TTLCache(maxsize=512, ttl=120)
        self.abyss_floor_card_cache = TTLCache(maxsize=512, ttl=120)
        self.abyss_one_page_cache = TTLCache(maxsize=512, ttl=120)

        # bot variables
        self.maintenance = False
        self.maintenance_time = ""
        self.session = aiohttp.ClientSession()
        self.db = await aiosqlite.connect("shenhe.db")
        self.main_db = await aiosqlite.connect("../shenhe_main/main.db")
        self.backup_db = await aiosqlite.connect("backup.db")
        self.debug = debug
        self.gateway = HuTaoLoginAPI(
            client_id=os.getenv("HUTAO_CLIENT_ID"),
            client_secret=os.getenv("HUTAO_CLIENT_SECRET"),
        )
        self.tokenStore: Dict[str, WebhookMessage] = {}
        self.gateway.ready(self.gateway_connect)
        self.gateway.player(self.gateway_player)

        c = await self.db.cursor()
        cookie_list = []
        async with self.db.execute(
            "SELECT uid, ltuid, ltoken FROM user_accounts WHERE china = 0 AND ltoken IS NOT NULL AND ltuid IS NOT NULL AND uid IS NOT NULL"
        ) as c:
            data = await c.fetchall()
        for _, tpl in enumerate(data):
            uid = tpl[0]
            if str(uid) in ["1", "2", "5"]:
                continue
            ltuid = tpl[1]
            ltoken = tpl[2]
            cookie = {"ltuid": int(ltuid), "ltoken": ltoken}
            if cookie in cookie_list:
                continue
            cookie_list.append(cookie)
        self.genshin_client = genshin.Client(cookie_list)

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
        self.gateway.start()

    async def gateway_connect(self, data: Ready):
        log.info(f"[System][Hutao Login Gateway] Connected")

    async def gateway_player(self, data: Player):
        if not data.token in self.tokenStore:
            return

        ctx = self.tokenStore[data.token]
        log.info(f"[System][Hutao Login Gateway] {data}")
        uid = data.genshin.uid
        user_id = data.genshin.userid
        if data.genshin.login_type == LoginMethod.UID:
            cookie = {
                "ltuid": None,
                "ltoken": None,
                "cookie_token": None,
            }
        else:
            cookie = {
                "ltuid": data.genshin.ltuid,
                "ltoken": data.genshin.ltoken,
                "cookie_token": data.genshin.cookie_token,
            }
        china = 1 if str(uid)[0] in [1, 2, 5] else 0
        await self.db.execute(
            "INSERT INTO user_accounts (uid, user_id, ltuid, ltoken, cookie_token, china) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (uid, user_id) DO UPDATE SET ltuid = ?, ltoken = ?, cookie_token = ? WHERE uid = ? AND user_id = ?",
            (
                uid,
                user_id,
                cookie["ltuid"],
                cookie["ltoken"],
                cookie["cookie_token"],
                china,
                cookie["ltuid"],
                cookie["ltoken"],
                cookie["cookie_token"],
                uid,
                user_id,
            ),
        )
        await self.db.commit()

        await ctx["message"].edit(
            embed=default_embed().set_author(
                name=text_map.get(39, ctx["locale"]),
                icon_url=ctx["author"].display_avatar.url,
            ),
            view=None,
        )

        await asyncio.sleep(1)
        await return_accounts(ctx["interaction"])

    async def on_message(self, message: Message):
        if message.author.id == self.user.id:
            return
        await self.process_commands(message)

    async def on_command_error(self, ctx, error) -> None:
        if hasattr(ctx.command, "on_error"):
            return
        ignored = (
            commands.CommandNotFound,
            app_commands.errors.CheckFailure,
            commands.NotOwner,
        )
        error = getattr(error, "original", error)
        if isinstance(error, ignored):
            return
        else:
            log.warning(f"[{ctx.author.id}]on_command_error: {error}")
            sentry_sdk.capture_exception(error)

    async def close(self) -> None:
        await self.db.close()
        await self.main_db.close()
        await self.backup_db.close()
        await self.session.close()
        await self.close()


sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"), integrations=[sentry_logging], traces_sample_rate=1.0
)

bot = ShenheBot()


@bot.before_invoke
async def before_invoke(ctx: Context):
    if ctx.guild is not None and not ctx.guild.chunked:
        await ctx.guild.chunk()


@bot.listen()
async def on_message_edit(before: Message, after: Message):
    if before.content == after.content:
        return
    if before.author.id != bot.owner_id:
        return
    return await bot.process_commands(after)


@bot.listen()
async def on_interaction(i: Interaction):
    if i.command is None:
        return

    c = await bot.db.cursor()
    await c.execute(
        "INSERT INTO user_settings (user_id) VALUES (?) ON CONFLICT (user_id) DO NOTHING",
        (i.user.id,),
    )
    await bot.db.commit()
    await c.close()

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


tree = bot.tree


async def check_maintenance(i: Interaction, /) -> bool:
    if i.user.id == 410036441129943050:
        return True
    else:
        if i.client.maintenance:
            await i.response.send_message(
                embed=error_embed(
                    "申鶴正在維護中\nShenhe is under maintenance",
                    f"預計將在 {i.client.maintenance_time} 恢復服務\nEstimated to be back online {i.client.maintenance_time}",
                ).set_thumbnail(url=i.client.user.avatar.url),
                ephemeral=True,
            )
            return False
        else:
            return True


tree.interaction_check = check_maintenance


@tree.error
async def on_error(i: Interaction, e: app_commands.AppCommandError):
    await global_error_handler(i, e)


if not debug:
    import uvloop  # type: ignore

    uvloop.install()
bot.run(token=token)
