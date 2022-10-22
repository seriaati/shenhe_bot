import discord
from UI_base_models import BaseView
import config
from typing import Dict, List
import io

from utility.utils import default_embed


class View(BaseView):
    def __init__(
        self,
        images: Dict[int, io.BytesIO],
        placeholder: str,
        options: List[discord.SelectOption],
    ):
        super().__init__(timeout=config.long_timeout)
        self.images = images
        self.add_item(Select(placeholder, options))


class Select(discord.ui.Select):
    def __init__(self, placeholder: str, options: List[discord.SelectOption]):
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, i: discord.Interaction):
        embed = default_embed()
        embed.set_image(url="attachment://overview.jpeg")
        fp = self.view.images[int(self.values[0])]
        fp.seek(0)
        image = discord.File(fp, filename="overview.jpeg")
        await i.response.edit_message(
            embed=embed, attachments=[image]
        )
