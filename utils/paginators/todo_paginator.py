import io
from typing import Any, Dict, List, Optional, Tuple, Union

from discord import Embed, File, Locale
from discord.ui import Button, Select

from ambr import Material
from apps.draw import main_funcs
from dev.models import DrawInput, Inter, TodoItem

from .paginator import GeneralPaginator, GeneralPaginatorView


class TodoPaginatorView(GeneralPaginatorView):
    def __init__(
        self,
        embeds: List[Embed],
        materials: List[Tuple[Material, int | str]],
        lang: Locale | str,
        dark_mode: bool,
        todo_items: List[TodoItem],
    ) -> None:
        super().__init__(embeds, str(lang))
        self.materials = materials
        self.dark_mode = dark_mode
        self.todo_items = todo_items

    async def make_response(self, i: Inter) -> None:
        fp = await main_funcs.draw_material_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                lang=self.lang,
                dark_mode=self.dark_mode,
            ),
            self.materials[self.current_page * 14 : (self.current_page + 1) * 14],
            "",
            False,
        )
        fp.seek(0)
        file_ = File(fp, filename="todo.jpeg")

        await i.response.edit_message(
            embed=self.embeds[self.current_page], view=self, attachments=[file_]
        )


class TodoPaginator(GeneralPaginator):
    def __init__(
        self,
        i: Inter,
        embeds: List[Embed],
        materials: List[Tuple[Material, int | str]],
        dark_mode: bool,
        first_fp: io.BytesIO,
        todo_items: List[TodoItem],
        custom_children: Optional[List[Union[Button, Select]]] = None,
    ):
        super().__init__(
            i=i,
            embeds=embeds,
            custom_children=custom_children,
        )

        self.materials = materials
        self.todo_items = todo_items
        self.dark_mode = dark_mode
        self.first_fp = first_fp

    def setup_view(self, lang: Locale | str) -> TodoPaginatorView:
        view = TodoPaginatorView(
            self.embeds, self.materials, lang, self.dark_mode, self.todo_items
        )
        return view

    def setup_kwargs(self, view: TodoPaginatorView) -> Dict[str, Any]:
        kwargs = super().setup_kwargs(view)

        self.first_fp.seek(0)
        kwargs["attachments"] = [File(self.first_fp, filename="todo.jpeg")]
        return kwargs
