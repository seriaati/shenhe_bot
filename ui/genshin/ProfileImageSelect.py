from typing import List

import discord
from discord import ui

import apps.genshin.custom_model as custom_model
import asset
import config
from apps.text_map.text_map_app import text_map
from base_ui import BaseView
from ui.genshin import EnkaDamageCalc
from ui.others.settings import CustomImage


class CustomImageView(BaseView):
    def __init__(
        self,
        options: List[discord.SelectOption],
        locale: discord.Locale | str,
        original_view: custom_model.EnkaView,
    ):
        super().__init__(timeout=config.long_timeout)

        self.add_item(SelectImage(options, locale))
        self.add_item(GoBackToProfile(original_view))
        self.add_item(Reload(original_view))
        self.character_id = original_view.character_id
        self.locale = original_view.locale


class GoBackToProfile(ui.Button):
    def __init__(self, original_view: custom_model.EnkaView):
        super().__init__(emoji=asset.back_emoji, row=1)
        self.original_view = original_view

    async def callback(self, i: custom_model.CustomInteraction):
        await EnkaDamageCalc.go_back_callback(i, self.original_view)


class Reload(ui.Button):
    def __init__(self, original_view: custom_model.EnkaView):
        super().__init__(
            emoji=asset.reload_emoji, row=1, style=discord.ButtonStyle.blurple
        )
        self.original_view = original_view

    async def callback(self, i: custom_model.CustomInteraction):
        self.view: CustomImageView

        custom_image = await CustomImage.get_user_custom_image(
            i.user.id, int(self.view.character_id), i.client.pool
        )
        embed = await CustomImage.get_user_custom_image_embed(
            i, self.view.locale, str(self.view.character_id), custom_image, False
        )
        options = await CustomImage.get_user_custom_image_options(
            int(self.view.character_id), i.client.pool, i.user.id, self.view.locale
        )
        self.view.clear_items()
        self.view.add_item(SelectImage(options, self.view.locale))
        self.view.add_item(GoBackToProfile(self.original_view))
        self.view.add_item(Reload(self.original_view))
        await i.response.edit_message(embed=embed, view=self.view)


class SelectImage(ui.Select):
    def __init__(
        self, options: List[discord.SelectOption], locale: discord.Locale | str
    ):
        disabled = bool(not options)
        super().__init__(
            placeholder=text_map.get(279 if disabled else 404, locale),
            options=options
            if not disabled
            else [discord.SelectOption(label="None", value="0")],
            disabled=disabled,
            row=0,
        )

    async def callback(self, i: custom_model.CustomInteraction):
        self.view: CustomImageView
        await CustomImage.change_user_custom_image(i.user.id, int(self.view.character_id), self.values[0], i.client.pool)  # type: ignore
        custom_image = await CustomImage.get_user_custom_image(
            i.user.id, int(self.view.character_id), i.client.pool  # type: ignore
        )
        embed = await CustomImage.get_user_custom_image_embed(
            i, self.view.locale, str(self.view.character_id), custom_image, False
        )
        await i.response.edit_message(embed=embed)
