from typing import List, Optional, Union

import discord
from discord import ui

import config
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseView


class _view(BaseView):
    def __init__(
        self,
        embeds: List[discord.Embed],
        locale: str,
    ):
        self.embeds = embeds
        self.locale = locale

        self.current_page = 0

        super().__init__(timeout=config.mid_timeout)

    async def update_children(self, i: discord.Interaction):
        self.first.disabled = self.current_page == 0
        self.next.disabled = self.current_page + 1 == len(self.embeds)
        self.previous.disabled = self.current_page <= 0
        self.last.disabled = self.current_page + 1 == len(self.embeds)

        text = text_map.get(176, self.locale)
        self.page.label = text.format(num=f"{self.current_page + 1}/{len(self.embeds)}")

        await i.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @ui.button(
        emoji="<:double_left:982588991461281833>",
        style=discord.ButtonStyle.gray,
        row=1,
        custom_id="paginator_double_left",
    )
    async def first(self, i: discord.Interaction, button: ui.Button):
        self.current_page = 0

        await self.update_children(i)

    @ui.button(
        emoji="<:left:982588994778972171>",
        style=discord.ButtonStyle.blurple,
        row=1,
        custom_id="paginator_left",
    )
    async def previous(self, i: discord.Interaction, button: ui.Button):
        self.current_page -= 1

        await self.update_children(i)

    @ui.button(
        label="page 1/1",
        custom_id="paginator_page",
        disabled=True,
        row=1,
    )
    async def page(self, i: discord.Interaction, button: ui.Button):
        pass

    @ui.button(
        emoji="<:right:982588993122238524>",
        style=discord.ButtonStyle.blurple,
        row=1,
        custom_id="paginator_right",
    )
    async def next(self, i: discord.Interaction, button: ui.Button):
        self.current_page += 1

        await self.update_children(i)

    @ui.button(
        emoji="<:double_right:982588990223958047>",
        style=discord.ButtonStyle.gray,
        row=1,
        custom_id="paginator_double_right",
    )
    async def last(self, i: discord.Interaction, button: ui.Button):
        self.current_page = len(self.embeds) - 1

        await self.update_children(i)


class GeneralPaginator:
    def __init__(
        self,
        i: discord.Interaction,
        embeds: List[discord.Embed],
        custom_children: List[Union[ui.Button, ui.Select]] = None,
    ):
        if custom_children is None:
            custom_children = []
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

        locale = (
            await get_user_locale(self.i.user.id, self.i.client.pool) or self.i.locale
        )
        view = _view(self.embeds, str(locale))
        view.author = self.i.user
        view.first.disabled = view.previous.disabled = True
        view.last.disabled = view.next.disabled = (
            True if len(self.embeds) == 1 else False
        )

        view.page.label = text_map.get(176, locale).format(
            num=f"{view.current_page + 1}/{len(self.embeds)}"
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
