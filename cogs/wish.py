from datetime import datetime
from typing import Dict, List, Optional

import aiosqlite
import GGanalysislib
from apps.genshin.checks import check_wish_history
from apps.genshin.custom_model import WishData
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from apps.wish.wish_app import (
    get_user_event_wish,
    get_user_weapon_wish,
)
from discord import File, Interaction, User, app_commands, SelectOption
from discord.app_commands import locale_str as _
from discord.ext import commands
from UI_elements.wish import ChoosePlatform, ChooseWeapon, ChooseBanner
from utility.paginator import GeneralPaginator
from utility.utils import default_embed, divide_chunks, error_embed
from yelan.draw import draw_wish_overview_card


class WishCog(commands.GroupCog, name="wish"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name="import", description=_("Import your genshin wish history", hash=474)
    )
    async def set_key(self, i: Interaction):
        await ChoosePlatform.GOBack.callback(self, i)

    @check_wish_history()
    @app_commands.command(name="history", description=_("View wish history", hash=478))
    async def wish_history(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)

        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute("SELECT * FROM wish_history WHERE user_id = ?", (i.user.id,))
        user_wish_history = await c.fetchall()
        user_wish_history.sort(key=lambda index: index[3], reverse=True)

        user_wish = []

        for index, tpl in enumerate(user_wish_history):
            wish_name = tpl[1]
            wish_rarity = tpl[2]
            wish_time = (datetime.strptime(tpl[3], "%Y/%m/%d %H:%M:%S")).strftime(
                "%Y/%m/%d"
            )
            wish_type = tpl[4]
            if (
                wish_rarity == 5 or wish_rarity == 4
            ):  # mark high rarity wishes with blue
                user_wish.append(
                    f"[{wish_time} {wish_name} ({wish_rarity} ✦ {wish_type})](https://seriaati.github.io/shenhe_website/)"
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
                name=text_map.get(369, i.locale, user_locale),
                icon_url=i.user.display_avatar.url,
            )
            embeds.append(embed)

        await GeneralPaginator(i, embeds, self.bot.db).start()

    @check_wish_history()
    @app_commands.command(name="luck", description=_("Wish luck analysis", hash=372))
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("check other user's data", hash=416))
    async def wish_analysis(self, i: Interaction, member: User = None):
        await i.response.defer()
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)

        (
            _,
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
            f"• {text_map.get(375, i.locale, user_locale)} **{up_five_star_num}** {text_map.get(379, i.locale, user_locale)}\n"
            f"• {text_map.get(380, i.locale, user_locale)} **{left_pull}** {text_map.get(381, i.locale, user_locale)}\n"
            f"• {guarantee}"
        )
        embed.set_author(
            name=text_map.get(372, i.locale, user_locale),
            icon_url=member.display_avatar.url,
        )
        await i.followup.send(embed=embed)

    @check_wish_history()
    @app_commands.command(
        name="character",
        description=_("Predict the chance of pulling a character", hash=480),
    )
    @app_commands.rename(num=_("number", hash=481))
    @app_commands.describe(
        num=_("How many five star UP characters do you wish to pull?", hash=482)
    )
    async def wish_char(self, i: Interaction, num: int):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        if num > 10:
            return await i.response.send_message(
                embed=error_embed(message="number <= 10").set_author(
                    name=text_map.get(190, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        await i.response.defer()

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
            name=text_map.get(386, i.locale, user_locale),
            icon_url=i.user.display_avatar.url,
        )
        await i.followup.send(embed=embed)

    @check_wish_history()
    @app_commands.command(
        name="weapon",
        description=_("Predict the chance of pulling a weapon you want", hash=483),
    )
    @app_commands.rename(item_num=_("number", hash=481))
    @app_commands.describe(
        item_num=_("How many five star UP weapons do you wish to pull?", hash=507)
    )
    async def wish_weapon(self, i: Interaction, item_num: int):
        user_locale = await get_user_locale(i.user.id, self.bot.db)

        last_name, pull_state = await get_user_weapon_wish(i.user.id, self.bot.db)
        if last_name == "":
            return await i.response.send_message(
                embed=error_embed().set_author(
                    name=text_map.get(405, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
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
            message=f"• {text_map.get(382, i.locale, user_locale)} **{item_num}** {text_map.get(395, i.locale, user_locale)}\n"
            f"• {text_map.get(380, i.locale, user_locale)} **{pull_state}** {text_map.get(381, i.locale, user_locale)}\n"
            f"• {text_map.get(384, i.locale, user_locale)} **{calc_pull}** {text_map.get(385, i.locale, user_locale)}"
        )
        embed.set_author(
            name=text_map.get(393, i.locale, user_locale),
            icon_url=i.user.display_avatar.url,
        )
        await i.edit_original_response(embed=embed, view=None)

    @check_wish_history()
    @app_commands.command(
        name="overview", description=_("View you genshin wish overview", hash=484)
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("check other user's data", hash=416))
    async def wish_overview(self, i: Interaction, member: Optional[User] = None):
        await i.response.defer()
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)

        async with i.client.db.execute(
            "SELECT wish_name, wish_banner_type, wish_rarity, wish_time FROM wish_history WHERE user_id = ?",
            (member.id,),
        ) as cursor:
            data = await cursor.fetchall()

        data.sort(
            key=lambda x: datetime.strptime(x[3], "%Y/%m/%d %H:%M:%S"), reverse=True
        )

        items: List[Dict[str, int | str]] = []
        images = {}
        options = []
        for _, tpl in enumerate(data):
            name = tpl[0]
            banner = tpl[1]
            wish_rarity = tpl[2]
            if banner == 400:
                banner = 301
            items.append({"name": name, "banner": banner, "rarity": wish_rarity})

        novice_banner = [i for i in items if i["banner"] == 100]
        character_banner = [i for i in items if i["banner"] == 301]
        weapon_banner = [i for i in items if i["banner"] == 302]
        permanent_banner = [i for i in items if i["banner"] == 200]
        banners = {
            100: novice_banner,
            301: character_banner,
            302: weapon_banner,
            200: permanent_banner,
        }
        for banner_id, banner in banners.items():
            if not banner:
                continue
            five_star = [i for i in banner if i["rarity"] == 5]
            four_star = [i for i in banner if i["rarity"] == 4]
            pity = 0
            for item in items:
                pity += 1
                if item["rarity"] == 5:
                    break
            reversed_banner = banner
            reversed_banner.reverse()
            pull = 0
            recents = []
            for item in reversed_banner:
                pull += 1
                if item["rarity"] == 5:
                    recents.append({"name": item["name"], "pull": pull})
                    pull = 0
            recents.reverse()
            title = ""
            if banner_id == 100:
                title = text_map.get(647, i.locale, user_locale)
            elif banner_id == 301:
                title = text_map.get(645, i.locale, user_locale)
            elif banner_id == 302:
                title = text_map.get(646, i.locale, user_locale)
            elif banner_id == 200:
                title = text_map.get(655, i.locale, user_locale)
            wish_data = WishData(
                title=title,
                total_wishes=len(banner),
                four_star=len(four_star),
                five_star=len(five_star),
                pity=pity,
                recents=recents,
            )
            fp = await draw_wish_overview_card(
                i.client.session,
                user_locale or i.locale,
                wish_data,
                "weapon" if banner == 302 else "character",
                member.display_avatar.url,
                member.name,
            )
            images[banner_id] = fp
            options.append(
                SelectOption(
                    label=title,
                    value=str(banner_id),
                )
            )
        fp = list(images.values())[0]
        fp.seek(0)
        await i.followup.send(
            embed=default_embed().set_image(url="attachment://overview.jpeg"),
            file=File(fp, filename="overview.jpeg"),
            view=ChooseBanner.View(
                images, text_map.get(656, i.locale, user_locale), options
            ),
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WishCog(bot))
