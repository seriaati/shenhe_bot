import io

from discord import Interaction, SelectOption, Embed, File
from discord.ui import Select

import config
from UI_base_models import BaseView
from typing import List


class View(BaseView):
    def __init__(self, embeds: List[Embed], options: List[SelectOption], placeholder: str, file: io.BytesIO):
        super().__init__(timeout=config.long_timeout)
        self.add_item(QuickNavigation(options, placeholder, file))
        self.embeds = embeds
        
class QuickNavigation(Select):
    def __init__(self, options: List[SelectOption], placeholder: str, file: io.BytesIO):
        super().__init__(placeholder=placeholder, options=options)
        self.file = file

    async def callback(self, i: Interaction):
        self.view: View
        if self.values[0] == "1":
            fp = self.file
            fp.seek(0)
            file = File(fp, filename="ascension.jpeg")
            await i.response.edit_message(embed=self.view.embeds[1], attachments=[file])
        else:
            await i.response.edit_message(embed=self.view.embeds[int(self.values[0])], attachments=[])
