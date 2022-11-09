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
        await i.response.defer()
        view = CalcCharacter.View()
        await i.followup.send(view=view)

    @app_commands.command(
        name="weapon",
        description=_("Calcualte materials needed for upgrading a weapon", hash=465),
    )
    @app_commands.rename(types=_("type", hash=429), rarities=_("rarity", hash=467))
    @app_commands.choices(
        types=[
            Choice(name=_("sword", hash=468), value=1),
            Choice(name=_("catalyst", hash=469), value=10),
            Choice(name=_("claymore", hash=470), value=11),
            Choice(name=_("bow", hash=471), value=12),
            Choice(name=_("polearm", hash=472), value=13),
        ],
        rarities=[
            Choice(name="★★★★★", value=5),
            Choice(name="★★★★", value=4),
            Choice(name="★★★", value=3),
            Choice(name="★★", value=2),
            Choice(name="★", value=1),
        ],
    )
    async def calc_weapon(self, i: Interaction, types: int, rarities: int):
        user_locale = await get_user_locale(i.user.id, self.bot.db)

        client = self.bot.genshin_client
        client.lang = to_genshin_py(user_locale or i.locale)

        weapons = await client.get_calculator_weapons(
            types=[types], rarities=[rarities]
        )
        view = CalcWeapon.View(weapons, i.user, self.bot.db, i.locale, user_locale)
        await i.response.send_message(view=view)
        view.message = await i.original_response()
        await view.wait()
        if view.weapon_id == "":
            return

        value: str
        for value in list(view.levels.values()):
            if not value.isdigit():
                await i.delete_original_response()
                return await i.followup.send(
                    embed=error_embed(
                        message=text_map.get(187, i.locale, user_locale)
                    ).set_author(
                        name=text_map.get(190, i.locale, user_locale),
                        icon_url=i.user.display_avatar.url,
                    ),
                    ephemeral=True,
                )
        try:
            cost = await (
                client.calculator().set_weapon(
                    int(view.weapon_id),
                    current=int(view.levels["current"]),
                    target=int(view.levels["target"]),
                )
            )
        except GenshinException as e:
            if e.retcode == -500001:
                await i.delete_original_response()
                return await i.followup.send(
                    embed=error_embed().set_author(
                        name=text_map.get(190, i.locale, user_locale),
                        icon_url=i.user.display_avatar.url,
                    ),
                    ephemeral=True,
                )

        embeds = []
        embed = default_embed()
        embed.set_author(
            name=text_map.get(191, i.locale, user_locale),
            icon_url=i.user.display_avatar.url,
        )
        embed.set_thumbnail(url=get_weapon(view.weapon_id)["icon"])
        embed.add_field(
            name=text_map.get(192, i.locale, user_locale),
            value=f'{text_map.get(200, i.locale, user_locale)} {view.levels["current"]} ▸ {view.levels["target"]}\n',
            inline=False,
        )

        materials = {}
        items = []

        for consumable in cost.weapon:
            if consumable.id in materials:
                materials[consumable.id] += consumable.amount
            else:
                materials[consumable.id] = consumable.amount

        for material_id, material_amount in materials.items():
            items.append((material_id, material_amount))

        result = await draw_todo_card(items, user_locale or i.locale, self.bot.session)

        if len(result) == 0:
            embeds.append(embed)

        for index in range(len(result)):
            if index == 0:
                pass
            else:
                embed = default_embed()
            embed.set_image(url=f"attachment://{index}.jpeg")
            embeds.append(embed)

        disabled = True if len(materials) == 0 else False
        button = AddToTodo.AddToTodo(
            disabled, self.bot.db, materials, text_map.get(175, i.locale, user_locale)
        )
        await GeneralPaginator(
            i, embeds, self.bot.db, custom_children=[button], files=result
        ).start(edit=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CalcCog(bot))
