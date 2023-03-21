from typing import Any, List, Union
from apps.draw.main_funcs import draw_artifact_card
from apps.text_map import text_map

import discord
import enkanetwork as enka
from discord import ui, utils

import apps.genshin.custom_model as custom_model
import asset
import config
from ui.genshin import EnkaDamageCalc, ProfileSettings
from ui.others.settings import CustomImage
from utility import DefaultEmbed, divide_chunks, get_user_appearance_mode
from yelan.damage_calculator import return_current_status


class View(custom_model.EnkaView):
    def __init__(
        self,
        character_options: List[discord.SelectOption],
        locale: Union[discord.Locale, str],
    ):
        super().__init__(timeout=config.mid_timeout)

        options: List[List[discord.SelectOption]] = list(
            divide_chunks(character_options, 25)
        )

        self.add_item(OverviewButton(text_map.get(43, locale)))
        self.add_item(BoxButton(options, text_map.get(105, locale)))
        self.add_item(CalculateDamageButton(text_map.get(348, locale)))
        self.add_item(SetCustomImage(locale))
        self.add_item(ShowArtifacts(text_map.get(92, locale)))
        self.add_item(InfoButton())
        self.add_item(CardSettings())

        self.original_children = self.children.copy()
        self.character_options = character_options


class InfoButton(ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary, emoji=asset.info_emoji, row=1
        )
        self.view: View

    async def callback(self, i: custom_model.CustomInteraction):
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
        self.view: View

    async def callback(self, i: custom_model.CustomInteraction):
        set_custom_image = utils.get(self.view.children, custom_id="set_custom_image")
        calculate = utils.get(self.view.children, custom_id="calculate")
        show_artifacts = utils.get(self.view.children, custom_id="show_artifacts")

        self.disabled = True
        set_custom_image.disabled = True  # type: ignore
        calculate.disabled = True  # type: ignore
        show_artifacts.disabled = True  # type: ignore

        [fp, fp_two] = self.view.overview_fps
        fp.seek(0)
        fp_two.seek(0)
        attachments = [
            discord.File(fp, filename="profile.jpeg"),
            discord.File(fp_two, filename="character.jpeg"),
        ]
        await i.response.edit_message(
            embeds=self.view.overview_embeds,
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
        self.view: custom_model.EnkaView

    async def callback(self, i: custom_model.CustomInteraction) -> Any:
        character = utils.get(self.view.data.characters, id=int(self.view.character_id))
        if character is None:
            raise AssertionError

        await CustomImage.return_custom_image_interaction(
            self.view, i, int(self.view.character_id), character.element.name
        )


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
        self.view: custom_model.EnkaView

    async def callback(self, i: custom_model.CustomInteraction):
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
        self.view: custom_model.EnkaView

    async def callback(self, i: custom_model.CustomInteraction) -> Any:
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
        self.view: custom_model.EnkaView

    async def callback(self, i: custom_model.CustomInteraction) -> Any:
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
        self.view: custom_model.EnkaView

    async def callback(self, i: custom_model.CustomInteraction) -> Any:
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


class CardSettings(ui.Button):
    def __init__(self):
        super().__init__(emoji=asset.settings_emoji, row=1, disabled=True)
        self.view: custom_model.EnkaView

    async def callback(self, i: custom_model.CustomInteraction) -> Any:
        view = ProfileSettings.View(self.view.locale, self.view)
        view.author = i.user
        await i.response.edit_message(
            embed=view.gen_settings_embed(), view=view, attachments=[]
        )
        view.message = await i.original_response()
