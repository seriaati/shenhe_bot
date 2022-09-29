import importlib
import sys
from typing import List

from discord import Interaction, app_commands
from discord.app_commands import locale_str as _
from discord.app_commands import Choice
from discord.ext import commands
from utility.utils import default_embed, error_embed
from UI_elements.admin import Annouce


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
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @is_seria()
    @app_commands.command(
        name="maintenance", description=_("Admin usage only", hash=496)
    )
    async def maintenance(self, i: Interaction, time: str = None):
        i.client.maintenance = not i.client.maintenance
        if time is not None:
            i.client.maintenance_time = time
        await i.response.send_message("success", ephemeral=True)

    @is_seria()
    @app_commands.command(name="reload", description=_("Admin usage only", hash=496))
    @app_commands.rename(module_name="name")
    async def reload(self, i: Interaction, module_name: str = None):
        await i.response.defer(ephemeral=True)
        if module_name is None:
            modules = list(sys.modules.values())
            for module in modules:
                if module is None:
                    continue
                if module.__name__.startswith(
                    (
                        "ambr."
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
            await i.followup.send("success", ephemeral=True)
        else:
            try:
                importlib.reload(sys.modules[module_name])
            except KeyError:
                return await i.response.send_message(
                    embed=error_embed(message=module_name).set_author(
                        name="Module not found", icon_url=i.user.display_avatar.url
                    ),
                    ephemeral=True,
                )
            else:
                return await i.response.send_message(
                    embed=default_embed(message=module_name).set_author(
                        name="Reload completed", icon_url=i.user.display_avatar.url
                    ),
                    ephemeral=True,
                )

    @reload.autocomplete("module_name")
    async def query_autocomplete(
        self, i: Interaction, current: str
    ) -> List[Choice[str]]:
        query_list = []
        for key in list(sys.modules.keys()):
            query_list.append(key)

        result = [
            app_commands.Choice(name=query, value=query)
            for query in query_list
            if current.lower() in query.lower()
        ]
        return result[:25]

    @is_seria()
    @app_commands.command(name="sync", description=_("Admin usage only", hash=496))
    async def roles(self, i: Interaction):
        await i.response.defer()
        await self.bot.tree.sync()
        await i.followup.send("sync done")

    @is_seria()
    @app_commands.command(name="annouce", description=_("Admin usage only", hash=496))
    async def annouce(self, i: Interaction):
        await i.response.send_modal(Annouce.Modal())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
