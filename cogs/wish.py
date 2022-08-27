from datetime import datetime
from pprint import pprint
from typing import Optional

import aiosqlite
import discord
import GGanalysislib
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from apps.wish.wish_app import (
    check_user_wish_data,
    get_user_event_wish,
    get_user_weapon_wish,
    get_user_wish_overview,
)
from discord import Interaction, Member, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from UI_elements.wish import ChoosePlatform, ChooseWeapon, SetAuthKey
from utility.paginator import GeneralPaginator
from utility.utils import default_embed, divide_chunks, error_embed
from discord.app_commands import locale_str as _


class WishCog(commands.GroupCog, name="wish"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name="import", description=_("Import your genshin wish history", hash=474)
    )
    @app_commands.rename(function=_("option", hash=475))
    @app_commands.choices(
        function=[
            Choice(name=_("Tutorial", hash=476), value="help"),
            Choice(name=_("Submit authkey link", hash=477), value="submit"),
        ]
    )
    async def set_key(self, i: Interaction, function: str):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        if function == "help":
            view = ChoosePlatform.View(i.locale, user_locale)
            embed = default_embed(text_map.get(365, i.locale, user_locale))
            embed.set_footer(text=text_map.get(366, i.locale, user_locale))
            await i.response.send_message(embed=embed, view=view, ephemeral=True)
            view.message = await i.original_response()
        else:
            await i.response.send_modal(
                SetAuthKey.Modal(self.bot.db, i.locale, user_locale)
            )

    # /wish history
    @app_commands.command(name="history", description=_("View wish history", hash=478))
    async def wish_history(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        check, msg = await check_user_wish_data(i.user.id, i, self.bot.db)
        if not check:
            return await i.response.send_message(embed=msg, ephemeral=True)

        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute("SELECT * FROM wish_history WHERE user_id = ?", (i.user.id,))
        user_wish_history = await c.fetchall()
        user_wish_history.sort(key=lambda index: index[3], reverse=True)

        user_wish = []

        for index, tuple in enumerate(user_wish_history):
            wish_name = tuple[1]
            wish_rarity = tuple[2]
            wish_time = (datetime.strptime(tuple[3], "%Y/%m/%d %H:%M:%S")).strftime(
                "%Y/%m/%d"
            )
            wish_type = tuple[4]
            if (
                wish_rarity == 5 or wish_rarity == 4
            ):  # mark high rarity wishes with blue
                user_wish.append(
                    f"[{wish_time} {wish_name} ({wish_rarity} ✦ {wish_type})](https://github.com/seriaati/shenhe_bot)"
                )
            else:
                user_wish.append(
                    f"{wish_time} {wish_name} ({wish_rarity} ✦ {wish_type})"
                )

        user_wish = list(divide_chunks(user_wish, 20))
        embeds = []
        for small_segment in user_wish:
            embed_str = ""
            for wish_str in small_segment:
                embed_str += f"{wish_str}\n"
            embed = default_embed(message=embed_str)
            embed.set_author(
                name=text_map.get(369, i.locale, user_locale), icon_url=i.user.avatar
            )
            embeds.append(embed)

        await GeneralPaginator(i, embeds, self.bot.db).start()

    @app_commands.command(name="luck", description=_("Wish luck analysis", hash=479))
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("check other user's data", hash=416))
    async def wish_analysis(self, i: Interaction, member: Member = None):
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        check, msg = await check_user_wish_data(member.id, i, self.bot.db)
        if not check:
            return await i.response.send_message(embed=msg, ephemeral=True)

        (
            get_num,
            left_pull,
            use_pull,
            up_guarantee,
            up_five_star_num,
        ) = await get_user_event_wish(member.id, self.bot.db)
        player = GGanalysislib.Up5starCharacter()
        player_luck = str(
            round(
                100
                * player.luck_evaluate(
                    get_num=up_five_star_num, use_pull=use_pull, left_pull=left_pull
                ),
                2,
            )
        )
        guarantee = (
            text_map.get(370, i.locale, user_locale)
            if up_guarantee == 1
            else text_map.get(371, i.locale, user_locale)
        )

        embed = default_embed(
            message=f"• {text_map.get(373, i.locale, user_locale)} **{player_luck}%** {text_map.get(374, i.locale, user_locale)}\n"
            f"• {text_map.get(375, i.locale, user_locale)} **{use_pull}** {text_map.get(376, i.locale, user_locale)}\n"
            f"• {text_map.get(378, i.locale, user_locale)} **{up_five_star_num}** {text_map.get(379, i.locale, user_locale)}\n"
            f"• {text_map.get(380, i.locale, user_locale)} **{left_pull}** {text_map.get(381, i.locale, user_locale)}\n"
            f"• {guarantee}"
        )
        embed.set_author(
            name=text_map.get(372, i.locale, user_locale), icon_url=member.avatar
        )
        await i.response.send_message(embed=embed)

    @app_commands.command(
        name="character",
        description=_("Predict the chance of pulling a character", hash=480),
    )
    @app_commands.rename(num=_("number", hash=481))
    @app_commands.describe(
        num=_("How many five star UP characters do you wish to pull?", hash=482)
    )
    async def wish_char(self, i: Interaction, num: int):
        check, embed = await check_user_wish_data(i.user.id, i, self.bot.db)
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        if not check:
            return await i.response.send_message(embed=embed, ephemeral=True)

        (
            get_num,
            left_pull,
            use_pull,
            up_guarantee,
            up_five_star_num,
        ) = await get_user_event_wish(i.user.id, self.bot.db)
        guarantee = (
            text_map.get(370, i.locale, user_locale)
            if up_guarantee == 1
            else text_map.get(371, i.locale, user_locale)
        )
        player = GGanalysislib.Up5starCharacter()
        calc_pull = 1
        p = 0
        while p < 80:
            p = 100 * player.get_p(
                item_num=num,
                calc_pull=calc_pull,
                pull_state=left_pull,
                up_guarantee=up_guarantee,
            )
            calc_pull += 1

        embed = default_embed(
            message=f"• {text_map.get(382, i.locale, user_locale)} **{num}** {text_map.get(383, i.locale, user_locale)}\n"
            f"• {text_map.get(380, i.locale, user_locale)} **{left_pull}** {text_map.get(381, i.locale, user_locale)}\n"
            f"• {guarantee}\n"
            f"• {text_map.get(384, i.locale, user_locale)} **{calc_pull}** {text_map.get(385, i.locale, user_locale)}\n"
        )
        embed.set_author(
            name=text_map.get(386, i.locale, user_locale), icon_url=i.user.avatar
        )
        await i.response.send_message(embed=embed)

    @app_commands.command(
        name="weapon",
        description=_("Predict the chance of pulling a weapon you want", hash=483),
    )
    @app_commands.rename(item_num=_("number", hash=506))
    @app_commands.describe(
        item_num=_("How many five star UP weapons do you wish to pull?", hash=507)
    )
    async def wish_weapon(self, i: Interaction, item_num: int):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        check, msg = await check_user_wish_data(i.user.id, i, self.bot.db)
        if not check:
            return await i.response.send_message(embed=msg, ephemeral=True)

        last_name, pull_state = await get_user_weapon_wish(i.user.id, self.bot.db)
        if last_name == "":
            return await i.response.send_message(
                embed=error_embed().set_author(
                    name=text_map.get(405, i.locale, user_locale),
                    icon_url=i.user.avatar,
                ),
                ephemeral=True,
            )

        view = ChooseWeapon.View(self.bot.db, i.user, i.locale, user_locale)
        embed = default_embed(
            message=f"{text_map.get(391, i.locale, user_locale)}:\n"
            f"**{last_name}**\n"
            f"{text_map.get(392, i.locale, user_locale)}\n"
        )
        await i.response.send_message(embed=embed, view=view)
        view.message = await i.original_response()
        await view.wait()
        if view.up is None:
            return

        if view.up:  # 是UP
            if view.want:  # 是想要的UP
                up_guarantee = 0
            else:  # 是不想要的UP
                up_guarantee = 1
        else:  # 是常駐
            up_guarantee = 2

        player = GGanalysislib.Up5starWeaponEP()
        calc_pull = 1
        p = 0
        while p < 80:
            p = 100 * player.get_p(
                item_num=item_num,
                calc_pull=calc_pull,
                pull_state=pull_state,
                up_guarantee=up_guarantee,
            )
            calc_pull += 1

        embed = default_embed(
            message=f"• {text_map.get(394, i.locale, user_locale)} **{item_num}** {text_map.get(395, i.locale, user_locale)}\n"
            f"• {text_map.get(380, i.locale, user_locale)} **{pull_state}** {text_map.get(381, i.locale, user_locale)}\n"
            f"• {text_map.get(384, i.locale, user_locale)} **{calc_pull}** {text_map.get(385, i.locale, user_locale)}"
        )
        embed.set_author(
            name=text_map.get(393, i.locale, user_locale), icon_url=i.user.avatar
        )
        await i.edit_original_response(embed=embed, view=None)

    @app_commands.command(
        name="overview", description=_("View you genshin wish overview", hash=484)
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("check other user's data", hash=416))
    async def wish_overview(self, i: Interaction, member: Optional[Member] = None):
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        check, embed = await check_user_wish_data(member.id, i, self.bot.db)
        if not check:
            return await i.response.send_message(embed=embed, ephemeral=True)

        overview = await get_user_wish_overview(member.id, self.bot.db)

        # banner_ids = [200, 301+400, 302]
        banner_names = [
            text_map.get(398, i.locale, user_locale),
            text_map.get(399, i.locale, user_locale),
            text_map.get(400, i.locale, user_locale),
        ]
        total = 0
        for banner in overview.values():
            total += banner["total"]
        embed = default_embed(
            message=f"{text_map.get(375, i.locale, user_locale)} {total} {text_map.get(376,i.locale, user_locale)}\n"
            f"{text_map.get(396, i.locale, user_locale)} {160*total} <:PRIMO:1010048703312171099> {text_map.get(397, i.locale, user_locale)}"
        )

        for index, banner in enumerate(overview.values()):
            average = (
                (banner["total"] // banner["five_star"])
                if banner["five_star"] != 0
                else 0
            )
            std_str = (
                f'• {text_map.get(387, i.locale, user_locale)}: **{banner["std"]}**\n'
                if index == 1
                else ""
            )
            embed.add_field(
                name=f"{banner_names[index]}",
                value=f'• {text_map.get(375, i.locale, user_locale)} **{banner["total"]}** {text_map.get(376, i.locale, user_locale)}\n({banner["total"]*160} <:PRIMO:1010048703312171099> {text_map.get(397, i.locale, user_locale)})\n'
                f'• 5<:white_star:982456919224615002> **{banner["five_star"]}**\n'
                f'• 4<:white_star:982456919224615002> **{banner["four_star"]}**\n'
                f"• {text_map.get(401, i.locale, user_locale)} **{average}** {text_map.get(402, i.locale, user_locale)}\n"
                f'• {text_map.get(403, i.locale, user_locale)} **{(80 if index == 2 else 90)-banner["left_pull"]}** {text_map.get(404, i.locale, user_locale)}\n'
                f"{std_str}",
            )
        embed.set_author(name=member, icon_url=member.avatar)
        await i.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WishCog(bot))
