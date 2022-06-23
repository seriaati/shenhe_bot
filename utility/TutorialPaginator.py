__all__ = ['TutorialPaginator']


import aiosqlite
from discord import Interaction, SelectOption, User, ButtonStyle
from discord.ui import Select, button, Button, View
from typing import Optional, List, Union

from utility.utils import errEmbed


class _view(View):
    def __init__(self, author: User, pages: List[SelectOption], embeded: bool, db: aiosqlite.Connection):
        super().__init__()
        self.author = author
        self.pages = pages
        self.embeded = embeded
        self.db = db
        self.current_page = 0

    async def interaction_check(self, interaction: Interaction) -> bool:
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

    @button(label="上一頁", style=ButtonStyle.blurple, row=1)
    async def previous(self, interaction: Interaction, button: Button):
        self.current_page -= 1

        await self.update_children(interaction)

    @button(label="下一頁", style=ButtonStyle.blurple, row=1)
    async def next(self, interaction: Interaction, button: Button):
        c = await self.db.cursor()
        await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (interaction.user.id,))
        uid = await c.fetchone()
        if uid is None:
            await interaction.response.send_message(embed=errEmbed('你似乎還沒有設定UID!', '要設定之後才可以繼續進行哦\n如果因為是亞服UID而沒辦法設定的話, 很抱歉, 可能沒辦法讓你入群了\n設置上有問題嗎? 點上面的小雪頭像來私訊她'), ephemeral=True)
        else:
            self.current_page += 1
            if self.current_page == 1:
                role = interaction.guild.get_role(978626192301236297) # step 1 夢工廠
                await interaction.user.add_roles(role)
            elif self.current_page == 3:
                role = interaction.guild.get_role(978626843517288468) # step 2 身份台
                await interaction.user.add_roles(role)
            elif self.current_page == 5:
                role = interaction.guild.get_role(978532779098796042) # 旅行者
                await interaction.user.add_roles(role)
            await self.update_children(interaction)


class TutorialPaginator:
    def __init__(self, interaction: Interaction, pages: list, custom_children: Optional[List[Union[Button, Select]]] = []):
        self.custom_children = custom_children
        self.interaction = interaction
        self.pages = pages

    async def start(self, db: aiosqlite.Connection, embeded: Optional[bool] = False, quick_navigation: bool = True) -> None:
        if not (self.pages):
            raise ValueError("Missing pages")

        view = _view(self.interaction.user, self.pages, embeded, db)

        view.previous.disabled = True if (view.current_page <= 0) else False
        view.next.disabled = True if (
            view.current_page + 1 >= len(self.pages)) else False

        if (len(self.custom_children) > 0):
            for child in self.custom_children:
                view.add_item(child)

        kwargs = {'content': self.pages[view.current_page]} if not (
            embeded) else {'embed': self.pages[view.current_page]}
        kwargs['view'] = view

        await self.interaction.response.edit_message(**kwargs)
