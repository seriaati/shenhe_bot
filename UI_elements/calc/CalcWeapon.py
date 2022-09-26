from typing import Any, List

import aiosqlite
import sentry_sdk
import config
from apps.genshin.utils import get_weapon
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseModal, BaseView
from discord import Interaction, Locale, User, SelectOption
from discord.ui import Modal, Select, TextInput
from utility.utils import error_embed, log


class View(BaseView):
    def __init__(self, weapons: List, author: User, db: aiosqlite.Connection, locale: Locale, user_locale: str):
        super().__init__(timeout=config.short_timeout)
        self.author = author
        self.db = db
        self.levels = {}
        self.weapon_id = ''
        placeholder = text_map.get(180, locale, user_locale)
        self.add_item(WeaponSelect(weapons, placeholder))


class WeaponSelect(Select):
    def __init__(self, weapons: List, placeholder: str):
        options = []
        for weapon in weapons:
            options.append(SelectOption(
                label=weapon.name, value=weapon.id, emoji=get_weapon(weapon.id)['emoji']))
        super().__init__(placeholder=placeholder, options=options)
        self.weapons = weapons

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        modal = LevelModal(self.values[0], i.locale, await get_user_locale(i.user.id, self.view.db))
        await i.response.send_modal(modal)
        await modal.wait()
        self.view.levels = {
            'current': modal.current.value,
            'target': modal.target.value
        }
        self.view.weapon_id = self.values[0]
        self.view.stop()


class LevelModal(BaseModal):
    current = TextInput(
        label='current_level', placeholder='like: 1')
    target = TextInput(label='target_level', placeholder='like: 90')

    def __init__(self, weapon_id: str, locale: Locale, user_locale: str) -> None:
        super().__init__(
            title=f'{text_map.get(181, locale, user_locale)} {text_map.get_weapon_name(weapon_id, locale, user_locale)} {text_map.get(182, locale, user_locale)}', timeout=config.mid_timeout)
        self.current.label = text_map.get(183, locale, user_locale)
        self.current.placeholder = text_map.get(184, locale, user_locale)
        self.target.label = text_map.get(185, locale, user_locale)
        self.target.placeholder = text_map.get(170, locale, user_locale)

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