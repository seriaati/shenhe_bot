from typing import Union

import discord

import dev.asset as asset
from apps.text_map import text_map
from apps.wish.utils import get_wish_history_embeds
from dev.models import Inter
from utils import WishHistoryPaginatorView


class SelectBanner(discord.ui.Select):
    def __init__(self, locale: Union[discord.Locale, str]):
        options = [
            discord.SelectOption(label=f"{text_map.get(645, locale)} 1", value="301"),
            discord.SelectOption(label=f"{text_map.get(645, locale)} 2", value="400"),
            discord.SelectOption(label=text_map.get(646, locale), value="302"),
            discord.SelectOption(label=text_map.get(647, locale), value="100"),
            discord.SelectOption(label=text_map.get(655, locale), value="200"),
        ]
        super().__init__(
            placeholder=text_map.get(662, locale),
            options=options,
            row=3,
            max_values=len(options),
            min_values=0,
        )
        self.view: WishHistoryPaginatorView

    async def callback(self, i: Inter):
        await filter_callback(self, i)


class SelectRarity(discord.ui.Select):
    def __init__(self, placeholder: str, select_banner: SelectBanner):
        options = [
            discord.SelectOption(label="5", value="5", emoji=asset.five_star_emoji),
            discord.SelectOption(label="4", value="4", emoji=asset.four_star_emoji),
            discord.SelectOption(label="3", value="3", emoji=asset.three_star_emoji),
        ]
        super().__init__(
            placeholder=placeholder,
            row=2,
            options=options,
            max_values=len(options),
            min_values=0,
        )
        self.select_banner = select_banner
        self.view: WishHistoryPaginatorView

    async def callback(self, i: Inter):
        await filter_callback(self, i)


async def filter_callback(self_var: SelectBanner | SelectRarity, i: Inter):
    if isinstance(self_var, SelectBanner):
        self_var.view.banner_filters = self_var.values
        for option in self_var.options:
            option.default = option.value in self_var.view.banner_filters
    elif isinstance(self_var, SelectRarity):
        self_var.view.rarity_filters = self_var.values
        for option in self_var.options:
            option.default = option.value in self_var.view.rarity_filters

    query = ""
    for index, filter_ in enumerate(self_var.view.banner_filters):
        if index == 0:
            query += "("
        query += f"wish_banner_type = {filter_} OR "
        if index == len(self_var.view.banner_filters) - 1:
            query = query[:-4] + ") AND "

    for index, filter_ in enumerate(self_var.view.rarity_filters):
        if index == 0:
            query += "("
        query += f"wish_rarity = {filter_} OR "
        if index == len(self_var.view.rarity_filters) - 1:
            query = query[:-4] + ") AND "

    self_var.view.current_page = 0
    self_var.view.embeds = await get_wish_history_embeds(i, query)
    await self_var.view.update_children(i)
