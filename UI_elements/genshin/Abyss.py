import aiosqlite
from apps.text_map.utils import get_user_locale
from debug import DefaultView
from discord import User, Interaction, Locale, Embed, SelectOption, File
from discord.ui import Select
from apps.text_map.text_map_app import text_map
from typing import Any
import config
from utility.utils import default_embed, get_user_appearance_mode
from yelan.draw import draw_abyss_floor_card


class View(DefaultView):
    def __init__(
        self,
        author: User,
        embeds: list[Embed],
        locale: Locale,
        user_locale: str,
        db: aiosqlite.Connection,
    ):
        super().__init__(timeout=config.mid_timeout)
        self.author = author
        self.db = db

        self.add_item(FloorSelect(embeds, locale, user_locale))


class FloorSelect(Select):
    def __init__(self, embeds: list[Embed], locale: Locale, user_locale: str):
        options = [
            SelectOption(label=text_map.get(43, locale, user_locale), value="overview")
        ]
        for index in range(0, len(embeds["floors"])):
            options.append(
                SelectOption(
                    label=f"{text_map.get(146, locale, user_locale)} {9+index} {text_map.get(147, locale, user_locale)}",
                    value=index,
                )
            )
        super().__init__(
            placeholder=text_map.get(148, locale, user_locale), options=options
        )
        self.embeds = embeds

    async def callback(self, i: Interaction) -> Any:
        await i.response.defer()
        if self.values[0] == "overview":
            fp = self.embeds["overview_card"]
            fp.seek(0)
            image = File(fp, filename="overview_card.jpeg")
            await i.edit_original_response(
                embed=self.embeds["overview"],
                attachments=[image],
            )
        else:
            embed = default_embed()
            embed.set_image(url="attachment://floor.jpeg")
            dark_mode = await get_user_appearance_mode(i.user.id, i.client.db)
            user_locale = await get_user_locale(i.user.id, i.client.db)
            fp = await draw_abyss_floor_card(
                dark_mode,
                user_locale or i.locale,
                self.embeds["floors"][int(self.values[0])],
            )
            fp.seek(0)
            image = File(fp, filename="floor.jpeg")
            await i.edit_original_response(embed=embed, attachments=[image])
