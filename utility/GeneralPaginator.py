__all__ = ['GeneralPaginator']


from discord import Interaction, SelectOption, User, ButtonStyle
from discord.ui import View, Select, button, Button
from typing import Optional, List, Union


class _select(Select):
	def __init__(self, pages: List[str]):
		super().__init__(placeholder="Quick navigation", min_values=1, max_values=1, options=pages, row=0)


	async def callback(self, interaction: Interaction):
		self.view.current_page = int(self.values[0])

		await self.view.update_children(interaction)


class _view(View):
	def __init__(self, author: User, pages: List[SelectOption], embeded: bool):
		super().__init__()
		self.author = author
		self.pages = pages
		self.embeded = embeded

		self.current_page = 0

	async def interaction_check(self, interaction: Interaction) -> bool:
		return (interaction.user.id == self.author.id)


	async def update_children(self, interaction: Interaction):
		self.next.disabled = (self.current_page + 1 == len(self.pages))
		self.previous.disabled = (self.current_page <= 0)

		kwargs = {'content': self.pages[self.current_page]} if not (self.embeded) else {'embed': self.pages[self.current_page]}
		kwargs['view'] = self

		await interaction.response.edit_message(**kwargs)


	@button(label="◀◀", style=ButtonStyle.gray, row=1)
	async def first(self, interaction: Interaction, button: Button):
		self.current_page = 0

		await self.update_children(interaction)

	@button(label="◀", style=ButtonStyle.blurple, row=1)
	async def previous(self, interaction: Interaction, button: Button):
		self.current_page -= 1

		await self.update_children(interaction)

	@button(label="▶", style=ButtonStyle.blurple, row=1)
	async def next(self, interaction: Interaction, button: Button):
		self.current_page += 1

		await self.update_children(interaction)

	@button(label="▶▶", style=ButtonStyle.gray, row=1)
	async def last(self, interaction: Interaction, button: Button):
		self.current_page = len(self.pages) - 1

		await self.update_children(interaction)


class GeneralPaginator:
	def __init__(self, interaction: Interaction, pages: list, custom_children: Optional[List[Union[Button, Select]]] = []):
		self.custom_children = custom_children
		self.interaction = interaction
		self.pages = pages


	async def start(self, embeded: Optional[bool] = False, quick_navigation: bool = True) -> None:
		if not (self.pages): raise ValueError("Missing pages")

		view = _view(self.interaction.user, self.pages, embeded)

		view.previous.disabled = True if (view.current_page <= 0) else False
		view.next.disabled = True if (view.current_page + 1 >= len(self.pages)) else False

		if (quick_navigation):
			options = []
			for index, page in enumerate(self.pages):
				options.append(SelectOption(label=f"Page {index+1}", value=index))

		if (len(self.custom_children) > 0):
			for child in self.custom_children:
				view.add_item(child)

		kwargs = {'content': self.pages[view.current_page]} if not (embeded) else {'embed': self.pages[view.current_page]}
		kwargs['view'] = view

		await self.interaction.response.send_message(**kwargs)

		await view.wait()
		
		await self.interaction.delete_original_message()