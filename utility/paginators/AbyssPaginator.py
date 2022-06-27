__all__ = ['AbyssPaginator']


from typing import List, Optional, Union

from discord import Interaction, SelectOption, User
from discord.ui import Button, Select, View

from utility.utils import errEmbed


class _select(Select):
    def __init__(self, pages: List[str]):
        super().__init__(placeholder="樓層導覽", min_values=1, max_values=1, options=pages, row=0)


    async def callback(self, interaction: Interaction):
        self.view.current_page = int(self.values[0])

        await self.view.update_children(interaction)


class _view(View):
    def __init__(self, author: User, pages: List[SelectOption], embeded: bool):
        super().__init__(timeout=None)
        self.author = author
        self.pages = pages
        self.embeded = embeded

        self.current_page = 0

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(embed=errEmbed('你不是這個指令的使用者'), ephemeral=True)
        return (interaction.user.id == self.author.id)


    async def update_children(self, interaction: Interaction):
        kwargs = {'content': self.pages[self.current_page]} if not (self.embeded) else {'embed': self.pages[self.current_page]}
        kwargs['view'] = self

        await interaction.response.edit_message(**kwargs)

class AbyssPaginator:
    def __init__(self, interaction: Interaction, pages: list, custom_children: Optional[List[Union[Button, Select]]] = []):
        self.custom_children = custom_children
        self.interaction = interaction
        self.pages = pages


    async def start(self, embeded: Optional[bool] = False, quick_navigation: bool = True) -> None:
        if not (self.pages): raise ValueError("Missing pages")

        view = _view(self.interaction.user, self.pages, embeded)
        if (quick_navigation):
            options = []
            for index, page in enumerate(self.pages):
                options.append(SelectOption(label=f"第{index+9}層", value=index))

            view.add_item(_select(options))

        kwargs = {'content': self.pages[view.current_page]} if not (embeded) else {'embed': self.pages[view.current_page]}
        kwargs['view'] = view

        await self.interaction.response.send_message(**kwargs)

        await view.wait()
        
        await self.interaction.delete_original_message()
