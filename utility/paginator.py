import io
from typing import Any, Dict, List, Optional, Union

import discord
from discord import ui

import dev.config as config
from apps.db import get_user_lang
from apps.text_map import text_map
from dev.base_ui import BaseView
from dev.models import Inter


class GeneralPaginatorView(BaseView):
    def __init__(
        self,
        embeds: List[discord.Embed],
        locale: str,
        fps: Optional[Dict[str, io.BytesIO]] = None,
    ):
        self.embeds = embeds
        self.locale = locale
        self.files = fps

        self.current_page = 0

        super().__init__(timeout=config.mid_timeout)

    async def update_children(self, i: discord.Interaction):
        """Called when a button is pressed"""
        self.update_components()
        await self.make_response(i)

    def update_components(self):
        """Update the buttons and the page label"""
        self.first.disabled = self.current_page == 0
        self.next.disabled = self.current_page + 1 == len(self.embeds)
        self.previous.disabled = self.current_page <= 0
        self.last.disabled = self.current_page + 1 == len(self.embeds)

        text = text_map.get(176, self.locale)
        self.page.label = text.format(num=f"{self.current_page + 1}/{len(self.embeds)}")

    async def make_response(self, i: discord.Interaction):
        """Make the response for the interaction"""
        embed = self.embeds[self.current_page]
        if self.files is None:
            files = []
        else:
            url = embed.image.url
            if url is None:
                raise ValueError("Missing image url")
            fp = self.files.get(url)
            if fp is None:
                raise ValueError("Missing fp")
            fp.seek(0)
            files = [discord.File(fp, filename=url)]

        await i.response.edit_message(embed=embed, view=self, attachments=files)

    @ui.button(
        emoji="<:double_left:982588991461281833>",
        style=discord.ButtonStyle.gray,
        row=1,
        custom_id="paginator_double_left",
    )
    async def first(self, i: discord.Interaction, _: ui.Button):
        self.current_page = 0

        await self.update_children(i)

    @ui.button(
        emoji="<:left:982588994778972171>",
        style=discord.ButtonStyle.blurple,
        row=1,
        custom_id="paginator_left",
    )
    async def previous(self, i: discord.Interaction, _: ui.Button):
        self.current_page -= 1

        await self.update_children(i)

    @ui.button(
        label="page 1/1",
        custom_id="paginator_page",
        disabled=True,
        row=1,
    )
    async def page(self, _: discord.Interaction, __: ui.Button):
        """This button is just a label"""

    @ui.button(
        emoji="<:right:982588993122238524>",
        style=discord.ButtonStyle.blurple,
        row=1,
        custom_id="paginator_right",
    )
    async def next(self, i: discord.Interaction, _: ui.Button):
        self.current_page += 1

        await self.update_children(i)

    @ui.button(
        emoji="<:double_right:982588990223958047>",
        style=discord.ButtonStyle.gray,
        row=1,
        custom_id="paginator_double_right",
    )
    async def last(self, i: discord.Interaction, _: ui.Button):
        self.current_page = len(self.embeds) - 1

        await self.update_children(i)


class GeneralPaginator:
    def __init__(
        self,
        i: Inter,
        embeds: List[discord.Embed],
        custom_children: Optional[List[Union[ui.Button, ui.Select]]] = None,
        fps: Optional[Dict[str, io.BytesIO]] = None,
    ):
        self.i = i
        self.embeds = embeds
        self.custom_children = custom_children
        self.fps = fps

    async def start(
        self,
        edit: bool = False,
        followup: bool = False,
        ephemeral: bool = False,
    ) -> None:
        if not self.embeds:
            raise ValueError("Missing embeds")

        locale = (
            await get_user_lang(self.i.user.id, self.i.client.pool) or self.i.locale
        )
        view = self.setup_view(locale)
        view.author = self.i.user
        view.first.disabled = view.previous.disabled = True
        view.last.disabled = view.next.disabled = len(self.embeds) == 1

        view.page.label = text_map.get(176, locale).format(
            num=f"{view.current_page + 1}/{len(self.embeds)}"
        )

        if self.custom_children:
            for child in self.custom_children:
                view.add_item(child)

        kwargs = self.setup_kwargs(view, edit, ephemeral)
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

    def setup_kwargs(
        self, view: GeneralPaginatorView, edit: bool, ephemeral: bool
    ) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {"embed": self.embeds[0], "view": view}
        if ephemeral:
            kwargs["ephemeral"] = ephemeral
        if self.fps:
            url = self.embeds[0].image.url
            if url is None:
                raise ValueError("Missing image url")
            fp = self.fps.get(url)
            if fp is None:
                raise ValueError("Missing fp")
            fp.seek(0)
            if edit:
                kwargs["attachments"] = [discord.File(fp, filename=url)]
            else:
                kwargs["files"] = [discord.File(fp, filename=url)]
        return kwargs

    def setup_view(self, locale: discord.Locale | str) -> GeneralPaginatorView:
        view = GeneralPaginatorView(self.embeds, str(locale))
        return view
