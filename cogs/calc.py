from typing import List
from discord import Interaction, app_commands
from discord.app_commands import Choice
from discord.app_commands import locale_str as _
from discord.ext import commands
from genshin import InvalidCookies
from genshin.errors import GenshinException
from ambr.client import AmbrTopAPI
from ambr.models import Character
from data.game.elements import get_element_list
from apps.genshin.checks import check_cookie_predicate
from apps.genshin.custom_model import ShenheBot
from apps.genshin.genshin_app import GenshinApp
from apps.genshin.utils import get_weapon
from apps.text_map.convert_locale import to_ambr_top, to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_elements.calc import AddToTodo, CalcCharacter, CalcWeapon
from utility.paginator import GeneralPaginator
from utility.utils import default_embed, error_embed
from yelan.draw import draw_todo_card


class CalcCog(commands.GroupCog, name="calc"):
    def __init__(self, bot):
        super().__init__()
        self.bot: ShenheBot = bot
        self.genshin_app = GenshinApp(self.bot.db, self.bot)

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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CalcCog(bot))
