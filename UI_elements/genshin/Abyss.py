from typing import Any

import aiosqlite
from discord import File, Interaction, Locale, SelectOption, User, Member
from discord.ui import Select
from apps.genshin.custom_model import AbyssResult

import config
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseView
from utility.utils import default_embed, get_user_appearance_mode
from yelan.draw import draw_abyss_floor_card, draw_abyss_one_page


class View(BaseView):
    def __init__(
        self,
        author: User | Member,
        result: AbyssResult,
        locale: Locale | str,
        db: aiosqlite.Connection,
    ):
        super().__init__(timeout=config.mid_timeout)
        self.author = author
        self.db = db

        self.add_item(FloorSelect(result, locale))


class FloorSelect(Select):
    def __init__(self, result: AbyssResult, locale: Locale | str):
        options = [
            SelectOption(label=text_map.get(43, locale), value="overview")
        ]
        for index in range(len(result.abyss_floors)):
            options.append(
                SelectOption(
                    label=text_map.get(146, locale).format(a=9 + index),
                    value=str(index),
                )
            )
        super().__init__(
            placeholder=text_map.get(148, locale), options=options
        )
        self.add_option(label=text_map.get(643, locale), value="one-page")
        self.abyss_result = result

    async def callback(self, i: Interaction) -> Any:
        await i.response.defer()
        dark_mode = await get_user_appearance_mode(i.user.id, i.client.db)  # type: ignore
        user_locale = await get_user_locale(i.user.id, i.client.db)  # type: ignore
        if self.values[0] == "overview":
            fp = self.abyss_result.overview_file
            fp.seek(0)
            image = File(fp, filename="overview_card.jpeg")
            await i.edit_original_response(
                embed=self.abyss_result.overview_embed,
                attachments=[image],
            )
        elif self.values[0] == "one-page":
            embed = default_embed()
            embed.set_author(
                name=text_map.get(644, i.locale, user_locale),
                icon_url="https://i.imgur.com/V76M9Wa.gif",
            )
            await i.edit_original_response(embed=embed, attachments=[])
            cache = i.client.abyss_one_page_cache  # type: ignore
            key = self.abyss_result.genshin_user.info.nickname
            fp = cache.get(key)
            if fp is None:
                fp = await draw_abyss_one_page(
                    self.abyss_result.genshin_user,
                    self.abyss_result.abyss,
                    user_locale or i.locale,
                    dark_mode,
                    i.client.session,  # type: ignore
                )
                cache[key] = fp
            fp.seek(0)
            image = File(fp, filename="abyss_one_page.jpeg")
            embed = default_embed()
            embed.set_image(url="attachment://abyss_one_page.jpeg")
            embed.set_author(
                name=self.abyss_result.embed_title,
                icon_url=self.abyss_result.discord_user.display_avatar.url,
            )
            await i.edit_original_response(embed=embed, attachments=[image])
        else:
            embed = default_embed()
            embed.set_author(
                name=text_map.get(644, i.locale, user_locale),
                icon_url="https://i.imgur.com/V76M9Wa.gif",
            )
            await i.edit_original_response(embed=embed, attachments=[])
            embed = default_embed()
            embed.set_image(url="attachment://floor.jpeg")
            embed.set_author(
                name=self.abyss_result.embed_title,
                icon_url=self.abyss_result.discord_user.display_avatar.url,
            )
            cache = i.client.abyss_floor_card_cache  # type: ignore
            key = str(self.abyss_result.abyss_floors[int(self.values[0])])
            fp = cache.get(key)
            if fp is None:
                fp = await draw_abyss_floor_card(
                    dark_mode,
                    self.abyss_result.abyss_floors[int(self.values[0])],
                    i.client.session,  # type: ignore
                )
                cache[key] = fp
            fp.seek(0)
            image = File(fp, filename="floor.jpeg")
            await i.edit_original_response(embed=embed, attachments=[image])
