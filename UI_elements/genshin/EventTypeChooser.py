from discord.ui import Select
from discord import Interaction, Embed, SelectOption, Locale
from typing import Any, Dict, List
from apps.text_map.text_map_app import text_map
    
class Select(Select):
    def __init__(self, options: List[SelectOption], embeds: Dict[int, List[Embed]], locale: Locale, user_locale: str | None) -> None:
        super().__init__(options=options, placeholder=text_map.get(409, locale, user_locale))
        self.embeds = embeds
        
    async def callback(self, i: Interaction) -> Any:
        self.view.current_page = 0
        self.view.embeds = self.embeds[self.values[0]]
        await i.response.edit_message(embed=self.view.embeds[0], view=self.view)