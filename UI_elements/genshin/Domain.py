from typing import List

from discord import Interaction, Locale, SelectOption, ui

from apps.genshin.utils import get_farm_data
from apps.text_map.text_map_app import text_map
from utility.utils import divide_chunks
from utility.paginator import _view


class DomainSelect(ui.Select):
    def __init__(self, placeholder: str, options: List[SelectOption], row: int):
        super().__init__(options=options, placeholder=placeholder, row=row)

    async def callback(self, i: Interaction):
        self.view: _view
        self.view.current_page = int(self.values[0])
        await self.view.update_children(i)


class WeekDaySelect(ui.Select):
    def __init__(self, placeholder: str, locale: Locale | str):
        options = []
        for index in range(0, 7):
            weekday_text = text_map.get(234 + index, locale)
            options.append(SelectOption(label=weekday_text, value=str(index)))

        self.locale = locale
        super().__init__(options=options, placeholder=placeholder, row=4)

    async def callback(self, i: Interaction):
        self.view: _view
        result, embeds, options = await get_farm_data(i, int(self.values[0]))
        self.view.domains = result # type: ignore
        self.view.embeds = embeds
        first = 1
        row = 2
        options = list(divide_chunks(options, 25))
        children = []
        for option in options:
            children.append(
                DomainSelect(
                    f"{text_map.get(325, self.locale)} ({first}~{first+len(option)})",
                    option,
                    row,
                )
            )
            first += 25
            row += 1
        children.append(self)
        for child in self.view.children:
            if isinstance(child, DomainSelect) or isinstance(child, WeekDaySelect):
                self.view.remove_item(child)
        for child in children:
            self.view.add_item(child)
        self.view.current_page = 0
        await self.view.update_children(i)
