from typing import Dict, List, Tuple

import asyncpg
from discord import ButtonStyle, Locale, SelectOption
from discord.ui import Button, Select, TextInput

import asset
import config
from ambr.client import AmbrTopAPI
from ambr.models import Material
from apps.draw import main_funcs
import apps.genshin.custom_model as custom_model
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from base_ui import BaseModal, BaseView
from utility.todo_paginator import TodoPaginator, TodoPaginatorView
from utility.utils import DefaultEmbed, get_user_appearance_mode


class View(BaseView):
    def __init__(
        self,
        todo_items: List[custom_model.TodoItem],
        locale: Locale | str,
    ):
        super().__init__(timeout=config.long_timeout)
        self.todo_items = todo_items
        self.locale = locale
        self.add_item(AddItem(text_map.get(203, locale)))
        self.add_item(
            EditOrRemove(
                not todo_items, text_map.get(729, locale), custom_model.TodoAction.EDIT
            )
        )
        self.add_item(
            EditOrRemove(
                not todo_items,
                text_map.get(205, locale),
                custom_model.TodoAction.REMOVE,
            )
        )
        self.add_item(ClearItems(not todo_items, text_map.get(206, locale)))


class AddItem(Button):
    def __init__(self, label: str):
        super().__init__(
            label=label, style=ButtonStyle.green, row=2, emoji=asset.add_emoji
        )

    @staticmethod
    async def callback(i: custom_model.CustomInteraction):
        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
        await i.response.send_modal(AddItemModal(locale))


class EditOrRemove(Button):
    def __init__(self, disabled: bool, label: str, action: custom_model.TodoAction):
        super().__init__(
            label=label,
            style=ButtonStyle.primary
            if action is custom_model.TodoAction.EDIT
            else ButtonStyle.red,
            disabled=disabled,
            row=2 if action is custom_model.TodoAction.EDIT else 3,
            emoji=asset.edit_emoji
            if action is custom_model.TodoAction.EDIT
            else asset.remove_emoji,
        )

        self.action = action

    async def callback(self, i: custom_model.CustomInteraction):
        self.view: TodoPaginatorView
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

    @staticmethod
    async def callback(i: custom_model.CustomInteraction):
        pool: asyncpg.Pool = i.client.pool  # type: ignore
        await pool.execute("DELETE FROM todo WHERE user_id = $1", i.user.id)
        await return_todo(i)


class ItemSelect(Select):
    def __init__(
        self,
        locale: Locale | str,
        todo_items: List[custom_model.TodoItem],
        action: custom_model.TodoAction,
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

    async def callback(self, i: custom_model.CustomInteraction):
        self.view: TodoPaginatorView
        pool: asyncpg.Pool = i.client.pool  # type: ignore

        row = await pool.fetchrow(
            "SELECT count, max FROM todo WHERE item = $1", self.values[0]
        )
        await i.response.send_modal(
            InputItemAmountModal(
                self.locale,
                self.values[0],
                self.action,
                row["count"],
                row["max"],
                self.item_dict,
            )
        )


class AddItemModal(BaseModal):
    item = TextInput(
        label="item_name",
        placeholder="for_example:_mora",
        max_length=50,
    )

    count = TextInput(label="item_amount", placeholder="for_example:_90", max_length=10)

    def __init__(self, locale: Locale | str) -> None:
        super().__init__(title=text_map.get(203, locale), timeout=config.mid_timeout)
        self.item.label = text_map.get(208, locale)
        self.item.placeholder = text_map.get(209, locale)
        self.count.label = text_map.get(308, locale)
        self.count.placeholder = text_map.get(170, locale).format(a=90)

    async def on_submit(self, i: custom_model.CustomInteraction) -> None:
        pool: asyncpg.Pool = i.client.pool  # type: ignore

        if not self.count.value.isdigit():
            return await return_todo(i)
        item_id = text_map.get_id_from_name(self.item.value.capitalize())

        await pool.execute(
            """
            INSERT INTO todo (user_id, item, max)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, item)
            DO UPDATE SET max = todo.max + $3
            """,
            i.user.id,
            str(item_id) if item_id else self.item.value,
            int(self.count.value),
        )
        await return_todo(i)


class InputItemAmountModal(BaseModal):
    count = TextInput(
        label="item_amount",
        max_length=10,
    )

    def __init__(
        self,
        locale: Locale | str,
        item_name: str,
        action: custom_model.TodoAction,
        current_amount: int,
        max_amount: int,
        item_dict: Dict[str, str],
    ) -> None:
        super().__init__(
            title=text_map.get(
                729 if action is custom_model.TodoAction.EDIT else 205, locale
            ),
            timeout=config.mid_timeout,
        )

        self.item_name = item_name
        self.action = action

        self.count.label = text_map.get(210, locale).format(item=item_dict[item_name])
        self.count.default = (
            str(current_amount)
            if action is custom_model.TodoAction.EDIT
            else str(max_amount)
        )

    async def on_submit(self, i: custom_model.CustomInteraction) -> None:
        pool: asyncpg.Pool = i.client.pool  # type: ignore

        if not self.count.value.isdigit():
            return await return_todo(i)

        if self.action is custom_model.TodoAction.EDIT:
            await pool.execute(
                "UPDATE todo SET count = $1 WHERE item = $2 AND user_id = $3",
                int(self.count.value),
                self.item_name,
                i.user.id,
            )
        elif self.action is custom_model.TodoAction.REMOVE:
            await pool.execute(
                "UPDATE todo SET max = max - $1 WHERE item = $2 AND user_id = $3",
                int(self.count.value),
                self.item_name,
                i.user.id,
            )
        await pool.execute("DELETE FROM todo WHERE count >= max OR max = 0")

        await return_todo(i)


async def return_todo(i: custom_model.CustomInteraction):
    await i.response.defer()

    locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
    todo_items: List[custom_model.TodoItem] = []
    materials: List[Tuple[Material, int | str]] = []

    pool: asyncpg.Pool = i.client.pool  # type: ignore
    rows = await pool.fetch(
        "SELECT item, count, max FROM todo WHERE user_id = $1 ORDER BY item",
        i.user.id,
    )
    for row in rows:
        todo_items.append(
            custom_model.TodoItem(
                name=row["item"], current=row["count"], max=row["max"]
            )
        )

    view = View(todo_items, locale)
    view.author = i.user

    embed = DefaultEmbed()
    embed.set_author(name=text_map.get(202, locale), icon_url=i.user.display_avatar.url)

    if not todo_items:
        embed.description = text_map.get(204, locale)
        view.message = await i.edit_original_response(
            embed=embed, view=view, attachments=[]
        )
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
            custom_model.DrawInput(
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
            i, embeds, materials, dark_mode, fp, todo_items, view.children
        ).start(edit=True)
