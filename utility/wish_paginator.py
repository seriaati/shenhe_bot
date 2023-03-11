import discord
from typing import List

from utility.paginator import GeneralPaginator, GeneralPaginatorView


class WishPaginatorView(GeneralPaginatorView):
    def __init__(self, embeds: List[discord.Embed], locale: str):
        super().__init__(embeds, locale)

        self.rarity_filters = []
        self.banner_filters = []


class WishPaginator(GeneralPaginator):
    def setup_view(self, locale: discord.Locale | str) -> WishPaginatorView:
        return WishPaginatorView(self.embeds, str(locale))
