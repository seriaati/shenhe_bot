from typing import List

import aiosqlite
from apps.genshin.utils import get_material
from debug import DefaultView
from discord import ButtonStyle, Interaction, Locale, Member, SelectOption
from discord.ui import Button, Modal, Select, TextInput
from apps.text_map.utils import get_user_locale
from apps.text_map.text_map_app import text_map
from apps.todo import get_todo_embed
from utility.utils import error_embed


class View(DefaultView):
    def __init__(self, db: aiosqlite.Connection, disabled: bool, author: Member, locale: Locale, user_locale: str):
        super().__init__(timeout=None)
        self.db = db
        self.author = author
        self.add_item(AddItem(text_map.get(203, locale, user_locale)))
        self.add_item(RemoveItem(
            disabled, text_map.get(205, locale, user_locale)))
        self.add_item(ClearItems(
            disabled, text_map.get(206, locale, user_locale)))

    async def interaction_check(self, i: Interaction) -> bool:
        user_locale = await get_user_locale(i.user.id, self.db)
        if i.user.id != self.author.id:
            await i.response.send_message(embed=error_embed().set_author(name=text_map.get(143, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        return i.user.id == self.author.id


class AddItem(Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=ButtonStyle.green)

    async def callback(self, i: Interaction):
        self.view: View
        user_locale = await get_user_locale(i.user.id, self.view.db)
        c: aiosqlite.Cursor = await self.view.db.cursor()
        await c.execute('SELECT COUNT(item) FROM todo WHERE user_id = ?', (i.user.id,))
        count = (await c.fetchone())[0]
        if count >= 125:
            return await i.response.send_message(embed=error_embed(message=text_map.get(176, i.locale, user_locale)).set_author(name=text_map.get(177, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        modal = AddItemModal(i.locale, user_locale)
        await i.response.send_modal(modal)
        await modal.wait()
        if not modal.count.value.isnumeric():
            return await i.followup.send(embed=error_embed(message=text_map.get(187, i.locale, user_locale)).set_author(name=text_map.get(190, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        await c.execute('INSERT INTO todo (user_id, item, count) VALUES (?, ?, ?) ON CONFLICT (user_id, item) DO UPDATE SET count = count + ? WHERE user_id = ? AND item = ?', (i.user.id, text_map.get_material_id_with_name(modal.item.value), int(modal.count.value), int(modal.count.value), i.user.id, text_map.get_material_id_with_name(modal.item.value)))
        await self.view.db.commit()
        embed, empty = await get_todo_embed(self.view.db, i.user, i.locale)
        view = View(self.view.db, empty, i.user, i.locale, user_locale)
        await i.edit_original_response(embed=embed, view=view)


class RemoveItem(Button):
    def __init__(self, disabled: bool, label: str):
        super().__init__(label=label, style=ButtonStyle.red, disabled=disabled)

    async def callback(self, i: Interaction):
        self.view: View
        user_locale = await get_user_locale(i.user.id, self.view.db)
        self.view: View
        c: aiosqlite.Cursor = await self.view.db.cursor()
        await c.execute('SELECT item FROM todo WHERE user_id = ?', (i.user.id,))
        todos = await c.fetchall()
        options = []
        for index, tuple in enumerate(todos):
            options.append(SelectOption(
                label=text_map.get_material_name(tuple[0], i.locale, user_locale), value=tuple[0], emoji=get_material(tuple[0])['emoji']))
        self.view.clear_items()
        self.view.add_item(RemoveItemSelect(
            options, text_map.get(207, i.locale, user_locale)))
        await i.response.edit_message(view=self.view)


class ClearItems(Button):
    def __init__(self, disabled: bool, label: str):
        super().__init__(label=label, disabled=disabled)

    async def callback(self, i: Interaction):
        self.view: View
        c: aiosqlite.Cursor = await self.view.db.cursor()
        user_locale = await get_user_locale(i.user.id, self.view.db)
        await c.execute('DELETE FROM todo WHERE user_id = ?', (i.user.id,))
        await self.view.db.commit()
        view = View(self.view.db, True, i.user, i.locale, user_locale)
        embed = (await get_todo_embed(self.view.db, i.user, i.locale))[0]
        await i.response.edit_message(embed=embed, view=view)


class AddItemModal(Modal):
    item = TextInput(
        label='item_name',
        placeholder='for_example:_mora',
    )

    count = TextInput(
        label='item_amount',
        placeholder='for_example:_90'
    )

    def __init__(self, locale: Locale, user_locale: str) -> None:
        super().__init__(title=text_map.get(203, locale, user_locale), timeout=None)
        self.item.label = text_map.get(208, locale, user_locale)
        self.item.placeholder = text_map.get(209, locale, user_locale)
        self.count.label = text_map.get(210, locale, user_locale)
        self.count.placeholder = text_map.get(170, locale, user_locale)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        self.stop()


class RemoveItemModal(Modal):
    count = TextInput(
        label='item_amount',
        placeholder='for_example:_90_(leave_blank_clear)',
        required=False
    )

    def __init__(self, locale: Locale, user_locale: str) -> None:
        super().__init__(title=text_map.get(205, locale, user_locale), timeout=None)
        self.count.label = text_map.get(210, locale, user_locale)
        self.count.placeholder = text_map.get(211, locale, user_locale)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        self.stop()


class RemoveItemSelect(Select):
    def __init__(self, options: List[SelectOption], placeholder: str):
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, i: Interaction):
        self.view: View
        c: aiosqlite.Cursor = await self.view.db.cursor()
        user_locale = await get_user_locale(i.user.id, self.view.db)
        modal = RemoveItemModal(i.locale, user_locale)
        await i.response.send_modal(modal)
        await modal.wait()
        if modal.count.value != '':
            await c.execute('SELECT count FROM todo WHERE user_id = ? AND item = ?', (i.user.id, self.values[0]))
            count = await c.fetchone()
            if (count is not None) and (int(modal.count.value) > int(count[0])):
                return await i.followup.send(embed=error_embed().set_author(name=text_map.get(212, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
            if not modal.count.value.isnumeric():
                return await i.followup.send(embed=error_embed(message=text_map.get(187, i.locale, user_locale)).set_author(name=text_map.get(190, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        if modal.count.value == '':
            await c.execute('DELETE FROM todo WHERE item = ? AND user_id = ?', (self.values[0], i.user.id))
        else:
            await c.execute('UPDATE todo SET count = ? WHERE user_id = ? AND item = ?', (count[0]-int(modal.count.value), i.user.id, self.values[0]))
            await c.execute('DELETE FROM todo WHERE count = 0 AND user_id = ?', (i.user.id,))
        await self.view.db.commit()
        embed, disabled = await get_todo_embed(self.view.db, i.user, i.locale)
        view = View(self.view.db, disabled, i.user, i.locale, user_locale)
        await i.edit_original_response(embed=embed, view=view)
