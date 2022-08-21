import traceback

import discord

from apps.text_map.text_map_app import text_map
from utility.utils import error_embed


class DebugView(discord.ui.View):
    def __init__(self, traceback_message=''):
        self.tb = traceback_message
        super().__init__(timeout=None)

    @discord.ui.button(label='顯示除錯用訊息', style=discord.ButtonStyle.gray, custom_id='show_debug_message_button')
    async def show_debug_msg(self, i: discord.Interaction, button: discord.Button):
        try:
            await i.response.send_message(embed=error_embed(f'除錯用訊息', f'```py\n{self.tb}\n```'), ephemeral=True)
        except discord.HTTPException:
            await i.response.send_message(content='錯誤訊息過長, 已 print 在 console 裡', ephemeral=True)
            print(self.tb)


class DefaultView(discord.ui.View):
    async def on_error(self, i: discord.Interaction, e: Exception, item) -> None:
        if isinstance(e, discord.HTTPException) and e.code == 10062:
            return
        embed = error_embed(message=text_map.get(
            513, i.locale))
        embed.set_author(name=text_map.get(
            135, i.locale), icon_url=i.user.avatar)
        traceback_message = traceback.format_exc()
        view = DebugView(traceback_message)
        seria = i.client.get_user(410036441129943050)
        try:
            await i.channel.send(embed=embed, view=view)
        except discord.Forbidden:
            pass
        embed.set_footer(
            text=f'{i.user.name}#{i.user.discriminator} {i.user.id}')
        await seria.send(embed=embed, view=view)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

        try:
            await self.message.edit(view=self)
        except AttributeError:
            print('ATTRIBUTE_ERROR:'+str(self.children))
        except (discord.NotFound, discord.HTTPException):
            pass
