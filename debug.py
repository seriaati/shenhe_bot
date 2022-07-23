import traceback

from discord import ButtonStyle, Interaction, HTTPException
from discord.ui import Button, View, button

from utility.utils import errEmbed


class DebugView(View):
    def __init__(self, traceback_message = ''):
        self.tb = traceback_message
        super().__init__(timeout=None)

    @button(label='顯示除錯用訊息', style=ButtonStyle.gray, custom_id='show_debug_message_button')
    async def show_debug_msg(self, i: Interaction, button: Button):
        try:
            await i.response.send_message(embed=errEmbed(f'除錯用訊息', f'```py\n{self.tb}\n```'), ephemeral=True)
        except HTTPException:
            await i.response.send_message(content='錯誤訊息過長, 已 print 在 console 裡', ephemeral=True)
            print(self.tb)


class DefaultView(View):
    async def on_error(self, i: Interaction, e: Exception, item) -> None:
        traceback_message = traceback.format_exc()
        view = DebugView(traceback_message)
        embed = errEmbed(message='發生了未知的錯誤, 請至[申鶴的 issue 頁面](https://github.com/seriaati/shenhe_bot/issues)回報這個錯誤').set_author(
            name='未知錯誤', icon_url=i.user.avatar)
        await i.channel.send(embed=embed, view=view)