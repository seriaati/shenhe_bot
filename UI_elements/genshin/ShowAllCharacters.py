from typing import Any, List

import genshin
from discord import File, Interaction, Locale, SelectOption
from discord.ui import Select

import asset
import config
from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView
from utility.utils import default_embed, get_user_appearance_mode
from yelan.draw import draw_big_character_card


class View(BaseView):
    def __init__(
        self,
        locale: Locale | str,
        characters: List[genshin.models.Character],
        options: List[SelectOption],
    ):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(ElementSelect(options, text_map.get(142, locale)))
        self.locale = locale
        self.characters = characters


class ElementSelect(Select):
    def __init__(self, options: List[SelectOption], placeholder: str):
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        await i.response.edit_message(
            embed=default_embed().set_author(
                name=text_map.get(644, self.view.locale), icon_url=asset.loader
            ),
            attachments=[],
        )
        fp = await draw_big_character_card(
            self.view.characters,
            i.client.session,
            await get_user_appearance_mode(i.user.id, i.client.db),
            self.view.locale,
            self.values[0],
        )
        fp.seek(0)
        file = File(fp, filename="characters.jpeg")
        embed = default_embed().set_image(url="attachment://characters.jpeg")
        await i.edit_original_response(embed=embed, attachments=[file])
