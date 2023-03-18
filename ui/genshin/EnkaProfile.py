import io
from typing import Any, List

import discord
import enkanetwork as enka
from discord import ui, utils

import apps.genshin.custom_model as custom_model
import asset
import config
from apps.draw.main_funcs import draw_artifact_card
from apps.text_map.text_map_app import text_map
from base_ui import BaseView
from ui.genshin import EnkaDamageCalc, ProfileImageSelect
from ui.others.settings import CustomImage
from utility.utils import DefaultEmbed, divide_chunks, get_user_appearance_mode
from yelan.damage_calculator import return_current_status


class View(BaseView):
    def __init__(
        self,
        overview_embed: List[discord.Embed],
        overview_fp: List[io.BytesIO],
        character_options: List[discord.SelectOption],
        data: enka.model.base.EnkaNetworkResponse,
        eng_data: enka.model.base.EnkaNetworkResponse,
        member: discord.User | discord.Member,
        locale: discord.Locale | str,
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

        options: List[List[discord.SelectOption]] = list(
            divide_chunks(self.character_options, 25)
        )

        self.add_item(OverviewButton(text_map.get(43, locale)))
        self.add_item(BoxButton(options, text_map.get(105, locale)))
        self.add_item(CalculateDamageButton(text_map.get(348, locale)))
        self.add_item(SetCustomImage(locale))
        self.add_item(ShowArtifacts(text_map.get(92, locale)))
        self.add_item(InfoButton())

        self.original_children = self.children.copy()


class InfoButton(ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary, emoji=asset.info_emoji, row=1
        )

    async def callback(self, i: custom_model.CustomInteraction):
        self.view: View
        await i.response.send_message(
            embed=DefaultEmbed(description=text_map.get(399, self.view.locale)),
            ephemeral=True,
        )


class OverviewButton(ui.Button):
    def __init__(self, label: str):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=label,
            custom_id="overview",
            disabled=True,
            row=0,
            emoji=asset.overview_emoji,
        )

    async def callback(self, i: custom_model.CustomInteraction):
        self.view: View

        overview = utils.get(self.view.children, custom_id="overview")
        set_custom_image = utils.get(self.view.children, custom_id="set_custom_image")
        calculate = utils.get(self.view.children, custom_id="calculate")
        show_artifacts = utils.get(self.view.children, custom_id="show_artifacts")

        overview.disabled = True  # type: ignore
        set_custom_image.disabled = True  # type: ignore
        calculate.disabled = True  # type: ignore
        show_artifacts.disabled = True  # type: ignore

        [fp, fp_two] = self.view.overview_fp
        fp.seek(0)
        fp_two.seek(0)
        attachments = [
            discord.File(fp, filename="profile.jpeg"),
            discord.File(fp_two, filename="character.jpeg"),
        ]
        await i.response.edit_message(
            embeds=self.view.overview_embed,
            attachments=attachments,
            view=self.view,
        )


class SetCustomImage(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            style=discord.ButtonStyle.green,
            label=text_map.get(62, locale),
            custom_id="set_custom_image",
            disabled=True,
            row=1,
            emoji=asset.image_emoji,
        )

    async def callback(self, i: custom_model.CustomInteraction) -> Any:
        self.view: custom_model.EnkaView

        options = await CustomImage.get_user_custom_image_options(
            int(self.view.character_id), i.client.pool, i.user.id
        )
        custom_image = await CustomImage.get_user_custom_image(
            i.user.id, int(self.view.character_id), i.client.pool
        )
        embed = await CustomImage.get_user_custom_image_embed(
            i, self.view.locale, str(self.view.character_id), custom_image, False
        )
        view = ProfileImageSelect.CustomImageView(options, self.view.locale, self.view)
        view.author = i.user
        await i.response.edit_message(embed=embed, view=view, attachments=[])
        view.message = await i.original_response()


class BoxButton(ui.Button):
    def __init__(self, options: List[List[discord.SelectOption]], label: str):
        super().__init__(
            emoji=asset.character_emoji,
            style=discord.ButtonStyle.blurple,
            row=0,
            label=label,
            custom_id="box",
        )
        self.options = options

    async def callback(self, i: custom_model.CustomInteraction):
        self.view: custom_model.EnkaView
        self.view.clear_items()
        count = 1
        for option in self.options:
            character_num = len(option)
            self.view.add_item(
                PageSelect(
                    option,
                    text_map.get(157, self.view.locale)
                    + f" ({count}~{count+character_num-1})",
                )
            )
            count += character_num

        await i.response.edit_message(view=self.view)


class PageSelect(ui.Select):
    def __init__(self, character_options: list[discord.SelectOption], plceholder: str):
        super().__init__(placeholder=plceholder, options=character_options)

    async def callback(self, i: custom_model.CustomInteraction) -> Any:
        self.view: custom_model.EnkaView
        self.view.character_id = self.values[0]
        await EnkaDamageCalc.go_back_callback(i, self.view)


class CalculateDamageButton(ui.Button):
    def __init__(self, label: str):
        super().__init__(
            style=discord.ButtonStyle.blurple,
            label=label,
            disabled=True,
            custom_id="calculate",
            row=0,
            emoji=asset.calculator_emoji,
        )

    async def callback(self, i: custom_model.CustomInteraction) -> Any:
        self.view: custom_model.EnkaView
        view = EnkaDamageCalc.View(self.view, self.view.locale, i.client.browsers)
        view.author = i.user
        await return_current_status(i, view)
        view.message = await i.original_response()


class ShowArtifacts(ui.Button):
    def __init__(self, label: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.blurple,
            custom_id="show_artifacts",
            disabled=True,
            emoji=asset.artifact_emoji,
            row=1,
        )

    async def callback(self, i: custom_model.CustomInteraction) -> Any:
        self.view: custom_model.EnkaView

        character = utils.get(self.view.data.characters, id=int(self.view.character_id))
        if not character:
            raise AssertionError

        await i.response.defer()
        fp = await draw_artifact_card(
            custom_model.DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=self.view.locale,
                dark_mode=await get_user_appearance_mode(i.user.id, i.client.pool),
            ),
            [e for e in character.equipments if e.type is enka.EquipmentsType.ARTIFACT],
            character,
        )
        fp.seek(0)

        file_ = discord.File(fp, filename="artifact.png")
        await i.edit_original_response(attachments=[file_])
