import ast
import functools
import importlib
import pickle
import sys
import dateutil.parser
from pathlib import Path
from typing import Optional

import asqlite
import git
from discord.app_commands import locale_str as _
from discord.errors import Forbidden
from discord.ext import commands
from diskcache import FanoutCache

from apps.genshin.custom_model import ShenheBot
from utility.utils import DefaultEmbed, ErrorEmbed, log


class AdminCog(commands.Cog, name="admin"):
    def __init__(self, bot):
        self.bot: ShenheBot = bot

    @commands.is_owner()
    @commands.command(name="maintenance")
    async def maintenance(self, ctx: commands.Context, time: Optional[str] = ""):
        self.bot.maintenance = not self.bot.maintenance
        if time != "":
            self.bot.maintenance_time = time
        await ctx.send("success")

    @commands.is_owner()
    @commands.command(name="reload")
    async def reload(self, ctx: commands.Context):
        message = await ctx.send("pulling from Git...")
        if not self.bot.debug:
            g = git.cmd.Git(Path(__file__).parent.parent)
            pull = functools.partial(g.pull)
            await self.bot.loop.run_in_executor(None, pull)
        modules = list(sys.modules.values())
        for _ in range(2):
            await message.edit(content="reloading modules...")
            for module in modules:
                if module is None:
                    continue
                if module.__name__.startswith(
                    (
                        "asset",
                        "config",
                        "UI_base_models",
                        "exceptions",
                        "ambr.",
                        "apps.",
                        "cogs.",
                        "data.",
                        "text_maps.",
                        "UI_elements.",
                        "utility.",
                        "yelan.",
                    )
                ):
                    try:
                        importlib.reload(module)
                    except Exception as e:
                        return await ctx.send(
                            embed=ErrorEmbed(module.__name__, f"```{e}```"),
                            ephemeral=True,
                        )

        await message.edit(content="reloading cogs...")
        for filepath in Path("./cogs").glob("**/*.py"):
            cog_name = Path(filepath).stem
            if cog_name in ["login", "grafana"]:
                continue
            try:
                await self.bot.reload_extension(f"cogs.{cog_name}")
            except Exception as e:
                return await message.edit(
                    embed=ErrorEmbed(cog_name, f"```{e}```"),
                )
        await message.edit(content="bot reloaded")

    @commands.is_owner()
    @commands.command(name="sync")
    async def sync(self, ctx: commands.Context):
        await self.bot.tree.sync()
        await ctx.send("commands synced")

    @commands.is_owner()
    @commands.command(name="dm")
    async def direct_message(
        self, ctx: commands.Context, user: commands.UserConverter, *, message: str
    ):
        embed = DefaultEmbed(description=message)
        embed.set_author(
            name=ctx.author.name + "#" + ctx.author.discriminator,
            icon_url=ctx.author.display_avatar.url,
        )
        try:
            await user.send(embed=embed)
        except Forbidden:
            await ctx.send("user has DMs disabled")
        else:
            await ctx.send("message sent")

    @commands.is_owner()
    @commands.command(name="transfer-enka-cache")
    async def transfer_enka_cache(self, ctx: commands.Context, uid: int):
        await ctx.send("getting old cache...")
        en_cache = FanoutCache("data/cache/enka_eng_cache")
        cache = FanoutCache("data/cache/enka_data_cache")
        en_cache_data = en_cache.get(uid)
        cache_data = cache.get(uid)
        await self.bot.pool.execute(
            "INSERT OR REPLACE INTO enka_cache (uid, en_data, data) VALUES ($1, $2, $3)",
            uid,
            pickle.dumps(en_cache_data),
            pickle.dumps(cache_data),
        )
        await ctx.send("done")

    @commands.is_owner()
    @commands.command(name="migrate-db")
    async def migrate_db(self, ctx: commands.Context, table_name: str):
        await ctx.send("migrating...")
        async with asqlite.connect("shenhe.db") as sqlite:
            if table_name == "user_accounts":
                # user_accounts
                user_accounts = await sqlite.fetchall("SELECT * FROM user_accounts")
                for user_account in user_accounts:
                    try:
                        await self.bot.pool.execute(
                            """
                            INSERT INTO user_accounts
                            (uid, user_id, ltuid, ltoken, cookie_token,
                            current, nickname, daily_checkin, china)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                            ON CONFLICT (uid, user_id) DO NOTHING
                            """,
                            user_account["uid"],
                            user_account["user_id"],
                            str(user_account["ltuid"]),
                            str(user_account["ltoken"]),
                            user_account["cookie_token"],
                            True if user_account["current"] == 1 else False,
                            user_account["nickname"],
                            True if user_account["daily_checkin"] == 1 else False,
                            True if user_account["china"] == 1 else False,
                        )
                        log.info(f"migrated user_account {user_account['uid']}")
                    except Exception as e:
                        log.warning(
                            f"failed to migrate user_account {user_account['uid']}: {e}"
                        )
                log.info("migrated user_accounts")
            elif table_name == "user_settings":
                # user_settings
                user_settings = await sqlite.fetchall("SELECT * FROM user_settings")
                for user_setting in user_settings:
                    try:
                        await self.bot.pool.execute(
                            """
                            INSERT INTO user_settings
                            (user_id, lang, dark_mode, notification, auto_redeem)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (user_id) DO NOTHING
                            """,
                            user_setting["user_id"],
                            None
                            if user_setting["lang"] == "en-US"
                            else user_setting["lang"],
                            True if user_setting["dark_mode"] == 1 else False,
                            True if user_setting["notification"] == 1 else False,
                            True if user_setting["auto_redeem"] == 1 else False,
                        )
                        log.info(f"migrated user_setting {user_setting['user_id']}")
                    except Exception as e:
                        log.warning(
                            f"failed to migrate user_setting {user_setting['user_id']}: {e}"
                        )
                log.info("migrated user_settings")
            elif table_name == "resin_notification":
                # resin_notification
                resin_notification = await sqlite.fetchall(
                    "SELECT * FROM resin_notification"
                )
                # columns: uid, user_id, last_notif, current, max, toggle, threshold
                for resin in resin_notification:
                    try:
                        await self.bot.pool.execute(
                            """
                            INSERT INTO resin_notification
                            (uid, user_id, last_notif, current, max, toggle, threshold)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            ON CONFLICT (uid, user_id) DO NOTHING
                            """,
                            resin["uid"],
                            resin["user_id"],
                            resin["last_notif"],
                            resin["current"],
                            resin["max"],
                            True if resin["toggle"] == 1 else False,
                            resin["threshold"],
                        )
                        log.info(f"migrated resin_notification {resin['uid']}")
                    except Exception as e:
                        log.warning(
                            f"failed to migrate resin_notification {resin['uid']}: {e}"
                        )
                log.info("migrated resin_notification")
            elif table_name == "pot_notification":
                # pot_notification
                pot_notification = await sqlite.fetchall("SELECT * FROM pot_notification")
                # columns: uid, user_id, last_notif, current, max, toggle, threshold
                for pot in pot_notification:
                    try:
                        await self.bot.pool.execute(
                            """
                            INSERT INTO pot_notification
                            (uid, user_id, last_notif, current, max, toggle, threshold)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            ON CONFLICT (uid, user_id) DO NOTHING
                            """,
                            pot["uid"],
                            pot["user_id"],
                            pot["last_notif"],
                            pot["current"],
                            pot["max"],
                            True if pot["toggle"] == 1 else False,
                            pot["threshold"],
                        )
                        log.info(f"migrated pot_notification {pot['uid']}")
                    except Exception as e:
                        log.warning(f"failed to migrate pot_notification {pot['uid']}: {e}")
                log.info("migrated pot_notification")
            elif table_name == "pt_notification":
                # pt_notification
                pt_notification = await sqlite.fetchall("SELECT * FROM pt_notification")
                # columns: uid, user_id, last_notif, current, max, toggle
                for pt in pt_notification:
                    try:
                        await self.bot.pool.execute(
                            """
                            INSERT INTO pt_notification
                            (uid, user_id, last_notif, current, max, toggle)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT (uid, user_id) DO NOTHING
                            """,
                            pt["uid"],
                            pt["user_id"],
                            pt["last_notif"],
                            pt["current"],
                            pt["max"],
                            True if pt["toggle"] == 1 else False,
                        )
                        log.info(f"migrated pt_notification {pt['uid']}")
                    except Exception as e:
                        log.warning(f"failed to migrate pt_notification {pt['uid']}: {e}")
                log.info("migrated pt_notification")
            elif table_name == "weapon_notification":
                # weapon_notification
                weapon_notification = await sqlite.fetchall(
                    "SELECT * FROM weapon_notification"
                )
                # columns: user_id, toggle, item_list
                for weapon in weapon_notification:
                    try:
                        await self.bot.pool.execute(
                            """
                            INSERT INTO weapon_notification
                            (user_id, toggle, item_list)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (user_id) DO NOTHING
                            """,
                            weapon["user_id"],
                            True if weapon["toggle"] == 1 else False,
                            ast.literal_eval(weapon["weapon_list"]),
                        )
                        log.info(f"migrated weapon_notification {weapon['user_id']}")
                    except Exception as e:
                        log.warning(
                            f"failed to migrate weapon_notification {weapon['user_id']}: {e}"
                        )
                log.info("migrated weapon_notification")
            elif table_name == "talent_notification":
                # talent_notification
                talent_notification = await sqlite.fetchall(
                    "SELECT * FROM talent_notification"
                )
                # columns: user_id, toggle, item_list
                for talent in talent_notification:
                    try:
                        await self.bot.pool.execute(
                            """
                            INSERT INTO talent_notification
                            (user_id, toggle, item_list)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (user_id) DO NOTHING
                            """,
                            talent["user_id"],
                            True if talent["toggle"] == 1 else False,
                            ast.literal_eval(talent["character_list"]),
                        )
                        log.info(f"migrated talent_notification {talent['user_id']}")
                    except Exception as e:
                        log.warning(
                            f"failed to migrate talent_notification {talent['user_id']}: {e}"
                        )
                log.info("migrated talent_notification")
            elif table_name == "abyss_character_leaderboard":
                # abyss_character_leaderboard
                abyss_character_leaderboard = await sqlite.fetchall(
                    "SELECT * FROM abyss_character_leaderboard"
                )
                # columns: uid, season, characters, user_id
                for leaderboard in abyss_character_leaderboard:
                    try:
                        await self.bot.pool.execute(
                            """
                            INSERT INTO abyss_character_leaderboard
                            (uid, season, characters, user_id)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (uid, season) DO NOTHING
                            """,
                            leaderboard["uid"],
                            leaderboard["season"],
                            ast.literal_eval(leaderboard["characters"]),
                            leaderboard["user_id"],
                        )
                        log.info(
                            f"migrated abyss_character_leaderboard {leaderboard['uid']}"
                        )
                    except Exception as e:
                        log.warning(
                            f"failed to migrate abyss_character_leaderboard {leaderboard['uid']}: {e}"
                        )
                log.info("migrated abyss_character_leaderboard")
            elif table_name == "abyss_leaderboard":
                # abyss_leaderboard
                abyss_leaderboard = await sqlite.fetchall("SELECT * FROM abyss_leaderboard")
                # columns: uid, single_strike, floor, stars_collected, user_name, user_id, season, runs, wins, level, icon_url, const, refine, c_level, c_icon
                for leaderboard in abyss_leaderboard:
                    try:
                        await self.bot.pool.execute(
                            """
                            INSERT INTO abyss_leaderboard
                            (uid, single_strike, floor, stars_collected, user_name, user_id, season, runs, wins, level, icon_url, const, refine, c_level, c_icon)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                            ON CONFLICT (uid, season) DO NOTHING
                            """,
                            leaderboard["uid"],
                            leaderboard["single_strike"],
                            leaderboard["floor"],
                            leaderboard["stars_collected"],
                            leaderboard["user_name"],
                            leaderboard["user_id"],
                            leaderboard["season"],
                            leaderboard["runs"],
                            leaderboard["wins"],
                            leaderboard["level"],
                            leaderboard["icon_url"],
                            leaderboard["const"],
                            leaderboard["refine"],
                            leaderboard["c_level"],
                            leaderboard["c_icon"],
                        )
                        log.info(f"migrated abyss_leaderboard {leaderboard['uid']}")
                    except Exception as e:
                        log.warning(
                            f"failed to migrate abyss_leaderboard {leaderboard['uid']}: {e}"
                        )
                log.info("migrated abyss_leaderboard")
            elif table_name == "custom_image":
                # custom_image
                custom_image = await sqlite.fetchall("SELECT * FROM custom_image")
                # columns: user_id, character_id, image_url, nickname, current
                for image in custom_image:
                    try:
                        await self.bot.pool.execute(
                            """
                            INSERT INTO custom_image
                            (user_id, character_id, image_url, nickname, current)
                            VALUES ($1, $2, $3, $4, $5)
                            """,
                            image["user_id"],
                            image["character_id"],
                            image["image_url"],
                            image["nickname"],
                            True if image["current"] == 1 else False,
                        )
                        log.info(
                            f"migrated custom_image {image['user_id']} {image['image_url']}"
                        )
                    except Exception as e:
                        log.warning(
                            f"failed to migrate custom_image {image['user_id']} {image['image_url']}: {e}"
                        )
                log.info("migrated custom_image")
            elif table_name == "enka_cache":
                # enka_cache
                enka_cache = await sqlite.fetchall("SELECT * FROM enka_cache")
                for cache in enka_cache:
                    try:
                        await self.bot.pool.execute(
                            """
                            INSERT INTO enka_cache
                            (uid, en_data, data)
                            VALUES ($1, $2, $3)
                            """,
                            cache["uid"],
                            cache["en_data"],
                            cache["data"],
                        )
                        log.info(f"migrated enka_cache {cache['uid']}")
                    except Exception as e:
                        log.warning(f"failed to migrate enka_cache {cache['uid']}: {e}")
                log.info("migrated enka_cache")
            elif table_name == "todo":
                # todo
                todos = await sqlite.fetchall("SELECT * FROM todo")
                for todo in todos:
                    try:
                        await self.bot.pool.execute(
                            """
                            INSERT INTO todo
                            (user_id, item, count, max)
                            VALUES ($1, $2, $3, $4)
                            """,
                            todo["user_id"],
                            todo["todo"],
                            todo["count"],
                            todo["max"],
                        )
                        log.info(f"migrated todo {todo['user_id']}")
                    except Exception as e:
                        log.warning(f"failed to migrate todo {todo['user_id']}: {e}")
                log.info("migrated todo")
            elif table_name == "wish_history":
                # wish_history
                wish_history = await sqlite.fetchall("SELECT * FROM wish_history")
                # columns: wish_id(int), user_id(int), uid(int), wish_name(str), wish_rarity(int), wish_time(datetime), wish_type(str), wish_banner_type(int), item_id(int), pity_pull(int)
                for wish in wish_history:
                    try:
                        await self.bot.pool.execute(
                            """
                            INSERT INTO wish_history
                            (wish_id, user_id, uid, wish_name, wish_rarity, wish_time, wish_type, wish_banner_type, item_id, pity_pull)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                            """,
                            wish["wish_id"],
                            wish["user_id"],
                            wish["uid"],
                            wish["wish_name"],
                            wish["wish_rarity"],
                            dateutil.parser.parse(wish["wish_time"]),
                            wish["wish_type"],
                            wish["wish_banner_type"],
                            wish["item_id"],
                            wish["pity_pull"],
                        )
                        log.info(f"migrated wish_history {wish['wish_id']}")
                    except Exception as e:
                        log.warning(f"failed to migrate wish_history {wish['wish_id']}: {e}")

async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(AdminCog(bot))
