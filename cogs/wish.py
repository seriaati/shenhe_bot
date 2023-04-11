from typing import Dict, List, Optional

import discord
import yaml
from discord import app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands

import ambr
import dev.models as models
from apps.db import get_user_lang, get_user_theme
from apps.draw import main_funcs
from apps.genshin import check_account, check_wish_history, get_uid
from apps.text_map import text_map, to_ambr_top
from apps.wish.models import (RecentWish, WishData, WishHistory, WishInfo,
                              WishItem)
from apps.wish.utils import get_wish_history_embeds, get_wish_info_embed
from dev.base_ui import capture_exception
from ui.wish import ChooseBanner, SetAuthKey, WishFilter
from ui.wish.SetAuthKey import wish_import_command
from utility.wish_history_paginator import WishHistoryPaginator
from utility.wish_overview_paginator import WishOverviewPaginator


class WishCog(commands.GroupCog, name="wish"):
    def __init__(self, bot) -> None:
        self.bot: models.BotModel = bot
        super().__init__()

    @check_account()
    @app_commands.command(
        name="import", description=_("import your genshin wish history", hash=474)
    )
    async def wish_import(self, inter: discord.Interaction) -> None:
        i: models.Inter = inter  # type: ignore
        await wish_import_command(i)

    @check_account()
    @app_commands.command(
        name="file-import",
        description=_(
            "import your Genshin wish history from a txt file exported by Shenhe",
            hash=692,
        ),
    )
    async def wish_file_import(
        self, inter: discord.Interaction, file: discord.Attachment
    ) -> None:
        i: models.Inter = inter  # type: ignore
        locale = await get_user_lang(i.user.id, self.bot.pool) or i.locale
        try:
            rows = yaml.safe_load((await file.read()).decode("utf-8"))
            wish_history = [WishHistory.from_row(row) for row in rows]  # type: ignore
            character_banner = 0
            weapon_banner = 0
            permanent_banner = 0
            novice_banner = 0

            for wish in wish_history:
                if wish.banner in (301, 400):
                    character_banner += 1
                elif wish.banner == 302:
                    weapon_banner += 1
                elif wish.banner == 200:
                    permanent_banner += 1
                elif wish.banner == 100:
                    novice_banner += 1

            wish_info = WishInfo(
                total=len(wish_history),
                newest_wish=wish_history[0],
                oldest_wish=wish_history[-1],
                character_banner_num=character_banner,
                weapon_banner_num=weapon_banner,
                permanent_banner_num=permanent_banner,
                novice_banner_num=novice_banner,
            )
            embed = await get_wish_info_embed(i, str(locale), wish_info)
            view = SetAuthKey.View(locale, True, True)
            view.clear_items()
            view.add_item(
                SetAuthKey.ConfirmWishimport(locale, wish_history, from_text_file=True)
            )
            view.add_item(SetAuthKey.CancelWishimport(locale))
            view.author = i.user
            await i.response.send_message(embed=embed, view=view)
            view.message = await i.original_response()
        except Exception as e:  # skipcq: PYL-W0703
            capture_exception(e)
            await i.response.send_message(
                embed=models.ErrorEmbed(
                    description=text_map.get(567, locale)
                ).set_title(135, locale, i.user),
                ephemeral=True,
            )

    @check_wish_history()
    @app_commands.command(name="history", description=_("View wish history", hash=478))
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("Check other user's data", hash=416))
    async def wish_history(
        self, inter: discord.Interaction, member: Optional[discord.User] = None
    ):
        i: models.Inter = inter  # type: ignore
        locale = (await get_user_lang(i.user.id, self.bot.pool)) or i.locale
        embeds = await get_wish_history_embeds(i, "", member)

        await WishHistoryPaginator(
            i,
            embeds,
            [
                select_banner := WishFilter.SelectBanner(locale),
                WishFilter.SelectRarity(text_map.get(661, locale), select_banner),
            ],
        ).start()

    @check_wish_history()
    @app_commands.command(
        name="overview", description=_("View you genshin wish overview", hash=484)
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("Check other user's data", hash=416))
    async def wish_overview(
        self,
        inter: discord.Interaction,
        member: Optional[discord.User | discord.Member] = None,
    ) -> None:
        i: models.Inter = inter  # type: ignore
        await i.response.defer()
        member = member or i.user
        locale = await get_user_lang(i.user.id, self.bot.pool) or i.locale

        client = ambr.AmbrTopAPI(self.bot.session, to_ambr_top(locale))

        wishes: List[WishItem] = []
        uid = await get_uid(member.id, self.bot.pool)
        rows = await self.bot.pool.fetch(
            "SELECT wish_name, wish_banner_type, wish_rarity, wish_time FROM wish_history WHERE user_id = $1 AND uid = $2 ORDER BY wish_id DESC",
            member.id,
            uid
        )
        for row in rows:
            wishes.append(
                WishItem(
                    name=row["wish_name"],
                    banner=row["wish_banner_type"],
                    rarity=row["wish_rarity"],
                    time=row["wish_time"],
                )
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
                        item = await client.get_character(str(item_id))
                        if not isinstance(item, ambr.Character):
                            item = await client.get_weapon(item_id)
                    if isinstance(item, ambr.Character | ambr.Weapon):
                        recents.append(
                            RecentWish(name=item.name, pull_num=pull, icon=item.icon)
                        )
                    else:
                        recents.append(RecentWish(name=wish.name, pull_num=pull))
                    pull = 0
            recents.reverse()

            title = ""
            if banner_id == 100:
                title = text_map.get(647, locale)
            elif banner_id == 301:
                title = text_map.get(645, locale) + " 1"
            elif banner_id == 400:
                title = text_map.get(645, locale) + " 2"
            elif banner_id == 302:
                title = text_map.get(646, locale)
            elif banner_id == 200:
                title = text_map.get(655, locale)

            wish_data = WishData(
                title=title,
                total_wishes=len(banner_wishes),
                four_star=len(four_star),
                five_star=len(five_star),
                pity=pity,
                recents=recents,
            )
            options.append(
                discord.SelectOption(
                    label=title,
                    value=str(banner_id),
                )
            )
            all_wish_data[str(banner_id)] = wish_data

        if not all_wish_data:
            return await i.followup.send(
                embed=models.ErrorEmbed().set_author(
                    name=text_map.get(731, locale),
                    icon_url=i.user.display_avatar.url,
                )
            )

        if "400" in all_wish_data and "301" in all_wish_data:
            temp = all_wish_data["301"].pity
            all_wish_data["301"].pity += all_wish_data["400"].pity
            all_wish_data["400"].pity += temp

        dark_mode = await get_user_theme(i.user.id, self.bot.pool)
        current_banner = list(all_wish_data.keys())[0]
        fp = await main_funcs.draw_wish_overview_card(
            models.DrawInput(
                loop=self.bot.loop,
                session=self.bot.session,
                locale=locale,
                dark_mode=dark_mode,
            ),
            all_wish_data[current_banner],
        )
        fp.seek(0)
        embed = models.DefaultEmbed().set_user_footer(member, uid)
        embed.set_image(url="attachment://wish_overview_0.jpeg")
        
        for option in options:
            if option.value == current_banner:
                option.default = True
                break

        await WishOverviewPaginator(
            i, [embed], current_banner, all_wish_data, options, fp
        ).start(edit=True)


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(WishCog(bot))
