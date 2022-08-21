from typing import Any, Dict, List

import aiosqlite
import config
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from debug import DefaultView
from discord import ButtonStyle, Interaction, Locale, Member
from discord.ui import Button
from utility.utils import default_embed, error_embed


class View(DefaultView):
    def __init__(self, db: aiosqlite.Connection, disabled: bool, author: Member, materials: Dict[str, int], locale: Locale, user_locale: str):
        super().__init__(timeout=config.long_timeout)
        self.author = author
        self.db = db
        self.add_item(AddToTodo(disabled, db, materials,
                      text_map.get(175, locale, user_locale)))

    async def interaction_check(self, i: Interaction) -> bool:
        user_locale = await get_user_locale(i.user.id, self.db)
        if i.user.id != self.author.id:
            await i.response.send_message(embed=error_embed().set_author(name=text_map.get(143, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        return i.user.id == self.author.id


class AddToTodo(Button):
    def __init__(self, disabled: bool, db: aiosqlite.Connection, materials: Dict[str, int], label: str):
        super().__init__(style=ButtonStyle.blurple, label=label, disabled=disabled)
        self.db = db
        self.materials = materials

    async def callback(self, i: Interaction) -> Any:
        c = await self.db.cursor()
        user_locale = await get_user_locale(i.user.id, self.db)
        await c.execute('SELECT COUNT(item) FROM todo WHERE user_id = ?', (i.user.id,))
        count = (await c.fetchone())[0]
        if count >= 125:
            return await i.response.send_message(embed=error_embed(message=text_map.get(176, i.locale, user_locale)).set_author(name=text_map.get(177, i.locale, user_locale), icon_url=i.user.avatar))
        for item_id, item_count in self.materials.items():
            await c.execute('INSERT INTO todo (user_id, item, count) VALUES (?, ?, ?) ON CONFLICT (user_id, item) DO UPDATE SET item = ?, count = count + ? WHERE user_id = ?', (i.user.id, item_id, item_count, item_id, item_count, i.user.id))
        await self.db.commit()
        await i.response.send_message(embed=default_embed(message=text_map.get(178, i.locale, user_locale)).set_author(name=text_map.get(179, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
