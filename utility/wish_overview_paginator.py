import io
from typing import Any, Dict, List, Union

import discord

from apps.db.utility import get_user_theme
from apps.draw import main_funcs
from apps.text_map import text_map
from apps.wish.models import RecentWish, WishData
from dev.models import DrawInput, Inter
from utility.paginator import GeneralPaginator, GeneralPaginatorView


class WishOverviewPaginatorView(GeneralPaginatorView):
    def __init__(
        self,
        embeds: List[discord.Embed],
        locale: str,
        current_banner: str,
        all_wish_data: Dict[str, WishData],
    ) -> None:
        super().__init__(embeds, locale)

        self.current_banner = current_banner
        self.all_wish_data = all_wish_data

    async def make_response(self, i: Inter) -> None:
        wish_data = self.all_wish_data[self.current_banner]
        current_page = self.current_page
        embed = self.embeds[0]

        if current_page == 0:
            fp = await self.draw_overview_fp(i, wish_data)
        else:
            first_num = 8 + 22 * (current_page - 1)
            fp = await self.draw_recents_fp(
                i,
                wish_data.recents[first_num : first_num + 22],
            )
        fp.seek(0)

        embed.set_image(url=f"attachment://wish_overview_{current_page}.jpeg")
        await i.response.edit_message(
            embed=embed,
            view=self,
            attachments=[
                discord.File(fp, filename=f"wish_overview_{current_page}.jpeg")
            ],
        )

    async def draw_overview_fp(self, i: Inter, wish_data: WishData) -> io.BytesIO:
        fp = await main_funcs.draw_wish_overview_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=self.locale,
                dark_mode=await get_user_theme(i.user.id, i.client.pool),
            ),
            wish_data,
        )
        return fp

    async def draw_recents_fp(
        self, i: Inter, wish_recents: List[RecentWish]
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
        return fp


class BannerSelect(discord.ui.Select):
    def __init__(
        self,
        locale: Union[discord.Locale, str],
        options: List[discord.SelectOption],
        all_wish_data: Dict[str, WishData],
        member: Union[discord.Member, discord.User],
    ) -> None:
        super().__init__(placeholder=text_map.get(656, locale), options=options)

        self.locale = locale
        self.all_wish_data = all_wish_data
        self.member = member
        self.view: WishOverviewPaginatorView

    async def callback(self, i: Inter) -> None:
        self.view.current_banner = self.values[0]
        self.view.current_page = 0

        total = len(self.all_wish_data[self.view.current_banner].recents)
        embed_ = self.view.embeds[0]
        embeds: List[discord.Embed] = [embed_]
        if total > 8:
            for _ in range(0, total - 8, 22):
                embeds.append(embed_)
        self.view.embeds = embeds

        for option in self.options:
            if option.value == self.view.current_banner:
                option.default = True
            else:
                option.default = False

        await self.view.update_children(i)


class WishOverviewPaginator(GeneralPaginator):
    def __init__(
        self,
        i: Inter,
        embeds: List[discord.Embed],
        current_banner: str,
        all_wish_data: Dict[str, WishData],
        select_options: List[discord.SelectOption],
        first_fp: io.BytesIO,
    ) -> None:
        super().__init__(i=i, embeds=embeds)

        self.current_banner = current_banner
        self.all_wish_data = all_wish_data
        self.select_options = select_options
        self.first_fp = first_fp

        total = len(self.all_wish_data[self.current_banner].recents)
        if total > 8:
            for _ in range(0, total - 8, 22):
                self.embeds.append(self.embeds[0])

    def setup_kwargs(self, view: GeneralPaginatorView) -> Dict[str, Any]:
        kwargs = {
            "view": view,
            "embed": self.embeds[0],
            "attachments": [
                discord.File(self.first_fp, filename="wish_overview_0.jpeg")
            ],
        }
        return kwargs

    def setup_view(
        self, locale: Union[discord.Locale, str]
    ) -> WishOverviewPaginatorView:
        view = WishOverviewPaginatorView(
            self.embeds, str(locale), self.current_banner, self.all_wish_data
        )
        view.add_item(
            BannerSelect(
                str(locale), self.select_options, self.all_wish_data, self.i.user
            )
        )
        return view
