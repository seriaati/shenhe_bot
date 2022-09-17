import config
from debug import DefaultView
from discord.errors import Forbidden
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
        try:
            await i.message.delete()
        except Forbidden:
            await i.followup.send(embed=error_embed(message='申鶴沒有移除訊息的權限，請檢查權限設定。').set_author(name="訊息刪除失敗", icon_url=self.author.display_avatar.url))
