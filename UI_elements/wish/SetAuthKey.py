import sqlite3

import aiosqlite
import genshin
import sentry_sdk
from apps.genshin.utils import get_dummy_client
from discord import Interaction, Locale, TextStyle
from discord.ui import TextInput
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from apps.text_map.convert_locale import to_genshin_py
from debug import DefaultModal
from utility.utils import default_embed, error_embed, log
import config


class Modal(DefaultModal):
    url = TextInput(
        label='Auth Key URL',
        placeholder='請ctrl+v貼上複製的連結',
        style=TextStyle.long,
        required=True
    )

    def __init__(self, db: aiosqlite.Connection, locale: Locale, user_locale: str | None):
        super().__init__(title=text_map.get(353, locale, user_locale), timeout=config.mid_timeout, custom_id='authkey_modal')
        self.db = db
        self.url.placeholder = text_map.get(132, locale, user_locale)
        
        # localization fro text input
        self.url.label = text_map.get(352, locale, user_locale)
        self.url.placeholder = text_map.get(354, locale, user_locale)

    async def on_submit(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.db)
        client = get_dummy_client()
        client.lang = to_genshin_py(user_locale or i.locale) or 'en-US'
        url = self.url.value
        authkey = genshin.utility.extract_authkey(url)
        log.info(f'[Wish Import][{i.user.id}]: [Authkey][{authkey}]')
        client.authkey = authkey
        await i.response.send_message(embed=default_embed(
            f'<a:LOADER:982128111904776242> {text_map.get(355, i.locale, user_locale)}'), ephemeral=True)
        try:
            wish_history = await client.wish_history()
        except Exception as e:
            return await i.edit_original_response(embed=error_embed(text_map.get(135, i.locale, user_locale), f'```py\n{e}\n```'))
        c = await self.db.cursor()
        for wish in wish_history:
            wish_time = wish.time.strftime("%Y/%m/%d %H:%M:%S")
            try:
                await c.execute('INSERT INTO wish_history (user_id, wish_name, wish_rarity, wish_time, wish_type, wish_banner_type, wish_id) VALUES (?, ?, ?, ?, ?, ?, ?)', (i.user.id, wish.name, wish.rarity, wish_time, wish.type, wish.banner_type, wish.id))
            except sqlite3.IntegrityError:
                pass
        await self.db.commit()
        await i.edit_original_response(embed=default_embed(f'<:wish:982419859117838386> {text_map.get(356, i.locale, user_locale)}'))

    async def on_error(self, i: Interaction, e: Exception) -> None:
        log.warning(
            f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
        )
        sentry_sdk.capture_exception(e)
        await i.response.send_message(
            embed=error_embed().set_author(
                name=text_map.get(135, i.locale), icon_url=i.user.avatar
            ),
            ephemeral=True,
        )