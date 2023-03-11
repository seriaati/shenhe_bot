import io
from typing import List, Tuple, Union

from discord import ButtonStyle, Embed, File, Interaction, Locale
from discord.ui import Button, Select, button

import config
from ambr.models import Material
from apps.draw import main_funcs
from apps.genshin.custom_model import DrawInput, TodoItem
from UI_base_models import BaseView
from apps.text_map.text_map_app import text_map


class _view(BaseView):
    def __init__(
        self,
        embeds: List[Embed],
        materials: List[Tuple[Material, int | str]],
        locale: Locale | str,
        dark_mode: bool,
        todo_items: List[TodoItem],
    ):
        super().__init__(timeout=config.mid_timeout)
        self.embeds = embeds
        self.materials = materials
        self.locale = locale
        self.dark_mode = dark_mode
        self.todo_items = todo_items
        self.current_page = 0

    async def update_children(self, i: Interaction):
        self.first.disabled = self.current_page == 0
        self.next.disabled = self.current_page + 1 == len(self.embeds)
        self.previous.disabled = self.current_page <= 0
        self.last.disabled = self.current_page + 1 == len(self.embeds)

        text = text_map.get(176, self.locale)
        self.page.label = text.format(num=f"{self.current_page + 1}/{len(self.embeds)}")

        fp = await main_funcs.draw_material_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=self.locale,
                dark_mode=self.dark_mode,
            ),
            self.materials[self.current_page * 14 : (self.current_page + 1) * 14],
            "",
            False,
        )
        fp.seek(0)
        file = File(fp, filename="todo.jpeg")

        await i.response.edit_message(
            embed=self.embeds[self.current_page], view=self, attachments=[file]
        )

    @button(
        emoji="<:double_left:982588991461281833>",
        style=ButtonStyle.gray,
        row=1,
        custom_id="paginator_double_left",
    )
    async def first(self, i: Interaction, button: Button):
        self.current_page = 0

        await self.update_children(i)

    @button(
        emoji="<:left:982588994778972171>",
        style=ButtonStyle.blurple,
        row=1,
        custom_id="paginator_left",
    )
    async def previous(self, i: Interaction, button: Button):
        self.current_page -= 1

        await self.update_children(i)

    @button(
        label="page 1/1",
        custom_id="paginator_page",
        row=1,
        disabled=True,
    )
    async def page(self, i: Interaction, button: Button):
        pass

    @button(
        emoji="<:right:982588993122238524>",
        style=ButtonStyle.blurple,
        row=1,
        custom_id="paginator_right",
    )
    async def next(self, i: Interaction, button: Button):
        self.current_page += 1

        await self.update_children(i)

    @button(
        emoji="<:double_right:982588990223958047>",
        style=ButtonStyle.gray,
        row=1,
        custom_id="paginator_double_right",
    )
    async def last(self, i: Interaction, button: Button):
        self.current_page = len(self.embeds) - 1

        await self.update_children(i)


class TodoPaginator:
    def __init__(
        self,
        i: Interaction,
        embeds: List[Embed],
        materials: List[Tuple[Material, int | str]],
        locale: Locale | str,
        dark_mode: bool,
        first_fp: io.BytesIO,
        todo_items: List[TodoItem],
        custom_children: List[Union[Button, Select]] = None,
    ):
        if custom_children is None:
            custom_children = []
        self.i = i
        self.embeds = embeds
        self.custom_children = custom_children
        self.materials = materials
        self.locale = locale
        self.dark_mode = dark_mode
        self.first_fp = first_fp
        self.todo_items = todo_items

    async def start(
        self,
    ) -> None:
        if not (self.embeds):
            raise ValueError("Missing embeds")

        view = _view(
            self.embeds, self.materials, self.locale, self.dark_mode, self.todo_items
        )
        view.author = self.i.user
        view.first.disabled = view.previous.disabled = True
        view.last.disabled = view.next.disabled = len(self.embeds) == 1
        view.page.label = text_map.get(176, self.locale).format(
            num=f"1/{len(self.embeds)}"
        )

        if len(self.custom_children) > 0:
            for child in self.custom_children:
                view.add_item(child)

        self.first_fp.seek(0)
        await self.i.edit_original_response(
            embed=self.embeds[0],
            view=view,
            attachments=[File(self.first_fp, filename="todo.jpeg")],
        )

        view.message = await self.i.original_response()
        await view.wait()
