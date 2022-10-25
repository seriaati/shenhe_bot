from typing import List

from discord import Interaction, SelectOption
from discord.ui import Select

from apps.genshin.utils import get_wish_history_embed
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale


class SelectBanner(Select):
    def __init__(self, placeholder: str, options: List[SelectOption]):
        super().__init__(placeholder=placeholder, options=options, row=3)

    async def callback(self, i: Interaction):
        await filter_callback(self, i, self.view.banner_filters)


class SelectRarity(Select):
    def __init__(self, placeholder: str, select_banner: SelectBanner):
        super().__init__(placeholder=placeholder, row=2)
        self.add_option(label="5 ✦", value="5")
        self.add_option(label="4 ✦", value="4")
        self.add_option(label="3 ✦", value="3")
        self.select_banner = select_banner

    async def callback(self, i: Interaction):
        await filter_callback(self, i, self.view.rarity_filters)


async def filter_callback(self_var, i: Interaction, filter_list: List):
    user_locale = await get_user_locale(i.user.id, i.client.db)
    if self_var.values[0] not in filter_list:
        filter_list.append(self_var.values[0])
    else:
        filter_list.remove(self_var.values[0])

    for option in self_var.options:
        if option.value in filter_list:
            option.description = text_map.get(374, i.locale, user_locale)
        else:
            option.description = None

    query = ""
    for filter in self_var.view.banner_filters:
        if filter == "301":
            query += "(wish_banner_type = 301 OR wish_banner_type = 400) AND "
        else:
            query += f"wish_banner_type = {filter} AND "

    for index, filter in enumerate(self_var.view.rarity_filters):
        if index == 0:
            query += "("
        query += f"wish_rarity = {filter} OR "
        if index == len(self_var.view.rarity_filters) - 1:
            query = query[:-4] + ") AND "

    self_var.view.embeds = await get_wish_history_embed(i, query)
    await self_var.view.update_children(i)
