import io
from typing import Any, List

from discord import (ButtonStyle, Embed, File, Interaction, Locale, Member,
                     SelectOption, User, utils)
from discord.ui import Button, Select
from enkanetwork.model.base import CharacterInfo, EnkaNetworkResponse

import asset
import config
from apps.draw.main_funcs import draw_artifact_card
from apps.genshin.custom_model import DrawInput, EnkaView, OriginalInfo
from apps.text_map.text_map_app import text_map
from data.game.artifact_slot import get_artifact_slot_emoji
from UI_base_models import BaseView, GoBackButton
from UI_elements.genshin import EnkaDamageCalculator
from UI_elements.others.settings.CustomImage import (
    change_user_custom_image, get_user_custom_image,
    get_user_custom_image_embed, get_user_custom_image_options)
from utility.utils import (default_embed, divide_chunks,
                           get_user_appearance_mode)
from yelan.damage_calculator import return_current_status


class View(BaseView):
    def __init__(
        self,
        overview_embed: List[Embed],
        overview_fp: List[io.BytesIO],
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

        options: List[List[SelectOption]] = list(
            divide_chunks(self.character_options, 25)
        )

        self.add_item(OverviewButton(text_map.get(43, locale)))
        self.add_item(BoxButton(options, text_map.get(105, locale)))
        self.add_item(CalculateDamageButton(text_map.get(348, locale)))
        self.add_item(SetCustomImage(locale))
        self.add_item(ShowArtifacts(text_map.get(92, locale)))
        self.add_item(InfoButton())

        self.original_children = self.children.copy()


class InfoButton(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.secondary, emoji=asset.info_emoji, row=1)

    async def callback(self, i: Interaction):
        self.view: View
        await i.response.send_message(
            embed=default_embed(message=text_map.get(399, self.view.locale)),
            ephemeral=True,
        )


class OverviewButton(Button):
    def __init__(self, label: str):
        super().__init__(
            style=ButtonStyle.primary,
            label=label,
            custom_id="overview",
            disabled=True,
            row=0,
            emoji=asset.overview_emoji,
        )

    async def callback(self, i: Interaction):
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
            File(fp, filename="profile.jpeg"),
            File(fp_two, filename="character.jpeg"),
        ]
        await i.response.edit_message(
            embeds=self.view.overview_embed,
            attachments=attachments,
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
            disabled=True,
            row=1,
            emoji=asset.image_emoji,
        )

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        options = await get_user_custom_image_options(i, int(self.view.character_id))
        custom_image = await get_user_custom_image(
            i.user.id, int(self.view.character_id), i.client.pool
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
            i.user.id, int(self.view.character_id), i.client.pool
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
            i.user.id, int(self.view.character_id), i.client.pool
        )
        embed = await get_user_custom_image_embed(
            i, self.view.locale, str(self.view.character_id), custom_image, False
        )
        await i.response.edit_message(embed=embed)


class BoxButton(Button):
    def __init__(self, options: List[List[SelectOption]], label: str):
        super().__init__(
            emoji=asset.character_emoji,
            style=ButtonStyle.blurple,
            row=0,
            label=label,
            custom_id="box",
        )
        self.options = options

    async def callback(self, i: Interaction):
        self.view: EnkaView
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
            style=ButtonStyle.blurple,
            label=label,
            disabled=True,
            custom_id="calculate",
            row=0,
            emoji=asset.calculator_emoji,
        )

    async def callback(self, i: Interaction) -> Any:
        self.view: EnkaView
        view = EnkaDamageCalculator.View(self.view, self.view.locale, i.client.browsers)
        view.author = i.user
        await return_current_status(i, view)
        view.message = await i.original_response()


class ShowArtifacts(Button):
    def __init__(self, label: str):
        super().__init__(
            label=label,
            style=ButtonStyle.blurple,
            custom_id="show_artifacts",
            disabled=True,
            emoji=asset.artifact_emoji,
            row=1,
        )

    async def callback(self, i: Interaction) -> Any:
        self.view: EnkaView

        character = utils.get(self.view.data.characters, id=int(self.view.character_id))

        if character:
            original_info = OriginalInfo(view=self.view, embed=i.message.embeds[0], children=self.view.children.copy())  # type: ignore

            self.view.clear_items()
            for index in range(5):
                self.view.add_item(
                    ArtifactSlot(get_artifact_slot_emoji(index), index, character)
                )

            self.view.add_item(GoBackButton(original_info))
            await i.response.edit_message(view=self.view)
        else:
            await i.response.defer()


class ArtifactSlot(Button):
    def __init__(self, emoji: str, slot: int, character: CharacterInfo):
        super().__init__(emoji=emoji, style=ButtonStyle.blurple)
        self.slot = slot
        self.character = character

    async def callback(self, i: Interaction):
        self.view: EnkaView

        await i.response.defer()

        fp = await draw_artifact_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=self.view.locale,
                dark_mode=await get_user_appearance_mode(i.user.id, i.client.pool),
            ),
            self.character.equipments[self.slot],
            self.character,
        )

        file_ = File(fp, filename="artifact.jpeg")
        fp.seek(0)
        await i.edit_original_response(
            embed=default_embed().set_image(url="attachment://artifact.jpeg"),
            attachments=[file_],
            view=self.view,
        )
