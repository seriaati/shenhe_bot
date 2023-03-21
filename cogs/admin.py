import importlib
import pickle
import sys
import traceback
from pathlib import Path
from typing import Optional

from discord.app_commands import locale_str as _
from discord.errors import Forbidden
from discord.ext import commands
from diskcache import FanoutCache

from models import ShenheBot
from utility import DefaultEmbed


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
        message = await ctx.send("Reloading...")

        modules_to_reload = (
            "base_ui",
            "ambr",
            "apps",
            "data",
            "ui",
            "utility",
            "yelan",
            "asset",
            "config",
            "exceptions",
        )
        copy_ = sys.modules.copy()

        for _ in range(2):
            for module_name, module in copy_.items():
                if any(module_name.startswith(name) for name in modules_to_reload):
                    try:
                        importlib.reload(module)
                    except Exception:  # skipcq: PYL-W0703
                        await ctx.send(
                            f"""
                            Error reloading module: {module_name}
                            ```py
                            {traceback.format_exc()}
                            ```
                            """
                        )
                        return

        for cog in Path("cogs").glob("*.py"):
            if cog.stem in ("login", "grafana", "schedule"):
                continue

            try:
                await self.bot.reload_extension(f"cogs.{cog.stem}")
            except Exception:  # skipcq: PYL-W0703
                await ctx.send(
                    f"""
                    Error reloading cog: {cog.stem}
                    ```py
                    {traceback.format_exc()}
                    ```
                    """
                )
                return

        await message.edit(content="Reloaded")

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


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(AdminCog(bot))
