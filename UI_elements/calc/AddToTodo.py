from typing import Any, Dict
from apps.text_map.text_map_app import text_map
from discord import ButtonStyle, Interaction, Locale
from discord.ui import Button
from utility.utils import default_embed


class AddToTodo(Button):
    def __init__(
        self,
        materials: Dict[int, int],
        locale: Locale | str,
    ):
        super().__init__(
            style=ButtonStyle.blurple, label=text_map.get(175, locale), row=2
        )
        self.materials = materials
        self.locale = locale

    async def callback(self, i: Interaction) -> Any:
        for item_id, item_count in self.materials.items():
            async with i.client.pool.acquire() as db:
                await db.execute(
                    "INSERT INTO todo (user_id, item, count, max) VALUES (?, ?, 0, ?) ON CONFLICT (user_id, item) DO UPDATE SET item = ?, max = max + ? WHERE user_id = ?",
                    (i.user.id, item_id, item_count, item_id, item_count, i.user.id),
                )
            await db.commit()
            
        await i.response.send_message(
            embed=default_embed(message=text_map.get(178, self.locale)).set_author(
                name=text_map.get(179, self.locale), icon_url=i.user.display_avatar.url
            ),
            ephemeral=True,
        )
