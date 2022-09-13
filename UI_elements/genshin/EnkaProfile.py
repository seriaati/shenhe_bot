from typing import Any, Dict, List

import aiosqlite
import config
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from debug import DefaultView
from discord import ButtonStyle, Embed, File, Interaction, Locale, SelectOption, User
from discord.ui import Button, Select
from enkanetwork import EnkaNetworkResponse
from enkanetwork.model.character import CharacterInfo
from pyppeteer.browser import Browser
from ui_elements.genshin import EnkaDamageCalculator
from utility.utils import default_embed, error_embed
from yelan.damage_calculator import return_damage
from yelan.draw import draw_character_card


class View(DefaultView):
    def __init__(
        self,
        embeds: Dict[int, Embed],
        artifact_embeds: dict[int, Embed],
        character_options: list[SelectOption],
        data: EnkaNetworkResponse,
        member: User,
        eng_data: EnkaNetworkResponse,
        author: User,
        db: aiosqlite.Connection,
        locale: Locale,
        user_locale: str,
        user_uid: str,
        characters: List[CharacterInfo],
        browser: Browser,
    ):
        super().__init__(timeout=config.mid_timeout)
        self.embeds = embeds
        self.artifact_embeds = artifact_embeds
        self.character_options = character_options
        self.character_id = None
        self.author = author
        self.data = data
        self.member = member
        self.eng_data = eng_data
        self.db = db
        self.user_uid = user_uid
        self.characters = characters
        self.browser = browser
        self.add_item(ViewArtifacts(text_map.get(92, locale, user_locale)))
        self.add_item(CalculateDamageButton(text_map.get(348, locale, user_locale)))
        self.add_item(
            PageSelect(character_options, text_map.get(157, locale, user_locale))
        )
        self.children[0].disabled = True
        self.children[1].disabled = True


class PageSelect(Select):
    def __init__(self, character_options: list[SelectOption], plceholder: str):
        super().__init__(placeholder=plceholder, options=character_options)

    async def callback(self, i: Interaction) -> Any:
        user_locale = await get_user_locale(i.user.id, self.view.db)
        self.view: View
        damage_calc_disabled = False
        card = None
        if self.values[0] != "0":
            card = i.client.enka_card_cache.get(
                f"{self.view.member.id} - {self.values[0]}"
            )
            if card is None:
                [character] = [
                    c for c in self.view.characters if c.id == int(self.values[0])
                ]
                card = await draw_character_card(
                    character, user_locale or i.locale, i.client.session
                )
                i.client.enka_card_cache[
                    f"{self.view.member.id} - {self.values[0]}"
                ] = card
        is_card = False if card is None else True
        artifact_disabled = True if is_card else False

        if self.values[0] == "0":
            artifact_disabled = True
            damage_calc_disabled = True

        self.view.children[0].disabled = artifact_disabled
        self.view.children[1].disabled = damage_calc_disabled
        self.view.character_id = self.values[0]

        if is_card:
            embed = default_embed()
            embed.set_image(url=f"attachment://card.jpeg")
            if self.view.user_uid is not None:
                embed.set_footer(
                    text=f"{text_map.get(123, i.locale, user_locale)}: {self.view.user_uid}"
                )
            else:
                embed.set_author(
                    name=self.view.member.display_name,
                    icon_url=self.view.member.display_avatar.url,
                )
            card.seek(0)
            file = File(card, "card.jpeg")
            await i.response.edit_message(
                embed=embed, view=self.view, attachments=[file]
            )
        else:
            embed = self.view.embeds[self.values[0]]
            if self.view.user_uid is not None:
                embed.set_footer(
                    text=f"{text_map.get(123, i.locale, user_locale)}: {self.view.user_uid}"
                )
            else:
                embed.set_author(
                    name=self.view.member.display_name,
                    icon_url=self.view.member.display_avatar.url,
                )
            await i.response.edit_message(embed=embed, view=self.view, attachments=[])


class ViewArtifacts(Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=ButtonStyle.blurple)

    async def callback(self, i: Interaction) -> Any:
        self.disabled = True
        await i.response.edit_message(
            embed=self.view.artifact_embeds[self.view.character_id],
            view=self.view,
            attachments=[],
        )


class CalculateDamageButton(Button):
    def __init__(self, label: str):
        super().__init__(style=ButtonStyle.blurple, label=label, disabled=True)

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        view = EnkaDamageCalculator.View(
            self.view, i.locale, await get_user_locale(i.user.id, self.view.db)
        )
        await return_damage(i, view)
        view.message = await i.original_response()
