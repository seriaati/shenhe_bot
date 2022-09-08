from typing import Any

import config
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.waifu.waifu_tags import nsfw_tags, sfw_tags
from debug import DefaultView
from discord import Interaction, SelectOption, User
from discord.ui import Select
from utility.utils import divide_chunks, error_embed


class View(DefaultView):
    def __init__(self, author: User, type: str):
        super().__init__(timeout=config.short_timeout)
        self.author = author
        self.tag = None
        options = []
        if type == "sfw":
            for tag_name, tag_info in sfw_tags.items():
                options.append(
                    SelectOption(
                        label=tag_name,
                        value=f'{str(tag_info["libs"])}/{tag_info["value"]}',
                        description=tag_info["description"],
                    )
                )
        elif type == "nsfw":
            for tag_name, tag_info in nsfw_tags.items():
                options.append(
                    SelectOption(
                        label=tag_name,
                        value=f'{str(tag_info["libs"])}/{tag_info["value"]}',
                        description=tag_info["description"],
                    )
                )
        divided = list(divide_chunks(options, 25))
        first = 1
        second = len(divided[0])
        for d in divided:
            self.add_item(TagSelect(d, f"{first}~{second}"))
            first += 25
            second = first + len(d)


class TagSelect(Select):
    def __init__(self, options: list, range: str):
        super().__init__(placeholder=f"選擇標籤 ({range})", options=options)

    async def callback(self, interaction: Interaction) -> Any:
        await interaction.response.defer()
        self.view.tag = self.values[0]
        self.view.stop()
