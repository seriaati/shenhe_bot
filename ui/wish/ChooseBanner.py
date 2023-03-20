from apps.genshin.custom_model import DrawInput
from apps.draw import main_funcs
from apps.text_map.utils import get_user_locale
import discord
from base_ui import BaseView
import config
from typing import List
from utility.utils import DefaultEmbed, get_user_appearance_mode


class View(BaseView):
    def __init__(
        self,
        user: discord.User | discord.Member,
        placeholder: str,
        options: List[discord.SelectOption],
        all_wish_data: dict,
    ):
        super().__init__(timeout=config.long_timeout)
        self.user = user
        self.add_item(Select(placeholder, options))
        self.all_wish_data = all_wish_data


class Select(discord.ui.Select):
    def __init__(self, placeholder: str, options: List[discord.SelectOption]):
        super().__init__(placeholder=placeholder, options=options)
        self.view: View

    async def callback(self, i: discord.Interaction):
        embed = DefaultEmbed()
        embed.set_image(url="attachment://overview.jpeg")
        fp = await main_funcs.draw_wish_overview_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=await get_user_locale(i.user.id, i.client.pool) or i.locale,
                dark_mode=await get_user_appearance_mode(i.user.id, i.client.pool),
            ),
            self.view.all_wish_data[self.values[0]],
            self.view.user.display_avatar.url,
            self.view.user.name,
        )
        fp.seek(0)
        image = discord.File(fp, filename="overview.jpeg")
        await i.response.edit_message(embed=embed, attachments=[image])
