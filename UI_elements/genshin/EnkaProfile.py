import io
from typing import Any, List

from discord import (ButtonStyle, Embed, File, Interaction, Locale, Member,
                     SelectOption, User)
from discord.ui import Button, Select
from enkanetwork import EnkaNetworkResponse

import asset
import config
from apps.genshin.custom_model import EnkaView
from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView
from UI_elements.genshin import EnkaDamageCalculator
from UI_elements.others.settings.CustomImage import (
    change_user_custom_image, get_user_custom_image,
    get_user_custom_image_embed, get_user_custom_image_options)
from utility.utils import (default_embed, divide_chunks,
                           get_user_appearance_mode)
from yelan.damage_calculator import return_damage
from yelan.draw import draw_profile_overview_card


class View(BaseView):
    def __init__(
        self,
        overview_embed: Embed,
        overview_fp: io.BytesIO,
        character_options: List[SelectOption],
        data: EnkaNetworkResponse,
        eng_data: EnkaNetworkResponse,
        member: User | Member,
        locale: Locale | str,
    ):
        super().__init__(timeout=config.mid_timeout)
        self.overview_embed = overview_embed
        self.overview_fp = overview_fp
        self.character_options = character_options
        self.character_id = "0"
        self.data = data
        self.eng_data = eng_data
        self.member = member
        self.locale = locale

        self.add_item(overview := OverviewButton(text_map.get(43, locale)))
        self.add_item(calculate := CalculateDamageButton(text_map.get(348, locale)))
        self.add_item(custom := SetCustomImage(locale))
        self.add_item(InfoButton())
        overview.disabled = True
        calculate.disabled = True
        custom.disabled = True

        options = list(divide_chunks(self.character_options, 25))
        count = 1
        for option in options:
            character_num = len([o for o in option if o.value != 0])
            self.add_item(
                PageSelect(
                    option,
                    text_map.get(157, locale) + f" ({count}~{count+character_num-1})",
                )
            )
            count += character_num


class InfoButton(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.secondary, emoji=asset.info_emoji)

    async def callback(self, i: Interaction):
        self.view: View
        await i.response.send_message(
            embed=default_embed(message=text_map.get(399, self.view.locale)),
            ephemeral=True,
        )


class OverviewButton(Button):
    def __init__(self, label: str):
        super().__init__(style=ButtonStyle.primary, label=label, custom_id="overview")

    async def callback(self, i: Interaction):
        self.view: View
        overview = [
            item
            for item in self.view.children
            if isinstance(item, Button) and item.custom_id == "overview"
        ][0]
        set_custom_image = [
            item
            for item in self.view.children
            if isinstance(item, Button) and item.custom_id == "set_custom_image"
        ][0]
        calculate = [
            item
            for item in self.view.children
            if isinstance(item, Button) and item.custom_id == "calculate"
        ][0]
        overview.disabled = True
        set_custom_image.disabled = True
        calculate.disabled = True
        fp = self.view.overview_fp
        fp.seek(0)
        attachment = File(fp, filename="profile.jpeg")
        await i.response.edit_message(
            embed=self.view.overview_embed,
            attachments=[attachment],
            view=self.view,
        )


class CustomImageView(BaseView):
    def __init__(
        self, options: List[SelectOption], locale: Locale | str, original_view: EnkaView
    ):
        super().__init__(timeout=config.long_timeout)

        self.add_item(SelectImage(options, locale))
        self.add_item(GoBackToProfile(original_view))
        self.add_item(Reload(original_view))
        self.character_id = original_view.character_id
        self.locale = original_view.locale


class SetCustomImage(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            style=ButtonStyle.green,
            label=text_map.get(62, locale),
            custom_id="set_custom_image",
        )

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        options = await get_user_custom_image_options(i, int(self.view.character_id))
        custom_image = await get_user_custom_image(
            i.user.id, i.client.db, int(self.view.character_id)
        )
        embed = await get_user_custom_image_embed(
            i, self.view.locale, str(self.view.character_id), custom_image, False
        )
        view = CustomImageView(options, self.view.locale, self.view)
        view.author = i.user
        await i.response.edit_message(embed=embed, view=view, attachments=[])
        view.message = await i.original_response()


class GoBackToProfile(Button):
    def __init__(self, original_view: EnkaView):
        super().__init__(emoji=asset.back_emoji, row=1)
        self.original_view = original_view

    async def callback(self, i: Interaction):
        await EnkaDamageCalculator.go_back_callback(i, self.original_view)


class Reload(Button):
    def __init__(self, original_view: EnkaView):
        super().__init__(emoji=asset.reload_emoji, row=1, style=ButtonStyle.blurple)
        self.original_view = original_view

    async def callback(self, i: Interaction):
        self.view: View
        custom_image = await get_user_custom_image(
            i.user.id, i.client.db, int(self.view.character_id)
        )
        embed = await get_user_custom_image_embed(
            i, self.view.locale, str(self.view.character_id), custom_image, False
        )
        options = await get_user_custom_image_options(i, int(self.view.character_id))
        self.view.clear_items()
        self.view.add_item(SelectImage(options, self.view.locale))
        self.view.add_item(GoBackToProfile(self.original_view))
        self.view.add_item(Reload(self.original_view))
        await i.response.edit_message(embed=embed, view=self.view)


class SelectImage(Select):
    def __init__(self, options: List[SelectOption], locale: Locale | str):
        disabled = True if not options else False
        super().__init__(
            placeholder=text_map.get(279 if disabled else 404, locale),
            options=options
            if not disabled
            else [SelectOption(label="None", value="0")],
            disabled=disabled,
            row=0,
        )

    async def callback(self, i: Interaction):
        self.view: CustomImageView
        await change_user_custom_image(i, self.values[0], int(self.view.character_id))
        custom_image = await get_user_custom_image(
            i.user.id, i.client.db, int(self.view.character_id)
        )
        embed = await get_user_custom_image_embed(
            i, self.view.locale, str(self.view.character_id), custom_image, False
        )
        await i.response.edit_message(embed=embed)


class PageSelect(Select):
    def __init__(self, character_options: list[SelectOption], plceholder: str):
        super().__init__(placeholder=plceholder, options=character_options)

    async def callback(self, i: Interaction) -> Any:
        self.view: EnkaView
        self.view.character_id = self.values[0]
        await EnkaDamageCalculator.go_back_callback(i, self.view)


class CalculateDamageButton(Button):
    def __init__(self, label: str):
        super().__init__(
            style=ButtonStyle.blurple, label=label, disabled=True, custom_id="calculate"
        )

    async def callback(self, i: Interaction) -> Any:
        self.view: EnkaView
        view = EnkaDamageCalculator.View(self.view, self.view.locale)
        view.author = i.user
        await return_damage(i, view)
        view.message = await i.original_response()
