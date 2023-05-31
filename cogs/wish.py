from typing import Dict, List, Optional

import discord
import yaml
from discord import app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands

import ambr
import dev.models as models
from apps.db.tables.user_settings import Settings
from apps.draw import main_funcs
from apps.text_map import text_map, to_ambr_top
from apps.wish.models import (RecentWish, WishData, WishHistory, WishInfo,
                              WishItem)
from dev.exceptions import WishFileImportError
from ui.wish import set_auth_key, wish_filter
from utils import get_wish_history_embeds, get_wish_info_embed, log
from utils.paginators import WishHistoryPaginator, WishOverviewPaginator


class WishCog(commands.GroupCog, name="wish"):
    def __init__(self, bot) -> None:
        self.bot: models.BotModel = bot
        super().__init__()

    @app_commands.command(
        name="import", description=_("import your genshin wish history", hash=474)
    )
    async def wish_import(self, inter: discord.Interaction) -> None:
        i: models.Inter = inter  # type: ignore
        view = set_auth_key.View()
        await view.start(i)

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
        lang = await i.client.db.settings.get(i.user.id, Settings.LANG) or str(i.locale)
        try:
            rows = yaml.safe_load((await file.read()).decode("utf-8"))
            if rows is None:
                raise WishFileImportError

            wish_history = [WishHistory(**row) for row in rows]

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

            uid = await i.client.db.users.get_uid(i.user.id)
            linked = await i.client.db.wish.check_linked(uid)
            embed = get_wish_info_embed(i.user, lang, wish_info, uid, linked)
            view = set_auth_key.View()
            await view.init(i)
            view.clear_items()
            view.add_item(set_auth_key.ConfirmWishimport(lang, wish_history))  # type: ignore
            view.add_item(set_auth_key.CancelWishimport(lang))
            view.author = i.user
            await i.response.send_message(embed=embed, view=view)
            view.message = await i.original_response()
        except Exception as e:  # skipcq: PYL-W0703
            log.exception("Error while importing wish history", exc_info=e)
            raise WishFileImportError

    @app_commands.command(name="history", description=_("View wish history", hash=478))
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("Check other user's data", hash=416))
    async def wish_history(
        self, inter: discord.Interaction, member: Optional[discord.User] = None
    ):
        i: models.Inter = inter  # type: ignore
        lang = await i.client.db.settings.get(i.user.id, Settings.LANG) or str(i.locale)
        embeds = await get_wish_history_embeds(i, "", member)

        await WishHistoryPaginator(
            i,
            embeds,
            [
                select_banner := wish_filter.SelectBanner(lang),
                wish_filter.SelectRarity(text_map.get(661, lang), select_banner),
            ],
        ).start()

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
        lang = await i.client.db.settings.get(i.user.id, Settings.LANG) or str(i.locale)

        client = ambr.AmbrTopAPI(self.bot.session, to_ambr_top(lang))

        wishes: List[WishItem] = []
        uid = await i.client.db.users.get_uid(member.id)
        rows = await self.bot.pool.fetch(
            "SELECT wish_name, wish_banner_type, wish_rarity, wish_time FROM wish_history WHERE user_id = $1 AND uid = $2 ORDER BY wish_id DESC",
            member.id,
            uid,
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
                title = text_map.get(647, lang)
            elif banner_id == 301:
                title = text_map.get(645, lang) + " 1"
            elif banner_id == 400:
                title = text_map.get(645, lang) + " 2"
            elif banner_id == 302:
                title = text_map.get(646, lang)
            elif banner_id == 200:
                title = text_map.get(655, lang)

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
                    name=text_map.get(731, lang),
                    icon_url=i.user.display_avatar.url,
                )
            )

        if "400" in all_wish_data and "301" in all_wish_data:
            temp = all_wish_data["301"].pity
            all_wish_data["301"].pity += all_wish_data["400"].pity
            all_wish_data["400"].pity += temp

        dark_mode = await i.client.db.settings.get(i.user.id, Settings.DARK_MODE)
        current_banner = list(all_wish_data.keys())[0]
        fp = await main_funcs.draw_wish_overview_card(
            models.DrawInput(
                loop=self.bot.loop,
                session=self.bot.session,
                lang=lang,
                dark_mode=dark_mode,
            ),
            all_wish_data[current_banner],
        )
        fp.seek(0)

        for option in options:
            if option.value == current_banner:
                option.default = True
                break

        await WishOverviewPaginator(
            i, current_banner, all_wish_data, options, fp
        ).start(edit=True)


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(WishCog(bot))
