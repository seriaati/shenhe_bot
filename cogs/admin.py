import functools
import importlib
import sys
from pathlib import Path
from typing import Optional

import git
from discord import Interaction, app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands

from apps.genshin.custom_model import ShenheBot
from UI_elements.admin import Annouce
from utility.utils import error_embed


def is_seria():
    async def predicate(i: Interaction) -> bool:
        if i.user.id != 410036441129943050:
            await i.response.send_message(
                embed=error_embed(message="你不是小雪本人").set_author(
                    name="生物驗證失敗", icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
        return i.user.id == 410036441129943050

    return app_commands.check(predicate)


class AdminCog(commands.Cog, name="admin"):
    def __init__(self, bot):
        self.bot: ShenheBot = bot

    @is_seria()
    @app_commands.command(
        name="maintenance", description=_("Owner usage only", hash=496)
    )
    async def maintenance(self, i: Interaction, time: Optional[str] = ""):
        self.bot.maintenance = not self.bot.maintenance
        if time != "":
            self.bot.maintenance_time = time
        await i.response.send_message("success", ephemeral=True)

    @is_seria()
    @app_commands.command(name="reload", description=_("Owner usage only", hash=496))
    async def reload(self, i: Interaction):
        await i.response.defer(ephemeral=True)
        if not self.bot.debug:
            g = git.cmd.Git(Path(__file__).parent.parent)
            pull = functools.partial(g.pull)
            await self.bot.loop.run_in_executor(None, pull)
            await i.edit_original_response(content="Git Pulled")
        modules = list(sys.modules.values())
        for _ in range(2):
            for module in modules:
                if module is None:
                    continue
                if module.__name__.startswith(
                    (
                        "assets"
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
                        return await i.followup.send(
                            embed=error_embed(module.__name__, f"```{e}```"),
                            ephemeral=True,
                        )
            await i.edit_original_response(content=f"reloaded modules ({_+1}/2)")
        for filepath in Path("./cogs").glob("**/*.py"):
            cog_name = Path(filepath).stem
            try:
                await self.bot.reload_extension(f"cogs.{cog_name}")
            except Exception as e:
                return await i.followup.send(
                    embed=error_embed(cog_name, f"```{e}```"),
                    ephemeral=True,
                )
        await i.edit_original_response(content="reloaded cogs")

    @is_seria()
    @app_commands.command(name="sync", description=_("Owner usage only", hash=496))
    async def roles(self, i: Interaction):
        await i.response.defer()
        await self.bot.tree.sync()
        await i.followup.send("sync done")

    @is_seria()
    @app_commands.command(name="annouce", description=_("Owner usage only", hash=496))
    async def annouce(self, i: Interaction):
        await i.response.send_modal(Annouce.Modal())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
