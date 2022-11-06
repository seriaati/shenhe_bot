import discord
from UI_base_models import BaseView
from apps.text_map.utils import get_user_locale
import config
from typing import List

from utility.utils import default_embed, get_user_appearance_mode
from yelan.draw import draw_wish_overview_card


class View(BaseView):
    def __init__(
        self,
        user: discord.User | discord.Member,
        placeholder: str,
        options: List[discord.SelectOption],
        all_wish_data: dict,
    ):
        super().__init__(timeout=config.long_timeout)
        self.user=  user
        self.add_item(Select(placeholder, options))
        self.all_wish_data = all_wish_data


class Select(discord.ui.Select):
    def __init__(self, placeholder: str, options: List[discord.SelectOption]):
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, i: discord.Interaction):
        self.view: View
        embed = default_embed()
        embed.set_image(url="attachment://overview.jpeg")
        fp = await draw_wish_overview_card(
            i.client.session,
            await get_user_locale(i.user.id, i.client.db) or i.locale,
            self.view.all_wish_data[self.values[0]],
            self.view.user.display_avatar.url,
            self.view.user.name,
            await get_user_appearance_mode(i.user.id, i.client.db),
        )
        fp.seek(0)
        image = discord.File(fp, filename="overview.jpeg")
        await i.response.edit_message(embed=embed, attachments=[image])
