
from typing import Any

import aiosqlite
import config
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from debug import DefaultView
from discord import Interaction, Locale
from discord.ui import Button
from utility.utils import default_embed


class View(DefaultView):
    def __init__(self, locale: Locale | str):
        super().__init__(timeout=config.mid_timeout)


class Appearance(Button):
    def __init__(self, label: str):
        super().__init__(emoji="🖥️", label=label)

    async def callback(self, i: Interaction) -> Any:
        user_locale = await get_user_locale(i.user.id, i.client.db)
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute(
            "INSERT INTO dark_mode_settings (user_id) VALUES (?) ON CONFLICT (user_id) DO UPDATE SET toggle = toggle",
            (i.user.id,),
        )
        await c.execute(
            "SELECT toggle FROM dark_mode_settings WHERE user_id = ?", (i.user.id,)
        )
        (toggle,) = await c.fetchone()
        emoji = '🌙' if toggle == 1 else '☀️'
        toggle_text = 535 if toggle == 1 else 536
        embed = default_embed(f'{text_map.get(101, i.locale, user_locale)}: {emoji} {text_map.get(toggle_text, i.locale, user_locale)}')
        embed.set_author(name=f'🖥️ {text_map.get(534, i.locale, user_locale)}')
