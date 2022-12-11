from typing import List, Union

from discord import ButtonStyle, Embed, Interaction
from discord.ui import Button, Select, button

import config
from UI_base_models import BaseView


class _view(BaseView):
    def __init__(
        self,
        embeds: List[Embed],
    ):
        super().__init__(timeout=config.mid_timeout)
        self.embeds = embeds
        self.current_page = 0
        self.rarity_filters = []
        self.banner_filters = []

    async def update_children(self, i: Interaction):
        self.first.disabled = self.current_page == 0
        self.next.disabled = self.current_page + 1 == len(self.embeds)
        self.previous.disabled = self.current_page <= 0
        self.last.disabled = self.current_page + 1 == len(self.embeds)

        await i.response.edit_message(embed=self.embeds[self.current_page], view=self)

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


class WishPaginator:
    def __init__(
        self,
        i: Interaction,
        embeds: List[Embed],
        custom_children: List[Union[Button, Select]] = [],
    ):
        self.i = i
        self.embeds = embeds
        self.custom_children = custom_children

    async def start(
        self,
        edit: bool = False,
        followup: bool = False,
        ephemeral: bool = False,
    ) -> None:
        if not (self.embeds):
            raise ValueError("Missing embeds")

        view = _view(self.embeds)
        view.author = self.i.user
        view.first.disabled = view.previous.disabled = True
        view.last.disabled = view.next.disabled = (
            True if len(self.embeds) == 1 else False
        )

        if len(self.custom_children) > 0:
            for child in self.custom_children:
                view.add_item(child)

        kwargs = {}
        kwargs["embed"] = self.embeds[0]
        kwargs["view"] = view
        if ephemeral:
            kwargs["ephemeral"] = ephemeral

        if edit and ephemeral:
            raise ValueError("Cannot edit the ephemeral status of a message")

        if edit:
            await self.i.edit_original_response(**kwargs)
        elif followup:
            await self.i.followup.send(**kwargs)
        else:
            await self.i.response.send_message(**kwargs)

        view.message = await self.i.original_response()
        await view.wait()
