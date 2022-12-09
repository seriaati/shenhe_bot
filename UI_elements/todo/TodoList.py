from typing import List, Tuple
from ambr.client import AmbrTopAPI
from ambr.models import Material
from apps.text_map.convert_locale import to_ambr_top
from discord import ButtonStyle, Interaction, Locale, SelectOption
from discord.ui import Button, TextInput, Select
from apps.draw import main_funcs
import asset
import config
from apps.genshin.custom_model import DrawInput, TodoItem
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseModal, BaseView
from utility.todo_paginator import TodoPaginator, _view
from utility.utils import (
    default_embed,
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
        self.add_item(RemoveItem(not todo_items, text_map.get(205, locale)))
        self.add_item(ClearItems(not todo_items, text_map.get(206, locale)))


class AddItem(Button):
    def __init__(self, label: str):
        super().__init__(
            label=label, style=ButtonStyle.green, row=2, emoji=asset.add_emoji
        )

    async def callback(self, i: Interaction):
        locale = await get_user_locale(i.user.id, i.client.db) or i.locale
        await i.response.send_modal(AddItemModal(locale))


class RemoveItem(Button):
    def __init__(self, disabled: bool, label: str):
        super().__init__(
            label=label,
            style=ButtonStyle.red,
            disabled=disabled,
            row=2,
            emoji=asset.remove_emoji,
        )

    async def callback(self, i: Interaction):
        self.view: _view
        self.view.clear_items()
        self.view.add_item(
            ItemSelect(
                self.view.locale,
                self.view.todo_items[
                    self.view.current_page * 14 : (self.view.current_page + 1) * 14
                ],
            )
        )
        await i.response.edit_message(view=self.view)


class ItemSelect(Select):
    def __init__(self, locale: Locale | str, todo_items: List[TodoItem]):
        options = []
        for todo_item in todo_items:
            if todo_item.name.isdigit():
                item_label = text_map.get_material_name(int(todo_item.name), locale)
                if isinstance(item_label, int):
                    item_label = todo_item.name
            else:
                item_label = todo_item.name
            options.append(SelectOption(label=item_label, value=todo_item.name))
        super().__init__(
            placeholder=text_map.get(207, locale),
            options=options,
        )
        self.locale = locale

    async def callback(self, i: Interaction):
        await i.response.send_modal(RemoveItemModal(self.locale, self.values[0]))


class ClearItems(Button):
    def __init__(self, disabled: bool, label: str):
        super().__init__(label=label, disabled=disabled, row=2, emoji=asset.clear_emoji)

    async def callback(self, i: Interaction):
        await i.client.db.execute("DELETE FROM todo WHERE user_id = ?", (i.user.id,))
        await i.client.db.commit()
        await return_todo(i)


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
        await i.client.db.execute(
            "INSERT INTO todo VALUES (?, ?, ?) ON CONFLICT (user_id, item) DO UPDATE SET count = count + ? WHERE item = ? AND user_id = ?",
            (
                i.user.id,
                item_id or self.item.value,
                self.count.value,
                self.count.value,
                item_id or self.item.value,
                i.user.id,
            ),
        )
        await i.client.db.commit()
        await return_todo(i)


class RemoveItemModal(BaseModal):
    count = TextInput(
        label="item_amount",
        placeholder="for_example:_90_(leave_blank_clear)",
        required=False,
        max_length=20,
    )

    def __init__(self, locale: Locale | str, item_name: str) -> None:
        super().__init__(title=text_map.get(205, locale), timeout=config.mid_timeout)
        self.item_name = item_name
        self.count.label = text_map.get(210, locale)
        self.count.placeholder = text_map.get(211, locale)

    async def on_submit(self, i: Interaction) -> None:
        if self.count.value:
            if not self.count.value.isdigit():
                return await return_todo(i)
            await i.client.db.execute(
                "UPDATE todo SET count = count - ? WHERE item = ? AND user_id = ?",
                (self.count.value, self.item_name, i.user.id),
            )
            await i.client.db.execute("DELETE FROM todo WHERE count <= 0")
        else:
            await i.client.db.execute(
                "DELETE FROM todo WHERE item = ? AND user_id = ?",
                (self.item_name, i.user.id),
            )
        await i.client.db.commit()
        await return_todo(i)


async def return_todo(i: Interaction):
    await i.response.defer()

    locale = await get_user_locale(i.user.id, i.client.db) or i.locale
    todo_items: List[TodoItem] = []
    materials: List[Tuple[Material, int | str]] = []

    async with i.client.db.execute(
        "SELECT item, count FROM todo WHERE user_id = ? ORDER BY count DESC",
        (i.user.id,),
    ) as c:
        async for row in c:
            todo_items.append(TodoItem(name=row[0], count=row[1]))

    view = View(todo_items, locale)
    view.author = i.user

    embed = default_embed()
    embed.set_author(name=text_map.get(202, locale), icon_url=i.user.display_avatar.url)

    if not todo_items:
        embed.description = text_map.get(204, locale)
        await i.edit_original_response(embed=embed, view=view, attachments=[])
    else:
        dark_mode = await get_user_appearance_mode(i.user.id, i.client.db)
        client = AmbrTopAPI(i.client.session, to_ambr_top(locale))

        for item in todo_items:
            if item.name.isdigit():
                ambr_material = await client.get_material(int(item.name))
            else:
                item_id = text_map.get_id_from_name(item.name)
                ambr_material = await client.get_material(item_id)
            if isinstance(ambr_material, Material):
                materials.append((ambr_material, item.count))
            else:
                materials.append(
                    (
                        Material(
                            id=0,
                            name=item.name,
                            type="custom",
                            icon="https://i.imgur.com/EMfc6o4.png",
                        ),
                        item.count,
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
        embed.set_footer(
            text=text_map.get(176, locale).format(num=f"1/{len(todo_items)//14+1}")
        )
        embeds = [embed]

        for _ in range(14, len(todo_items), 14):
            embeds.append(
                default_embed()
                .set_author(
                    name=text_map.get(202, locale), icon_url=i.user.display_avatar.url
                )
                .set_image(url="attachment://todo.jpeg")
                .set_footer(
                    text=text_map.get(176, locale).format(
                        num=f"{_+1//14+1}/{len(todo_items)//14+1}"
                    )
                )
            )

        await TodoPaginator(
            i, embeds, materials, locale, dark_mode, fp, todo_items, view.children
        ).start()
