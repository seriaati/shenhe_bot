from typing import List

import discord

import dev.config as config
import dev.models as models
from apps.db import get_user_lang, get_user_theme
from apps.draw import main_funcs
from dev.base_ui import BaseView
from dev.models import DefaultEmbed, DrawInput


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

    async def callback(self, i: models.Inter):
        embed = DefaultEmbed()
        embed.set_image(url="attachment://overview.jpeg")
        fp = await main_funcs.draw_wish_overview_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=await get_user_lang(i.user.id, i.client.pool) or i.locale,
                dark_mode=await get_user_theme(i.user.id, i.client.pool),
            ),
            self.view.all_wish_data[self.values[0]],
            self.view.user.display_avatar.url,
            self.view.user.name,
        )
        fp.seek(0)
        image = discord.File(fp, filename="overview.jpeg")
        await i.response.edit_message(embed=embed, attachments=[image])
