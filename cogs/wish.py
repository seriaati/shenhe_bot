import ast
from typing import Dict, List, Optional

import GGanalysis.games.genshin_impact as GI
import sentry_sdk
from discord import (Attachment, File, Interaction, Member, SelectOption, User,
                     app_commands)
from discord.app_commands import locale_str as _
from discord.ext import commands

from ambr.client import AmbrTopAPI
from ambr.models import Character, Weapon
from apps.draw import main_funcs
from apps.genshin.checks import check_account, check_wish_history
from apps.genshin.custom_model import (DrawInput, RecentWish, ShenheBot, Wish,
                                       WishData, WishInfo, WishItem)
from apps.genshin.utils import (get_uid, get_wish_history_embed,
                                get_wish_info_embed)
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.game.standard_characters import get_standard_characters
from UI_elements.wish import ChooseBanner, ChooseWeapon, SetAuthKey, WishFilter
from UI_elements.wish.SetAuthKey import wish_import_command
from utility.utils import DefaultEmbed, ErrorEmbed, get_user_appearance_mode
from utility.wish_paginator import WishPaginator


class WishCog(commands.GroupCog, name="wish"):
    def __init__(self, bot):
        self.bot: ShenheBot = bot
        super().__init__()

    @check_account()
    @app_commands.command(
        name="import", description=_("Import your genshin wish history", hash=474)
    )
    async def wish_import(self, i: Interaction):
        await wish_import_command(i)

    @check_account()
    @app_commands.command(
        name="file-import",
        description=_(
            "Import your Genshin wish history from a txt file exported by Shenhe",
            hash=692,
        ),
    )
    async def wish_file_import(self, i: Interaction, file: Attachment):
        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
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
            embed = await get_wish_info_embed(i, str(locale), wish_info)
            view = SetAuthKey.View(locale, True, True)
            view.clear_items()
            view.add_item(
                SetAuthKey.ConfirmWishImport(locale, wish_history, from_text_file=True)
            )
            view.add_item(SetAuthKey.CancelWishImport(locale))
            view.author = i.user
            await i.response.send_message(embed=embed, view=view)
            view.message = await i.original_response()
        except UnicodeEncodeError:
            await i.response.send_message(
                embed=ErrorEmbed(description=text_map.get(567, locale)).set_author(
                    name=text_map.get(195, locale), icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await i.response.send_message(
                embed=ErrorEmbed(description=text_map.get(693, locale)).set_author(
                    name=text_map.get(135, locale), icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )

    @check_wish_history()
    @app_commands.command(name="history", description=_("View wish history", hash=478))
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("Check other user's data", hash=416))
    async def wish_history(self, i: Interaction, member: Optional[User] = None):
        user_locale = await get_user_locale(i.user.id, i.client.pool)
        embeds = await get_wish_history_embed(i, "", member)
        options = [
            SelectOption(
                label=text_map.get(645, i.locale, user_locale) + " 1", value="301"
            ),
            SelectOption(
                label=text_map.get(645, i.locale, user_locale) + " 2", value="400"
            ),
            SelectOption(label=text_map.get(646, i.locale, user_locale), value="302"),
            SelectOption(label=text_map.get(647, i.locale, user_locale), value="100"),
            SelectOption(label=text_map.get(655, i.locale, user_locale), value="200"),
        ]
        select_banner = WishFilter.SelectBanner(
            text_map.get(662, i.locale, user_locale), options
        )
        await WishPaginator(
            i,
            embeds,
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
    @app_commands.describe(member=_("Check other user's data", hash=416))
    async def wish_analysis(
        self, i: Interaction, member: Optional[User | Member] = None
    ):
        await i.response.defer()
        member = member or i.user
        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale

        # charcter banner data
        async with self.bot.pool.acquire() as db:
            async with db.execute(
                "SELECT wish_name, wish_rarity, wish_time FROM wish_history WHERE user_id = ? AND (wish_banner_type = 301 OR wish_banner_type = 400) AND uid = ? ORDER BY wish_id DESC",
                (i.user.id, await get_uid(member.id, self.bot.pool)),
            ) as c:
                up_num = 0
                std = get_standard_characters()
                data_length = 0
                for row in c.get_cursor():
                    name = row[0]
                    rarity = row[1]
                    if rarity == 5:
                        if name not in std:
                            up_num += 1
                    data_length += 1
                dist_c = GI.up_5star_character(item_num=up_num)
                player_luck = round(100 * sum((dist_c)[: data_length + 1]), 2)

        embed = DefaultEmbed(
            description=f"""
                • {text_map.get(373, locale).format(luck=round(100-player_luck, 2))}
                • {text_map.get(379, locale).format(a=data_length, b=up_num)}
            """
        )
        embed.set_author(
            name=text_map.get(372, locale),
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
        user_locale = await get_user_locale(i.user.id, i.client.pool)
        if item_num > 10:
            return await i.response.send_message(
                embed=ErrorEmbed(description="number <= 10").set_author(
                    name=text_map.get(190, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        await i.response.defer()

        async with self.bot.pool.acquire() as db:
            async with db.execute(
                "SELECT wish_name, wish_rarity, wish_time FROM wish_history WHERE user_id = ? AND (wish_banner_type = 301 OR wish_banner_type = 400) AND uid = ? ORDER BY wish_id DESC",
                (i.user.id, await get_uid(i.user.id, self.bot.pool)),
            ) as c:
                pull_state = 0
                up_guarantee = 0

                std = get_standard_characters()

                for row in c.get_cursor():
                    name = row[0]
                    rarity = row[1]
                    if rarity == 5:
                        if name in std:
                            up_guarantee = 1
                        break
                    pull_state += 1

        dist_c = GI.up_5star_character(
            item_num=item_num, pull_state=pull_state, up_guarantee=up_guarantee
        )

        embed = DefaultEmbed(
            description=f"• {text_map.get(382, i.locale, user_locale)} **{item_num}** {text_map.get(383, i.locale, user_locale)}\n"
            f"• {text_map.get(380, i.locale, user_locale).format(a=pull_state)}\n"
            f"• {text_map.get(370 if up_guarantee==1 else 371, i.locale, user_locale)}\n"
            f"• {text_map.get(384, i.locale, user_locale).format(a=round(dist_c.exp))}\n" # type: ignore
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
        user_locale = await get_user_locale(i.user.id, i.client.pool)
        if fate_point not in [0, 1, 2]:
            return await i.followup.send(
                embed=ErrorEmbed(
                    description=text_map.get(659, user_locale or i.locale)
                ).set_author(
                    name=text_map.get(23, user_locale or i.locale),
                    icon_url=i.user.display_avatar.url,
                ),
            )

        if item_num > 1000:
            return await i.followup.send(
                embed=ErrorEmbed(description="number <= 1000").set_author(
                    name=text_map.get(190, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )

        async with self.bot.pool.acquire() as db:
            async with db.execute(
                "SELECT wish_name, wish_rarity, wish_time FROM wish_history WHERE user_id = ? AND wish_banner_type = 302 AND uid = ? ORDER BY wish_id DESC",
                (i.user.id, await get_uid(i.user.id, self.bot.pool)),
            ) as c:
                pull_state = 0
                last_name = ""

                for row in c.get_cursor():
                    name = row[0]
                    rarity = row[1]
                    if rarity == 5:
                        if last_name == "":
                            last_name = name
                    pull_state += 1

            view = ChooseWeapon.View(i.locale, user_locale)
            view.author = i.user
            embed = DefaultEmbed(
                description=f"{text_map.get(391, i.locale, user_locale)}:\n"
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

        dist_w = GI.up_5star_ep_weapon(
            item_num=item_num,
            fate_point=fate_point,
            pull_state=pull_state,
            up_guarantee=up_guarantee,
        )

        embed = DefaultEmbed(
            description=f"• {text_map.get(382, i.locale, user_locale)} **{item_num}** {text_map.get(395, i.locale, user_locale)}\n"
            f"• {text_map.get(657, i.locale, user_locale).replace('-', ' ')}: **{fate_point}**\n"
            f"• {text_map.get(380, i.locale, user_locale).format(a=pull_state)}\n"
            f"• {text_map.get(385, i.locale, user_locale).format(a=round(dist_w.exp))}\n" # type: ignore
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
    @app_commands.describe(member=_("Check other user's data", hash=416))
    async def wish_overview(
        self, i: Interaction, member: Optional[User | Member] = None
    ):
        await i.response.defer()
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, i.client.pool)
        ambr = AmbrTopAPI(self.bot.session, to_ambr_top(user_locale or i.locale))

        wishes: List[WishItem] = []
        async with self.bot.pool.acquire() as db:
            async with db.execute(
                "SELECT wish_name, wish_banner_type, wish_rarity, wish_time FROM wish_history WHERE user_id = ? AND uid = ? ORDER BY wish_id DESC",
                (member.id, await get_uid(member.id, self.bot.pool)),
            ) as c:
                for row in c.get_cursor():
                    name = row[0]
                    banner = row[1]
                    rarity = row[2]
                    time = row[3]
                    wishes.append(
                        WishItem(name=name, banner=banner, rarity=rarity, time=time)
                    )

        novice_banner = [wish_item for wish_item in wishes if wish_item.banner == 100]
        character_banner = [
            wish_item for wish_item in wishes if wish_item.banner == 301
        ]
        character_banner_alt = [
            wish_item for wish_item in wishes if wish_item.banner == 400
        ]
        weapon_banner = [wish_item for wish_item in wishes if wish_item.banner == 302]
        permanent_banner = [
            wish_item for wish_item in wishes if wish_item.banner == 200
        ]
        banners = {
            100: novice_banner,
            301: character_banner,
            400: character_banner_alt,
            302: weapon_banner,
            200: permanent_banner,
        }

        all_wish_data: Dict[str, WishData] = {}
        options = []

        for banner_id, banner_wishes in banners.items():
            if not banner_wishes:
                continue
            five_star = [wish for wish in banner_wishes if wish.rarity == 5]
            four_star = [wish for wish in banner_wishes if wish.rarity == 4]
            pity = 0
            for wish in banner_wishes:
                pity += 1
                if wish.rarity == 5:
                    break
            reversed_banner = banner_wishes
            reversed_banner.reverse()
            pull = 0

            recents: List[RecentWish] = []
            for wish in reversed_banner:
                pull += 1
                if wish.rarity == 5:
                    item_id = text_map.get_id_from_name(wish.name)
                    item = None
                    if item_id is not None:
                        item = await ambr.get_character(str(item_id))
                        if not isinstance(item, Character):
                            item = await ambr.get_weapon(item_id)
                    if isinstance(item, Character | Weapon):
                        recents.append(
                            RecentWish(name=item.name, pull_num=pull, icon=item.icon)
                        )
                    else:
                        recents.append(RecentWish(name=wish.name, pull_num=pull))
                    pull = 0
            recents.reverse()

            title = ""
            if banner_id == 100:
                title = text_map.get(647, i.locale, user_locale)
            elif banner_id == 301:
                title = text_map.get(645, i.locale, user_locale) + " 1"
            elif banner_id == 400:
                title = text_map.get(645, i.locale, user_locale) + " 2"
            elif banner_id == 302:
                title = text_map.get(646, i.locale, user_locale)
            elif banner_id == 200:
                title = text_map.get(655, i.locale, user_locale)

            wish_data = WishData(
                title=title,
                total_wishes=len(banner_wishes),
                four_star=len(four_star),
                five_star=len(five_star),
                pity=pity,
                recents=recents,
            )
            options.append(
                SelectOption(
                    label=title,
                    value=str(banner_id),
                )
            )
            all_wish_data[str(banner_id)] = wish_data

        if not all_wish_data:
            return await i.followup.send(
                embed=ErrorEmbed().set_author(
                    name=text_map.get(731, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                )
            )

        if "400" in all_wish_data:
            temp = all_wish_data["301"].pity
            all_wish_data["301"].pity += all_wish_data["400"].pity
            all_wish_data["400"].pity += temp

        fp = await main_funcs.draw_wish_overview_card(
            DrawInput(
                loop=self.bot.loop,
                session=self.bot.session,
                locale=user_locale or i.locale,
                dark_mode=await get_user_appearance_mode(i.user.id, i.client.pool),
            ),
            list(all_wish_data.values())[0],
            member.display_avatar.url,
            member.display_name,
        )
        fp.seek(0)
        view = ChooseBanner.View(
            member, text_map.get(656, i.locale, user_locale), options, all_wish_data
        )
        await i.followup.send(
            embed=DefaultEmbed().set_image(url="attachment://overview.jpeg"),
            file=File(fp, filename="overview.jpeg"),
            view=view,
        )
        view.message = await i.original_response()


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(WishCog(bot))
