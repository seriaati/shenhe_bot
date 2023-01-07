import functools
import importlib
import sys
from pathlib import Path
from typing import Optional

import git
from discord.app_commands import locale_str as _
from discord.ext import commands
from discord.errors import Forbidden

from apps.genshin.custom_model import ShenheBot
from utility.utils import default_embed, error_embed


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
                        "UI_base_models",
                        "exceptions",
                        "ambr.",
                        "cogs.",
                        "apps.",
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
                            embed=error_embed(module.__name__, f"```{e}```"),
                            ephemeral=True,
                        )

        await message.edit(content="reloading cogs...")
        for filepath in Path("./cogs").glob("**/*.py"):
            cog_name = Path(filepath).stem
            if cog_name == "login":
                continue
            try:
                await self.bot.reload_extension(f"cogs.{cog_name}")
            except Exception as e:
                return await message.edit(
                    embed=error_embed(cog_name, f"```{e}```"),
                )
        await message.edit(content="bot reloaded")

    @commands.is_owner()
    @commands.command(name="sync")
    async def sync(self, ctx: commands.Context):
        await self.bot.tree.sync()
        await ctx.send("commands synced")
        
    @commands.is_owner()
    @commands.command(name="dm")
    async def direct_message(self, ctx: commands.Context, user: commands.UserConverter, *, message: str):
        embed = default_embed(message=message)
        embed.set_author(name=ctx.author.name+"#"+ctx.author.discriminator, icon_url=ctx.author.display_avatar.url)
        try:
            await user.send(embed=embed)
        except Forbidden:
            await ctx.send("user has DMs disabled")
        else:
            await ctx.send("message sent")


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(AdminCog(bot))
