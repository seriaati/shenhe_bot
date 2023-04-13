from typing import List

import discord

from .paginator import GeneralPaginator, GeneralPaginatorView


class WishHistoryPaginatorView(GeneralPaginatorView):
    def __init__(self, embeds: List[discord.Embed], locale: str) -> None:
        super().__init__(embeds, locale)

        self.rarity_filters: List[str] = []
        self.banner_filters: List[str] = []


class WishHistoryPaginator(GeneralPaginator):
    def setup_view(self, locale: discord.Locale | str) -> WishHistoryPaginatorView:
        return WishHistoryPaginatorView(self.embeds, str(locale))
