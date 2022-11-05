import ast
from typing import Dict, List, Optional, Tuple

import GGanalysis.games.genshin_impact as GI
from discord import File, Interaction, SelectOption, User, app_commands, Attachment
from discord.app_commands import locale_str as _
from discord.ext import commands
from UI_elements.wish.SetAuthKey import wish_import_command
from apps.genshin.checks import check_account, check_wish_history
from apps.genshin.custom_model import Wish, WishData, WishInfo
from apps.genshin.utils import get_uid, get_wish_history_embed, get_wish_info_embed
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.game.standard_characters import get_standard_characters
from UI_elements.wish import ChooseBanner, ChooseWeapon, WishFilter, SetAuthKey
from utility.paginator import GeneralPaginator
from utility.utils import default_embed, error_embed
from yelan.draw import draw_wish_overview_card
import sentry_sdk


class WishCog(commands.GroupCog, name="wish"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @check_account()
    @app_commands.command(
        name="import", description=_("Import your genshin wish history", hash=474)
    )
    async def wish_import(self, i: Interaction):
        await wish_import_command(i)

    @app_commands.command(
        name="file-import",
        description=_(
            "Import your Genshin wish history from a txt file exported by Shenhe",
            hash=692,
        ),
    )
    async def wish_file_import(self, i: Interaction, file: Attachment):
        locale = await get_user_locale(i.user.id, i.client.db) or i.locale
        try:
            wish_history = ast.literal_eval((await file.read()).decode("utf-8"))
            character_banner = 0
            weapon_banner = 0
            permanent_banner = 0
            novice_banner = 0

            for wish in wish_history:
                if wish[3] in [301, 400]:
                    character_banner += 1
                elif wish[3] == 302:
                    weapon_banner += 1
                elif wish[3] == 200:
                    permanent_banner += 1
                elif wish[3] == 100:
                    novice_banner += 1

            newest_wish = wish_history[0]
            oldest_wish = wish_history[-1]
            wish_info = WishInfo(
                total=len(wish_history),
                newest_wish=Wish(
                    time=newest_wish[2],
                    name=newest_wish[0],
                    rarity=newest_wish[1],
                ),
                oldest_wish=Wish(
                    time=oldest_wish[2],
                    name=oldest_wish[0],
                    rarity=oldest_wish[1],
                ),
                character_banner_num=character_banner,
                weapon_banner_num=weapon_banner,
                permanent_banner_num=permanent_banner,
                novice_banner_num=novice_banner,
            )
            embed = await get_wish_info_embed(i, locale, wish_info)
            view = SetAuthKey.View(locale, True, True)
            view.clear_items()
            view.add_item(
                SetAuthKey.ConfirmWishImport(locale, wish_history, from_text_file=True)
            )
            view.add_item(SetAuthKey.CancelWishImport(locale))
            view.author = i.user
            await i.response.send_message(embed=embed, view=view)
            view.message = await i.original_response()
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await i.response.send_message(
                embed=error_embed(message=text_map.get(693, locale)).set_author(
                    name=text_map.get(135, locale), icon_url=i.user.avatar_url
                ),
                ephemeral=True,
            )

    @check_wish_history()
    @app_commands.command(name="history", description=_("View wish history", hash=478))
    async def wish_history(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, i.client.db)
        embeds = await get_wish_history_embed(i, "")
        options = [
            SelectOption(label=text_map.get(645, i.locale, user_locale), value="301"),
            SelectOption(label=text_map.get(646, i.locale, user_locale), value="302"),
            SelectOption(label=text_map.get(647, i.locale, user_locale), value="100"),
            SelectOption(label=text_map.get(655, i.locale, user_locale), value="200"),
        ]
        select_banner = WishFilter.SelectBanner(
            text_map.get(662, i.locale, user_locale), options
        )
        await GeneralPaginator(
            i,
            embeds,
            self.bot.db,
            [
                select_banner,
                WishFilter.SelectRarity(
                    text_map.get(661, i.locale, user_locale), select_banner
                ),
            ],
        ).start()

    @check_wish_history()
    @app_commands.command(name="luck", description=_("Wish luck analysis", hash=372))
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("check other user's data", hash=416))
    async def wish_analysis(self, i: Interaction, member: User = None):
        await i.response.defer()
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)

        # chacter banner data
        async with i.client.db.execute(
            "SELECT wish_name, wish_rarity, wish_time FROM wish_history WHERE user_id = ? AND (wish_banner_type = 301 OR wish_banner_type = 400) AND uid = ? ORDER BY wish_id DESC",
            (i.user.id, await get_uid(member.id, i.client.db)),
        ) as cursor:
            data: List[Tuple[str, int, str]] = await cursor.fetchall()

        dist_c = None

        if data is not None:
            up_num = 0
            std = get_standard_characters()
            for _, tpl in enumerate(data):
                name = tpl[0]
                rarity = tpl[1]
                if rarity == 5:
                    if name not in std:
                        up_num += 1

            dist_c = GI.up_5star_character(item_num=up_num)

        if dist_c is None:
            return await i.response.send_message(
                embed=error_embed().set_author(
                    name=text_map.get(660, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        else:
            player_luck = str(round(100 * sum((dist_c)[: len(data)]), 2))

        embed = default_embed(
            message=f"• {text_map.get(373, i.locale, user_locale).format(luck=player_luck)}\n"
            f"• {text_map.get(379, i.locale, user_locale).format(a=len(data), b=up_num)}\n"
        )
        embed.set_author(
            name=text_map.get(372, i.locale, user_locale),
            icon_url=member.display_avatar.url,
        )
        await i.followup.send(embed=embed)

    @check_wish_history()
    @app_commands.command(
        name="predict-character",
        description=_(
            "Predict the chance of pulling a 5-star banner character", hash=480
        ),
    )
    @app_commands.rename(item_num=_("number", hash=481))
    @app_commands.describe(
        item_num=_("How many 5-star banner characters do you wish to pull?", hash=482)
    )
    async def wish_char(self, i: Interaction, item_num: int):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        if item_num > 10:
            return await i.response.send_message(
                embed=error_embed(message="number <= 10").set_author(
                    name=text_map.get(190, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        await i.response.defer()

        async with i.client.db.execute(
            "SELECT wish_name, wish_rarity, wish_time FROM wish_history WHERE user_id = ? AND (wish_banner_type = 301 OR wish_banner_type = 400) AND uid = ? ORDER BY wish_id DESC",
            (i.user.id, await get_uid(i.user.id, i.client.db)),
        ) as cursor:
            data: List[Tuple[str, int, str]] = await cursor.fetchall()

        pull_state = 0
        up_guarantee = 0

        if data:
            std = get_standard_characters()

            for pull, tpl in enumerate(data):
                name = tpl[0]
                rarity = tpl[1]
                if rarity == 5:
                    if name in std:
                        up_guarantee = 1
                    pull_state = pull
                    break

        dist_c = GI.up_5star_character(
            item_num=item_num, pull_state=pull_state, up_guarantee=up_guarantee
        )

        embed = default_embed(
            message=f"• {text_map.get(382, i.locale, user_locale)} **{item_num}** {text_map.get(383, i.locale, user_locale)}\n"
            f"• {text_map.get(380, i.locale, user_locale).format(a=pull_state)}\n"
            f"• {text_map.get(370 if up_guarantee==1 else 371, i.locale, user_locale)}\n"
            f"• {text_map.get(384, i.locale, user_locale).format(a=round(dist_c.exp))}\n"
        )
        embed.set_author(
            name=text_map.get(386, i.locale, user_locale),
            icon_url=i.user.display_avatar.url,
        )
        await i.followup.send(embed=embed)

    @check_wish_history()
    @app_commands.command(
        name="predict-weapon",
        description=_("Predict the chance of pulling a 5-star banner weapon", hash=483),
    )
    @app_commands.rename(
        item_num=_("number", hash=481), fate_point=_("fate-point", hash=657)
    )
    @app_commands.describe(
        item_num=_("How many 5-star banner weapons do you wish to pull?", hash=507),
        fate_point=_("A number that is either 0, 1, or 2", hash=658),
    )
    async def wish_weapon(self, i: Interaction, item_num: int, fate_point: int):
        await i.response.defer()
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        if fate_point not in [0, 1, 2]:
            return await i.followup.send(
                embed=error_embed(
                    message=text_map.get(659, user_locale or i.locale)
                ).set_author(
                    name=text_map.get(23, user_locale or i.locale),
                    icon_url=i.user.display_avatar.url,
                ),
            )

        if item_num > 1000:
            return await i.followup.send(
                embed=error_embed(message="number <= 1000").set_author(
                    name=text_map.get(190, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )

        async with i.client.db.execute(
            "SELECT wish_name, wish_rarity, wish_time FROM wish_history WHERE user_id = ? AND wish_banner_type = 302 AND uid = ? ORDER BY wish_id DESC",
            (i.user.id, await get_uid(i.user.id, i.client.db)),
        ) as cursor:
            data: List[Tuple[str, int, str]] = await cursor.fetchall()

        pull_state = 0

        if data:
            last_name = ""
            for pull, tpl in enumerate(data):
                name = tpl[0]
                rarity = tpl[1]
                if rarity == 5:
                    if last_name == "":
                        last_name = name
                        pull_state = pull

            view = ChooseWeapon.View(i.locale, user_locale)
            view.author = i.user
            embed = default_embed(
                message=f"{text_map.get(391, i.locale, user_locale)}:\n"
                f"**{last_name}**\n"
                f"{text_map.get(392, i.locale, user_locale)}\n"
            )
            await i.followup.send(embed=embed, view=view)
            view.message = await i.original_response()
            await view.wait()
            if view.up is None:
                return

            if view.up:  # 是UP
                up_guarantee = 0
            else:  # 是常駐
                up_guarantee = 1
        else:
            up_guarantee = 0

        dist_w = GI.up_5star_ep_weapon(
            item_num=item_num,
            fate_point=fate_point,
            pull_state=pull_state,
            up_guarantee=up_guarantee,
        )

        embed = default_embed(
            message=f"• {text_map.get(382, i.locale, user_locale)} **{item_num}** {text_map.get(395, i.locale, user_locale)}\n"
            f"• {text_map.get(657, i.locale, user_locale).replace('-', ' ')}: **{fate_point}**\n"
            f"• {text_map.get(380, i.locale, user_locale).format(a=pull_state)}\n"
            f"• {text_map.get(385, i.locale, user_locale).format(a=round(dist_w.exp))}\n"
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
            "SELECT wish_name, wish_banner_type, wish_rarity, wish_time FROM wish_history WHERE user_id = ? AND uid = ? ORDER BY wish_id DESC",
            (member.id, await get_uid(member.id, i.client.db)),
        ) as cursor:
            data = await cursor.fetchall()

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
        view = ChooseBanner.View(
            images, text_map.get(656, i.locale, user_locale), options
        )
        await i.followup.send(
            embed=default_embed().set_image(url="attachment://overview.jpeg"),
            file=File(fp, filename="overview.jpeg"),
            view=view,
        )
        view.message = await i.original_response()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WishCog(bot))
