import config
from debug import DefaultView
from discord import ButtonStyle, Interaction, User
from discord.ui import Button, button
from utility.utils import error_embed


class View(DefaultView):
    def __init__(self, author: User):
        super().__init__(timeout=config.long_timeout)
        self.author = author

    @button(label="刪除圖片", emoji="🗑️", style=ButtonStyle.gray)
    async def deleteImage(self, i: Interaction, button: Button):
        await i.response.defer()
        await i.message.delete()
