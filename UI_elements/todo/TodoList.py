from typing import Dict, List, Tuple
from ambr.client import AmbrTopAPI
from ambr.models import Material
from apps.text_map.convert_locale import to_ambr_top
from discord import ButtonStyle, Interaction, Locale, SelectOption
from discord.ui import Button, TextInput, Select
from apps.draw import main_funcs
import asset
import config
from apps.genshin.custom_model import DrawInput, TodoAction, TodoItem
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseModal, BaseView
from utility.todo_paginator import TodoPaginator, _view
from utility.utils import (
    DefaultEmbed,
    get_user_appearance_mode,
)


class View(BaseView):
    def __init__(
        self,
        todo_items: List[TodoItem],
        locale: Locale | str,
    ):
        super().__init__(timeout=config.long_timeout)
        self.todo_items = todo_items
        self.locale = locale
        self.add_item(AddItem(text_map.get(203, locale)))
        self.add_item(
            EditOrRemove(not todo_items, text_map.get(729, locale), TodoAction.EDIT)
        )
        self.add_item(
            EditOrRemove(not todo_items, text_map.get(205, locale), TodoAction.REMOVE)
        )
        self.add_item(ClearItems(not todo_items, text_map.get(206, locale)))


class AddItem(Button):
    def __init__(self, label: str):
        super().__init__(
            label=label, style=ButtonStyle.green, row=2, emoji=asset.add_emoji
        )

    async def callback(self, i: Interaction):
        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
        await i.response.send_modal(AddItemModal(locale))


class EditOrRemove(Button):
    def __init__(self, disabled: bool, label: str, action: TodoAction):
        super().__init__(
            label=label,
            style=ButtonStyle.primary if action is TodoAction.EDIT else ButtonStyle.red,
            disabled=disabled,
            row=2 if action is TodoAction.EDIT else 3,
            emoji=asset.edit_emoji if action is TodoAction.EDIT else asset.remove_emoji,
        )

        self.action = action

    async def callback(self, i: Interaction):
        self.view: _view
        self.view.clear_items()
        self.view.add_item(
            ItemSelect(
                self.view.locale,
                self.view.todo_items[
                    self.view.current_page * 14 : (self.view.current_page + 1) * 14
                ],
                self.action,
            )
        )
        await i.response.edit_message(view=self.view)


class ClearItems(Button):
    def __init__(self, disabled: bool, label: str):
        super().__init__(label=label, disabled=disabled, row=3, emoji=asset.clear_emoji)

    async def callback(self, i: Interaction):
        async with i.client.pool.acquire() as db:
            await db.execute("DELETE FROM todo WHERE user_id = ?", (i.user.id,))
            await db.commit()
        await return_todo(i)


class ItemSelect(Select):
    def __init__(
        self, locale: Locale | str, todo_items: List[TodoItem], action: TodoAction
    ):
        options: List[SelectOption] = []
        item_dict: Dict[str, str] = {}

        for todo_item in todo_items:
            if todo_item.name.isdigit():
                item_label = text_map.get_material_name(int(todo_item.name), locale)
                if isinstance(item_label, int):
                    item_label = todo_item.name
            else:
                item_label = todo_item.name

            item_dict[todo_item.name] = item_label
            options.append(SelectOption(label=item_label, value=todo_item.name))

        super().__init__(
            placeholder=text_map.get(207, locale),
            options=options,
        )

        self.locale = locale
        self.action = action
        self.item_dict = item_dict

    async def callback(self, i: Interaction):
        self.view: _view

        async with i.client.pool.acquire() as db:
            async with db.execute(
                "SELECT max FROM todo WHERE item = ?", (self.values[0],)
            ) as c:
                current_amount = await c.fetchone()
                if current_amount is not None:
                    current_amount = current_amount[0]
                    await i.response.send_modal(
                        InputItemAmountModal(
                            self.locale,
                            self.values[0],
                            self.action,
                            current_amount,
                            self.item_dict,
                        )
                    )


class AddItemModal(BaseModal):
    item = TextInput(
        label="item_name",
        placeholder="for_example:_mora",
        max_length=50,
    )

    count = TextInput(label="item_amount", placeholder="for_example:_90", max_length=20)

    def __init__(self, locale: Locale | str) -> None:
        super().__init__(title=text_map.get(203, locale), timeout=config.mid_timeout)
        self.item.label = text_map.get(208, locale)
        self.item.placeholder = text_map.get(209, locale)
        self.count.label = text_map.get(210, locale)
        self.count.placeholder = text_map.get(170, locale).format(a=90)

    async def on_submit(self, i: Interaction) -> None:
        if not self.count.value.isdigit():
            return await return_todo(i)
        item_id = text_map.get_id_from_name(self.item.value.capitalize())
        async with i.client.pool.acquire() as db:
            await db.execute(
                "INSERT INTO todo (user_id, item, count, max) VALUES (?, ?, ?, ?) ON CONFLICT (user_id, item) DO UPDATE SET max = max + ? WHERE item = ? AND user_id = ?",
                (
                    i.user.id,
                    item_id or self.item.value,
                    self.count.value,
                    self.count.value,
                    self.count.value,
                    item_id or self.item.value,
                    i.user.id,
                ),
            )
            await db.commit()
        await return_todo(i)


class InputItemAmountModal(BaseModal):
    count = TextInput(
        label="item_amount",
        placeholder="for_example:_90_(leave_blank_clear)",
        required=False,
        max_length=20,
    )

    def __init__(
        self,
        locale: Locale | str,
        item_name: str,
        action: TodoAction,
        current_amount: int,
        item_dict: Dict[str, str],
    ) -> None:
        super().__init__(
            title=text_map.get(729 if action is TodoAction.EDIT else 205, locale),
            timeout=config.mid_timeout,
        )

        self.item_name = item_name
        self.action = action

        self.count.label = text_map.get(210, locale).format(item=item_dict[item_name])
        self.count.default = str(current_amount)

    async def on_submit(self, i: Interaction) -> None:

        if not self.count.value.isdigit():
            return await return_todo(i)

        async with i.client.pool.acquire() as db:
            if self.action is TodoAction.REMOVE:
                await db.execute(
                    "UPDATE todo SET max = max - ? WHERE item = ? AND user_id = ?",
                    (self.count.value, self.item_name, i.user.id),
                )
                await db.execute("DELETE FROM todo WHERE max = 0")
            elif self.action is TodoAction.EDIT:
                await db.execute(
                    "UPDATE todo SET count = ? WHERE item = ? AND user_id = ?",
                    (self.count.value, self.item_name, i.user.id),
                )
                await db.execute("DELETE FROM todo WHERE count >= max")
            await db.commit()

        await return_todo(i)


async def return_todo(i: Interaction):
    await i.response.defer()

    locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
    todo_items: List[TodoItem] = []
    materials: List[Tuple[Material, int | str]] = []

    async with i.client.pool.acquire() as db:
        async with db.execute(
            "SELECT item, count, max FROM todo WHERE user_id = ? ORDER BY item",
            (i.user.id,),
        ) as c:
            for row in c.get_cursor():
                todo_items.append(TodoItem(name=row[0], current=row[1], max=row[2]))

    view = View(todo_items, locale)
    view.author = i.user

    embed = DefaultEmbed()
    embed.set_author(name=text_map.get(202, locale), icon_url=i.user.display_avatar.url)

    if not todo_items:
        embed.description = text_map.get(204, locale)
        await i.edit_original_response(embed=embed, view=view, attachments=[])
    else:
        dark_mode = await get_user_appearance_mode(i.user.id, i.client.pool)
        client = AmbrTopAPI(i.client.session, to_ambr_top(locale))

        for item in todo_items:
            if item.name.isdigit():
                ambr_material = await client.get_material(int(item.name))
            else:
                item_id = text_map.get_id_from_name(item.name)
                ambr_material = await client.get_material(item_id)
            if isinstance(ambr_material, Material):
                materials.append((ambr_material, f"{item.current}/{item.max}"))
            else:
                materials.append(
                    (
                        Material(
                            id=0,
                            name=item.name,
                            type="custom",
                            icon="https://i.imgur.com/EMfc6o4.png",
                        ),
                        f"{item.current}/{item.max}",
                    )
                )

        fp = await main_funcs.draw_material_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=locale,
                dark_mode=dark_mode,
            ),
            materials[:14],
            "",
            False,
        )
        embed.set_image(url="attachment://todo.jpeg")
        embeds = [embed]

        for _ in range(14, len(todo_items), 14):
            embeds.append(
                DefaultEmbed()
                .set_author(
                    name=text_map.get(202, locale), icon_url=i.user.display_avatar.url
                )
                .set_image(url="attachment://todo.jpeg")
            )

        await TodoPaginator(
            i, embeds, materials, locale, dark_mode, fp, todo_items, view.children
        ).start()
