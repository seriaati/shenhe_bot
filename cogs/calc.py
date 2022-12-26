from discord import Interaction, app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands
from ambr.client import AmbrTopAPI
from apps.genshin.custom_model import ShenheBot
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.utils import get_user_locale
from UI_elements.calc import CalcCharacter, CalcWeapon


class CalcCog(commands.GroupCog, name="calc"):
    def __init__(self, bot):
        super().__init__()
        self.bot: ShenheBot = bot

    @app_commands.command(
        name="character",
        description=_("Calculate materials needed for upgrading a character", hash=460),
    )
    async def calc_characters(self, i: Interaction):
        view = CalcCharacter.View()
        view.author = i.user
        await i.response.send_message(view=view)
        view.message = await i.original_response()

    @app_commands.command(
        name="weapon",
        description=_("Calcualte materials needed for upgrading a weapon", hash=465),
    )
    async def calc_weapon(self, i: Interaction):
        locale = await get_user_locale(i.user.id, self.bot.db) or i.locale
        ambr = AmbrTopAPI(i.client.session, to_ambr_top(locale))
        view = CalcWeapon.View(locale, await ambr.get_weapon_types())
        view.author = i.user
        await i.response.send_message(view=view)
        view.message = await i.original_response()


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(CalcCog(bot))
