from typing import Any

import discord
from discord import ui

import dev.config as config
from apps.db import get_user_lang, get_user_theme
from apps.draw import main_funcs
from apps.draw.main_funcs import draw_abyss_one_page
from apps.text_map import text_map
from dev.base_ui import BaseView
from dev.models import AbyssResult, CustomInteraction, DefaultEmbed, DrawInput


class View(BaseView):
    def __init__(
        self,
        author: discord.User | discord.Member,
        result: AbyssResult,
        locale: discord.Locale | str,
    ):
        self.author = author
        super().__init__(timeout=config.mid_timeout)

        self.add_item(FloorSelect(result, locale))


class FloorSelect(ui.Select):
    def __init__(self, result: AbyssResult, locale: discord.Locale | str):
        options = [
            discord.SelectOption(label=text_map.get(43, locale), value="overview")
        ]
        for index in range(len(result.abyss_floors)):
            options.append(
                discord.SelectOption(
                    label=text_map.get(146, locale).format(a=9 + index),
                    value=str(index),
                )
            )
        super().__init__(placeholder=text_map.get(148, locale), options=options)
        self.add_option(label=text_map.get(643, locale), value="one-page")
        self.abyss_result = result

    async def callback(self, i: CustomInteraction) -> Any:
        await i.response.defer()
        dark_mode = await get_user_theme(i.user.id, i.client.pool)
        locale = await get_user_lang(i.user.id, i.client.pool) or i.locale
        if self.values[0] == "overview":
            fp = self.abyss_result.overview_file
            fp.seek(0)
            image = discord.File(fp, filename="overview_card.jpeg")
            await i.edit_original_response(
                embed=self.abyss_result.overview_embed,
                attachments=[image],
            )
        elif self.values[0] == "one-page":
            embed = DefaultEmbed()
            embed.set_author(
                name=text_map.get(644, locale),
                icon_url="https://i.imgur.com/V76M9Wa.gif",
            )
            await i.edit_original_response(embed=embed, attachments=[])
            cache = i.client.abyss_one_page_cache
            key = self.abyss_result.genshin_user.info.nickname
            fp = cache.get(key)
            if fp is None:
                fp = await draw_abyss_one_page(
                    DrawInput(
                        loop=i.client.loop,
                        session=i.client.session,
                        locale=locale,
                        dark_mode=dark_mode,
                    ),
                    self.abyss_result.genshin_user,
                    self.abyss_result.abyss,
                    self.abyss_result.characters,
                )
                cache[key] = fp
            fp.seek(0)
            image = discord.File(fp, filename="abyss_one_page.jpeg")
            embed = DefaultEmbed()
            embed.set_image(url="attachment://abyss_one_page.jpeg")
            embed.set_author(
                name=self.abyss_result.embed_title,
                icon_url=self.abyss_result.discord_user.display_avatar.url,
            )
            await i.edit_original_response(embed=embed, attachments=[image])
        else:
            embed = DefaultEmbed()
            embed.set_author(
                name=text_map.get(644, locale),
                icon_url="https://i.imgur.com/V76M9Wa.gif",
            )
            await i.edit_original_response(embed=embed, attachments=[])
            embed = DefaultEmbed()
            embed.set_image(url="attachment://floor.jpeg")
            embed.set_author(
                name=self.abyss_result.embed_title,
                icon_url=self.abyss_result.discord_user.display_avatar.url,
            )
            cache = i.client.abyss_floor_card_cache
            key = str(self.abyss_result.abyss_floors[int(self.values[0])])
            fp = cache.get(key)
            if fp is None:
                fp = await main_funcs.draw_abyss_floor_card(
                    DrawInput(
                        loop=i.client.loop,
                        session=i.client.session,
                        dark_mode=dark_mode,
                    ),
                    self.abyss_result.abyss_floors[int(self.values[0])],
                    self.abyss_result.characters,
                )
                cache[key] = fp
            fp.seek(0)
            image = discord.File(fp, filename="floor.jpeg")
            await i.edit_original_response(embed=embed, attachments=[image])
