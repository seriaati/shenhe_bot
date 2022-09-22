import asyncio
import aiosqlite
import config
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from discord import Interaction, TextStyle
from discord.ui import TextInput
from UI_base_models import BaseModal
from utility.utils import default_embed


class Modal(BaseModal):
    embed_title = TextInput(label="Title")
    embed_description = TextInput(label="Description", style=TextStyle.long)
    image_url = TextInput(label="Image URL", required=False)

    def __init__(self):
        super().__init__(title="Announcement", timeout=config.long_timeout)

    async def on_submit(self, i: Interaction) -> None:
        await i.response.defer()
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute("SELECT user_id FROM user_settings WHERE dev_msg = 1")
        user_ids = await c.fetchall()
        seria = i.client.get_user(410036441129943050) or await i.client.fetch_user(
            410036441129943050
        )
        for _, tpl in enumerate(user_ids):
            user_id = tpl[0]
            user = i.client.get_user(user_id) or await i.client.fetch_user(user_id)
            user_locale = await get_user_locale(user_id, i.client.db)
            embed = default_embed(self.embed_title.value, self.embed_description.value)
            embed.set_author(
                name=f"{seria.name}#{seria.discriminator}", icon_url=seria.avatar.url
            )
            embed.set_footer(text=text_map.get(524, "zh-TW", user_locale))
            embed.set_image(url=self.image_url.value)
            try:
                await user.send(embed=embed)
            except:
                pass
            await asyncio.sleep(1)
        await i.followup.send("completed.", ephemeral=True)
