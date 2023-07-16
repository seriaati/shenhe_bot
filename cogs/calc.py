from ambr import AmbrAPI
from discord import Interaction, app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands

from apps.db.tables.user_settings import Settings
from apps.text_map import to_ambr_top
from dev.models import BotModel, Inter
from ui.calc import calc_character, calc_weapon


class CalcCog(commands.GroupCog, name="calc"):
    def __init__(self, bot):
        super().__init__()
        self.bot: BotModel = bot

    @app_commands.command(
        name="character",
        description=_("Calculate materials needed for upgrading a character", hash=460),
    )
    async def calc_characters(self, i: Interaction):
        view = calc_character.View()
        view.author = i.user
        await i.response.send_message(view=view)
        view.message = await i.original_response()

    @app_commands.command(
        name="weapon",
        description=_("Calcualte materials needed for upgrading a weapon", hash=465),
    )
    async def calc_weapon(self, inter: Interaction):
        i: Inter = inter  # type: ignore
        lang = await self.bot.db.settings.get(i.user.id, Settings.LANG) or str(i.locale)
        ambr = AmbrAPI(i.client.session, to_ambr_top(lang))
        view = calc_weapon.View(lang, await ambr.get_weapon_types())
        view.author = i.user
        await i.response.send_message(view=view)
        view.message = await i.original_response()


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(CalcCog(bot))
