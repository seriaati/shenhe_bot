from typing import Any, List
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from debug import DefaultView
from discord import User, Interaction
from discord.ui import Select
import config
from utility.utils import error_embed


class View(DefaultView):
    def __init__(self, choices: List, author: User):
        super().__init__(timeout=config.short_timeout)
        self.add_item(TagSelect(choices))
        self.tags = []
        self.author = author

    async def interaction_check(self, i: Interaction) -> bool:
        user_locale = await get_user_locale(i.user.id, self.db)
        if self.author.id != i.user.id:
            await i.response.send_message(
                embed=error_embed().set_author(
                    name=text_map.get(143, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        return self.author.id == i.user.id

class TagSelect(Select):
    def __init__(self, choices: List) -> None:
        super().__init__(
            placeholder="選擇你想要查詢的標籤",
            min_values=1,
            max_values=len(choices),
            options=choices,
        )

    async def callback(self, interaction: Interaction) -> Any:
        await interaction.response.defer()
        self.view.tags.append(self.values)
        self.view.stop()