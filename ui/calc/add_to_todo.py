from typing import Any, Dict

from discord import ButtonStyle, Locale
from discord.ui import Button

from apps.text_map import text_map
from dev.models import DefaultEmbed, Inter


class AddButton(Button):
    def __init__(
        self,
        materials: Dict[int, int],
        lang: Locale | str,
    ):
        super().__init__(
            style=ButtonStyle.blurple, label=text_map.get(175, lang), row=2
        )
        self.materials = materials
        self.lang = lang

    async def callback(self, i: Inter) -> Any:
        for item_id, item_count in self.materials.items():
            await i.client.pool.execute(
                "INSERT INTO todo (user_id, item, max) VALUES ($1, $2, $3) ON CONFLICT (user_id, item) DO UPDATE SET max = todo.max + $3",
                i.user.id,
                str(item_id),
                item_count,
            )

        await i.response.send_message(
            embed=DefaultEmbed(description=text_map.get(178, self.lang)).set_author(
                name=text_map.get(179, self.lang), icon_url=i.user.display_avatar.url
            ),
            ephemeral=True,
        )
