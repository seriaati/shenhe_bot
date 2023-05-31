import discord
from discord import app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands

import ui
from apps.db.tables.user_settings import Settings
from dev.models import Inter


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help", description=_("View a list of all commands", hash=486)
    )
    async def help(self, inter: discord.Interaction):
        i: Inter = inter  # type: ignore
        lang = await i.client.db.settings.get(i.user.id, Settings.LANG) or str(i.locale)
        view = ui.HelpView(lang)
        await i.response.send_message(view=view)
        view.message = await i.original_response()


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(HelpCog(bot))
