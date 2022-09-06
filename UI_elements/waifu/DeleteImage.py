import config
from debug import DefaultView
from discord import ButtonStyle, Interaction, User
from discord.ui import Button, button
from utility.utils import error_embed


class View(DefaultView):
    def __init__(self, author: User):
        super().__init__(timeout=config.long_timeout)
        self.author = author

    async def interaction_check(self, interaction: Interaction) -> bool:
        if self.author is None:
            return True
        if self.author.id != interaction.user.id:
            await interaction.response.send_message(
                embed=error_embed().set_author(
                    name="你不是這個指令的發起人", icon_url=interaction.user.display_avatar.url
                ),
                ephemeral=True,
            )
        return self.author.id == interaction.user.id

    @button(label="刪除圖片", emoji="🗑️", style=ButtonStyle.gray)
    async def deleteImage(self, i: Interaction, button: Button):
        await i.response.defer()
        await i.message.delete()
