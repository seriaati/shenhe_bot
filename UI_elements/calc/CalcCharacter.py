from typing import List, Literal, Sequence

import aiohttp
import aiosqlite
import sentry_sdk
import config
from apps.genshin.utils import get_character
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.game.elements import convert_elements, elements
from UI_base_models import BaseModal, BaseView
from discord import Interaction, User, SelectOption, User
from discord.ui import Button, Modal, Select, TextInput
from genshin.models import BaseCharacter
from utility.utils import error_embed, log


class View(BaseView):
    def __init__(
        self,
        author: User,
        session: aiohttp.ClientSession,
        db: aiosqlite.Connection,
        characters: Sequence[BaseCharacter],
    ):
        super().__init__(timeout=config.mid_timeout)
        self.author = author
        self.session = session
        self.db = db
        self.character_id = ""
        self.levels = {}
        self.characters = characters

        element_names = list(convert_elements.values())
        element_emojis = list(elements.values())
        for index in range(0, 7):
            self.add_item(
                ElementButton(element_names[index], element_emojis[index], index // 4)
            )


class ElementButton(Button):
    def __init__(self, element_name: str, element_emoji: str, row: int):
        super().__init__(emoji=element_emoji, row=row)
        self.element = element_name

    async def callback(self, i: Interaction):
        self.view: View
        user_locale = await get_user_locale(i.user.id, self.view.db)
        locale = user_locale or i.locale
        options = []
        for character in self.view.characters:
            if character.element == self.element:
                options.append(
                    SelectOption(
                        label=text_map.get_character_name(character.id, locale),
                        emoji=get_character(character.id)["emoji"],
                        value=character.id,
                    )
                )
        placeholder = text_map.get(157, locale)
        self.view.clear_items()
        self.view.add_item(CharacterSelect(options, placeholder))
        await i.response.edit_message(view=self.view)


class CharacterSelect(Select):
    def __init__(self, options: List[SelectOption], placeholder: str):
        super().__init__(options=options, placeholder=placeholder)

    async def callback(self, i: Interaction):
        self.view: View
        modal = LevelModal(
            self.values[0], await get_user_locale(i.user.id, self.view.db) or i.locale
        )
        await i.response.send_modal(modal)
        await modal.wait()
        self.view.levels = {
            "target": modal.target.value,
            "a": modal.a.value,
            "e": modal.e.value,
            "q": modal.q.value,
        }
        self.view.character_id = self.values[0]
        self.view.stop()


class LevelModal(BaseModal):
    target = TextInput(
        label="character_level_target",
        placeholder="like: 90",
    )

    a = TextInput(
        label="attack_target",
        placeholder="like: 9",
    )

    e = TextInput(
        label="skill_target",
        placeholder="like: 4",
    )

    q = TextInput(
        label="burst_target",
        placeholder="like: 10",
    )

    def __init__(self, character_id: str, locale: Literal["Locale", "str"]) -> None:
        super().__init__(
            title=f"{text_map.get(181, locale)} {text_map.get_character_name(character_id, locale)} {text_map.get(182, locale)}",
            timeout=config.mid_timeout,
        )
        self.target.label = text_map.get(169, locale)
        self.target.placeholder = text_map.get(170, locale)
        self.a.label = text_map.get(171, locale)
        self.a.placeholder = text_map.get(172, locale)
        self.e.label = text_map.get(173, locale)
        self.e.placeholder = text_map.get(172, locale)
        self.q.label = text_map.get(174, locale)
        self.q.placeholder = text_map.get(172, locale)

    async def on_submit(self, i: Interaction) -> None:
        await i.response.defer()
        self.stop()

    async def on_error(self, i: Interaction, e: Exception) -> None:
        log.warning(
            f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
        )
        sentry_sdk.capture_exception(e)
        await i.response.send_message(
            embed=error_embed().set_author(
                name=text_map.get(135, i.locale), icon_url=i.user.display_avatar.url
            ),
            ephemeral=True,
        )
