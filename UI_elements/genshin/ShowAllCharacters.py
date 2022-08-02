from discord.ui import Select 
from discord import Interaction, SelectOption
from typing import Any

class ElementSelect(Select):
    def __init__(self, options: list[SelectOption], placeholder: str):
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, i: Interaction) -> Any:
        self.view.current_page = int(self.values[0])
        await self.view.update_children(i)