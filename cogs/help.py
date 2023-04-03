import discord
from discord import app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands

import ui
from apps.db import get_user_lang
from dev.models import CustomInteraction


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help", description=_("View a list of all commands", hash=486)
    )
    async def help(self, inter: discord.Interaction):
        i: CustomInteraction = inter  # type: ignore
        user_locale = await get_user_lang(i.user.id, i.client.pool)
        view = ui.HelpView(user_locale or i.locale)
        await i.response.send_message(view=view)
        view.message = await i.original_response()


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(HelpCog(bot))
