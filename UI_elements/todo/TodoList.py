from typing import List

import aiosqlite
import sentry_sdk
from debug import DefaultModal, DefaultView
from discord import ButtonStyle, Interaction, Locale, User, SelectOption
from discord.ui import Button, Select, TextInput
from apps.text_map.utils import get_user_locale
from apps.text_map.text_map_app import text_map
from apps.todo.todo_app import get_todo_embed, return_todo
from utility.utils import error_embed, log
import config


class View(DefaultView):
    def __init__(
        self,
        db: aiosqlite.Connection,
        disabled: bool,
        author: User,
        locale: Locale,
        user_locale: str,
    ):
        super().__init__(timeout=config.long_timeout)
        self.db = db
        self.author = author
        self.add_item(AddItem(text_map.get(203, locale, user_locale)))
        self.add_item(RemoveItem(disabled, text_map.get(205, locale, user_locale)))
        self.add_item(ClearItems(disabled, text_map.get(206, locale, user_locale)))


class AddItem(Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=ButtonStyle.green, row=2)

    async def callback(self, i: Interaction):
        self.view: View
        user_locale = await get_user_locale(i.user.id, self.view.db)
        c: aiosqlite.Cursor = await self.view.db.cursor()
        await c.execute("SELECT COUNT(item) FROM todo WHERE user_id = ?", (i.user.id,))
        count = (await c.fetchone())[0]
        if count >= 125:
            return await i.response.send_message(
                embed=error_embed(
                    message=text_map.get(176, i.locale, user_locale)
                ).set_author(
                    name=text_map.get(177, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        modal = AddItemModal(i.locale, user_locale)
        await i.response.send_modal(modal)
        await modal.wait()
        if modal.count.value == "":
            return
        if not modal.count.value.isnumeric():
            return await i.followup.send(
                embed=error_embed(
                    message=text_map.get(187, i.locale, user_locale)
                ).set_author(
                    name=text_map.get(190, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        await c.execute(
            "INSERT INTO todo (user_id, item, count) VALUES (?, ?, ?) ON CONFLICT (user_id, item) DO UPDATE SET count = count + ? WHERE user_id = ? AND item = ?",
            (
                i.user.id,
                text_map.get_material_id_with_name(modal.item.value),
                int(modal.count.value),
                int(modal.count.value),
                i.user.id,
                text_map.get_material_id_with_name(modal.item.value),
            ),
        )
        await self.view.db.commit()
        result, empty = await get_todo_embed(
            self.view.db, i.user, i.locale, i.client.session
        )
        view = View(self.view.db, empty, i.user, i.locale, user_locale)
        await return_todo(result, i, view, i.client.db)


class RemoveItem(Button):
    def __init__(self, disabled: bool, label: str):
        super().__init__(label=label, style=ButtonStyle.red, disabled=disabled, row=2)

    async def callback(self, i: Interaction):
        self.view: View
        user_locale = await get_user_locale(i.user.id, self.view.db)
        self.view: View
        c: aiosqlite.Cursor = await self.view.db.cursor()
        await c.execute("SELECT item FROM todo WHERE user_id = ?", (i.user.id,))
        todos = await c.fetchall()
        options = []
        for index, tpl in enumerate(todos):
            options.append(
                SelectOption(
                    label=text_map.get_material_name(tpl[0], i.locale, user_locale),
                    value=tpl[0],
                )
            )
        self.view.clear_items()
        self.view.add_item(
            RemoveItemSelect(options, text_map.get(207, i.locale, user_locale))
        )
        await i.response.edit_message(view=self.view)


class ClearItems(Button):
    def __init__(self, disabled: bool, label: str):
        super().__init__(label=label, disabled=disabled, row=2)

    async def callback(self, i: Interaction):
        self.view: View
        c: aiosqlite.Cursor = await self.view.db.cursor()
        user_locale = await get_user_locale(i.user.id, self.view.db)
        await c.execute("DELETE FROM todo WHERE user_id = ?", (i.user.id,))
        await self.view.db.commit()
        view = View(self.view.db, True, i.user, i.locale, user_locale)
        result = (
            await get_todo_embed(self.view.db, i.user, i.locale, i.client.session)
        )[0]
        await return_todo(result, i, view, i.client.db)


class AddItemModal(DefaultModal):
    item = TextInput(
        label="item_name",
        placeholder="for_example:_mora",
    )

    count = TextInput(label="item_amount", placeholder="for_example:_90")

    def __init__(self, locale: Locale, user_locale: str) -> None:
        super().__init__(
            title=text_map.get(203, locale, user_locale), timeout=config.mid_timeout
        )
        self.item.label = text_map.get(208, locale, user_locale)
        self.item.placeholder = text_map.get(209, locale, user_locale)
        self.count.label = text_map.get(210, locale, user_locale)
        self.count.placeholder = text_map.get(170, locale, user_locale)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
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


class RemoveItemModal(DefaultModal):
    count = TextInput(
        label="item_amount",
        placeholder="for_example:_90_(leave_blank_clear)",
        required=False,
    )

    def __init__(self, locale: Locale, user_locale: str) -> None:
        super().__init__(
            title=text_map.get(205, locale, user_locale), timeout=config.mid_timeout
        )
        self.count.label = text_map.get(210, locale, user_locale)
        self.count.placeholder = text_map.get(211, locale, user_locale)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
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
        if modal.count.value != "":
            await c.execute(
                "SELECT count FROM todo WHERE user_id = ? AND item = ?",
                (i.user.id, self.values[0]),
            )
            count = await c.fetchone()
            if not modal.count.value.isnumeric():
                return await i.followup.send(
                    embed=error_embed(
                        message=text_map.get(187, i.locale, user_locale)
                    ).set_author(
                        name=text_map.get(190, i.locale, user_locale),
                        icon_url=i.user.display_avatar.url,
                    ),
                    ephemeral=True,
                )
            if (count is not None) and (int(modal.count.value) > int(count[0])):
                return await i.followup.send(
                    embed=error_embed().set_author(
                        name=text_map.get(212, i.locale, user_locale),
                        icon_url=i.user.display_avatar.url,
                    ),
                    ephemeral=True,
                )
        if modal.count.value == "":
            await c.execute(
                "DELETE FROM todo WHERE item = ? AND user_id = ?",
                (self.values[0], i.user.id),
            )
        else:
            await c.execute(
                "UPDATE todo SET count = ? WHERE user_id = ? AND item = ?",
                (count[0] - int(modal.count.value), i.user.id, self.values[0]),
            )
            await c.execute(
                "DELETE FROM todo WHERE count = 0 AND user_id = ?", (i.user.id,)
            )
        await self.view.db.commit()
        result, disabled = await get_todo_embed(
            self.view.db, i.user, i.locale, i.client.session
        )
        view = View(self.view.db, disabled, i.user, i.locale, user_locale)
        await return_todo(result, i, view, i.client.db)
