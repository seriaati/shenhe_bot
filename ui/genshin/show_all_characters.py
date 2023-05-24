import asyncio
import io
from datetime import timedelta
from typing import List, Union

import aiohttp
import asyncpg
import discord
import genshin
from dateutil import parser
from discord import ui

import ambr
import data.game.elements as game_elements
import dev.asset as asset
import dev.config as config
from apps.db.json import read_json
from apps.db.tables.user_settings import Settings
from apps.draw import main_funcs
from apps.text_map import text_map
from dev.base_ui import BaseView
from dev.models import DefaultEmbed, DrawInput, ErrorEmbed, Inter
from utils import (get_dt_now, get_user_theme, image_gen_transition,
                   update_talents_json)


class View(BaseView):
    def __init__(
        self,
        locale: discord.Locale | str,
        characters: List[genshin.models.Character],
        member: Union[discord.User, discord.Member],
        ambr_characters: List[ambr.models.Character],
    ):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        self.characters = characters
        self.ambr_characters = ambr_characters
        self.character_copy = characters.copy()
        self.author: Union[discord.User, discord.Member]
        self.member = member
        self.sort_current = "default_sort"
        self.filter_current = "default_filter"

        self.add_item(SortBy(locale))
        self.add_item(FilterBy(locale))
        self.add_item(UpdateTalentsJson(locale))

    async def start(self, i: Inter) -> None:
        self.author = i.user
        fp = await self.draw_fp(i)
        fp.seek(0)
        for child in self.children:
            if isinstance(child, (SortBy, FilterBy)):
                child.disabled = False
                for option in child.options:
                    if "default" in option.value:
                        option.default = False
                    elif option.value in (self.sort_current, self.filter_current):
                        option.default = True
                    else:
                        option.default = False
            elif isinstance(child, UpdateTalentsJson):
                child.disabled = False

        if self.filter_current == "default_filter":
            total = len(self.ambr_characters) + 1
        elif self.filter_current in game_elements.get_element_list():
            total = len(
                [x for x in self.ambr_characters if x.element == self.filter_current]
            )
        else:
            total = len(self.characters)

        await i.edit_original_response(
            view=self,
            attachments=[discord.File(fp, "characters.jpeg")],
            embed=DefaultEmbed(f"{len(self.character_copy)}/{total}").set_image(
                url="attachment://characters.jpeg"
            ),
        )
        self.message = await i.original_response()

    async def draw_fp(
        self,
        i: Inter,
    ) -> io.BytesIO:
        draw_input = DrawInput(
            loop=i.client.loop,
            session=i.client.session,
            locale=self.locale,
            dark_mode=await i.client.db.settings.get(i.user.id, Settings.DARK_MODE),
        )
        uid = await i.client.db.users.get_uid(self.member.id)
        talents = await read_json(i.client.pool, f"talents/{uid}.json")

        fp = await main_funcs.character_summary_card(
            draw_input, self.character_copy, talents or {}, i.client.pool
        )
        return fp

    def apply_filter(self) -> None:
        if (
            self.filter_current == "default_filter"
            or self.sort_current == "default_sort"
        ):
            self.character_copy = self.characters.copy()

        if self.filter_current == "friendship_1":
            self.character_copy = [x for x in self.characters if x.friendship < 10]
        elif self.filter_current == "friendship_2":
            self.character_copy = [x for x in self.characters if x.friendship == 10]
        elif self.filter_current in game_elements.get_element_list():
            self.character_copy = [
                x for x in self.characters if x.element == self.filter_current
            ]

        if self.sort_current == "element":
            self.character_copy.sort(key=lambda x: x.element)
        elif self.sort_current == "level":
            self.character_copy.sort(key=lambda x: x.level, reverse=True)
        elif self.sort_current == "rarity":
            self.character_copy.sort(key=lambda x: x.rarity, reverse=True)
        elif self.sort_current == "friendship":
            self.character_copy.sort(key=lambda x: x.friendship, reverse=True)
        elif self.sort_current == "const":
            self.character_copy.sort(key=lambda x: x.constellation, reverse=True)


class SortBy(ui.Select):
    def __init__(self, locale: Union[discord.Locale, str]):
        options = [
            discord.SelectOption(label=text_map.get(124, locale), value="default_sort"),
            discord.SelectOption(
                label=text_map.get(703, locale).title(), value="element"
            ),
            discord.SelectOption(
                label=text_map.get(183, locale).title(), value="level"
            ),
            discord.SelectOption(
                label=text_map.get(467, locale).title(), value="rarity"
            ),
            discord.SelectOption(
                label=text_map.get(299, locale).title(), value="friendship"
            ),
            discord.SelectOption(
                label=text_map.get(318, locale).title(), value="const"
            ),
        ]
        super().__init__(options=options, placeholder=text_map.get(278, locale))

        self.view: View

    async def callback(self, i: Inter):
        await image_gen_transition(i, self.view, self.view.locale)
        self.view.sort_current = self.values[0]
        self.view.apply_filter()
        await self.view.start(i)


class FilterBy(ui.Select):
    def __init__(self, locale: Union[discord.Locale, str]):
        elements = game_elements.get_element_list()
        options: List[discord.SelectOption] = [
            discord.SelectOption(
                label=text_map.get(124, locale), value="default_filter"
            )
        ]
        for element in elements:
            t_hash = game_elements.get_element_text(element)
            options.append(
                discord.SelectOption(
                    label=text_map.get(t_hash, locale),
                    value=element,
                    emoji=game_elements.get_element_emoji(element),
                )
            )
        friendship = [
            discord.SelectOption(
                label=f"{text_map.get(299, locale).title()} = 10",
                value="friendship_2",
                emoji=asset.friendship_emoji,
            ),
            discord.SelectOption(
                label=f"{text_map.get(299, locale).title()} < 10",
                value="friendship_1",
                emoji=asset.friendship_no_box_emoji,
            ),
        ]
        options.extend(friendship)
        super().__init__(options=options, placeholder=text_map.get(279, locale))

        self.view: View

    async def callback(self, i: Inter):
        await image_gen_transition(i, self.view, self.view.locale)
        self.view.filter_current = self.values[0]
        self.view.apply_filter()
        await self.view.start(i)


class UpdateTalentsJson(ui.Button):
    def __init__(self, locale: Union[discord.Locale, str]):
        super().__init__(
            label=text_map.get(404, locale), style=discord.ButtonStyle.blurple
        )

        self.view: View

    async def callback(self, i: Inter):
        locale = self.view.locale
        await i.response.edit_message(
            embed=DefaultEmbed().set_author(
                name=text_map.get(762, locale), icon_url=asset.loader
            ),
            attachments=[],
            view=None,
        )

        acc = await i.client.db.users.get(i.user.id)
        talents = await read_json(i.client.pool, f"talents/{acc.uid}.json")
        if (
            talents
            and "last_updated" in talents
            and get_dt_now() - parser.parse(talents["last_updated"])  # type: ignore
            < timedelta(hours=1)
        ):
            return await i.edit_original_response(
                embed=ErrorEmbed().set_author(
                    name=text_map.get(659, locale).format(hour=1),
                    icon_url=i.user.display_avatar.url,
                )
            )
        await update_talents_json(
            self.view.characters,
            await acc.client,
            i.client.pool,
            acc.uid,
            i.client.session,
        )
        await i.edit_original_response(
            embed=DefaultEmbed(description=text_map.get(763, locale)).set_title(
                761, locale, i.user
            ),
        )
