import io
from typing import Dict, List, Union

import discord

import dev.config as config
import dev.models as models
from apps.db import get_user_lang, get_user_theme
from apps.draw import main_funcs
from apps.text_map import text_map
from apps.wish.models import RecentWish, WishData
from dev.base_ui import BaseView
from dev.models import DefaultEmbed, DrawInput
from utility.paginator import GeneralPaginator


class View(BaseView):
    def __init__(
        self,
        locale: Union[discord.Locale, str],
        options: List[discord.SelectOption],
        all_wish_data: Dict[str, WishData],
        member: Union[discord.Member, discord.User],
    ):
        super().__init__(timeout=config.long_timeout)
        self.add_item(BannerSelect(locale, options, all_wish_data, member))
        self.all_wish_data = all_wish_data
        self.member = member
        self.locale = locale

    async def draw_overview_fp(
        self, i: models.Inter, wish_data: WishData
    ) -> io.BytesIO:
        fp = await main_funcs.draw_wish_overview_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=self.locale,
                dark_mode=await get_user_theme(i.user.id, i.client.pool),
            ),
            wish_data,
        )
        fp.seek(0)
        return fp

    async def draw_recents_fp(
        self, i: models.Inter, wish_recents: List[RecentWish]
    ) -> io.BytesIO:
        fp = await main_funcs.draw_wish_recents_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=self.locale,
                dark_mode=await get_user_theme(i.user.id, i.client.pool),
            ),
            wish_recents,
        )
        fp.seek(0)
        return fp


class BannerSelect(discord.ui.Select, View):
    def __init__(
        self,
        locale: Union[discord.Locale, str],
        options: List[discord.SelectOption],
        all_wish_data: Dict[str, WishData],
        member: Union[discord.Member, discord.User],
    ):
        super().__init__(placeholder=text_map.get(656, locale), options=options)
        self.locale = locale
        self.view: View
        self.all_wish_data = all_wish_data
        self.member = member

    async def callback(self, i: models.Inter):
        await i.response.defer()

        current_banner_data = self.all_wish_data[self.values[0]]
        embeds: List[discord.Embed] = []
        files: List[discord.File] = []

        embed = DefaultEmbed().set_user_footer(self.member)
        embed.set_image(url="attachment://overview.jpeg")
        fp = await self.draw_overview_fp(i, current_banner_data)
        fp.seek(0)
        image = discord.File(fp, filename="overview.jpeg")
        embeds.append(embed)
        files.append(image)

        if len(current_banner_data.recents) > 8:
            embed = DefaultEmbed().set_user_footer(self.member)
            embed.set_image(url="attachment://recents.jpeg")
            fp = await self.draw_recents_fp(i, current_banner_data.recents)
            fp.seek(0)
            image = discord.File(fp, filename="recents.jpeg")
            embeds.append(embed)
            files.append(image)

        await GeneralPaginator(i, embeds, [self], files).start(edit=True)
