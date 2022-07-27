__all__ = ['GeneralPaginator']


from discord import Embed, Interaction, SelectOption, User, ButtonStyle
from discord.ui import Select, button, Button, View
from typing import Optional, List, Union

from utility.utils import errEmbed


class _view(View):
    def __init__(self, author: User, pages: List[SelectOption], embeded: bool, check: bool = True):
        super().__init__(timeout=None)
        self.author = author
        self.pages = pages
        self.embeded = embeded
        self.check = check

        self.current_page = 0

    async def interaction_check(self, interaction: Interaction) -> bool:
        if not self.check:
            return True
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(embed=errEmbed('你不是這個指令的使用者'), ephemeral=True)
        return (interaction.user.id == self.author.id)

    async def update_children(self, interaction: Interaction):
        self.next.disabled = (self.current_page + 1 == len(self.pages))
        self.previous.disabled = (self.current_page <= 0)

        kwargs = {'content': self.pages[self.current_page]} if not (
            self.embeded) else {'embed': self.pages[self.current_page]}
        kwargs['view'] = self

        await interaction.response.edit_message(**kwargs)

    @button(emoji="<:double_left:982588991461281833>", style=ButtonStyle.gray, row=1)
    async def first(self, interaction: Interaction, button: Button):
        self.current_page = 0

        await self.update_children(interaction)

    @button(emoji='<:left:982588994778972171>', style=ButtonStyle.blurple, row=1)
    async def previous(self, interaction: Interaction, button: Button):
        self.current_page -= 1

        await self.update_children(interaction)

    @button(emoji="<:right:982588993122238524>", style=ButtonStyle.blurple, row=1)
    async def next(self, interaction: Interaction, button: Button):
        self.current_page += 1

        await self.update_children(interaction)

    @button(emoji='<:double_right:982588990223958047>', style=ButtonStyle.gray, row=1)
    async def last(self, interaction: Interaction, button: Button):
        self.current_page = len(self.pages) - 1

        await self.update_children(interaction)


class GeneralPaginator:
    def __init__(self, interaction: Interaction, pages: list, custom_children: Optional[List[Union[Button, Select]]] = []):
        self.custom_children = custom_children
        self.interaction = interaction
        self.pages = pages

    async def start(self, embeded: Optional[bool] = False, edit_original_message: bool = False, follow_up: bool = False, check: bool = True, ephemeral: bool = False) -> None:
        if not (self.pages):
            raise ValueError("Missing pages")

        view = _view(self.interaction.user, self.pages, embeded, check)

        view.previous.disabled = True if (view.current_page <= 0) else False
        view.next.disabled = True if (
            view.current_page + 1 >= len(self.pages)) else False

        if (len(self.custom_children) > 0):
            for child in self.custom_children:
                view.add_item(child)

        kwargs = {'content': self.pages[view.current_page]} if not (
            embeded) else {'embed': self.pages[view.current_page]}
        kwargs['view'] = view
        kwargs['ephemeral'] = ephemeral

        if edit_original_message:
            await self.interaction.edit_original_message(**kwargs)
        elif follow_up:
            await self.interaction.followup.send(**kwargs)
        else:
            await self.interaction.response.send_message(**kwargs)

        await view.wait()

        # await self.interaction.delete_original_message()
