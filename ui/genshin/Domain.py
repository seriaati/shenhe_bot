from datetime import timedelta
from typing import Optional

import aiohttp
import asyncpg
import discord
from discord import ui

import dev.asset as asset
import config
from apps.db import get_user_lang, get_user_theme
from apps.draw import main_funcs
from apps.genshin import get_farm_data, get_uid, get_uid_tz
from apps.text_map import text_map
from base_ui import BaseView
from dev.models import DefaultEmbed, DrawInput
from utility import get_dt_now


class View(BaseView):
    def __init__(self, locale: discord.Locale | str, weekday: int):
        super().__init__(timeout=config.mid_timeout)

        self.add_item(WeekDaySelect(weekday, locale))


class WeekDaySelect(ui.Select):
    def __init__(self, weekday: int, locale: discord.Locale | str):
        options = []
        for index in range(0, 7):
            weekday_text = text_map.get(234 + index, locale)
            options.append(
                discord.SelectOption(
                    label=weekday_text, value=str(index), default=(index == weekday)
                )
            )

        self.locale = locale
        super().__init__(options=options, placeholder=text_map.get(583, locale), row=4)

    async def callback(self, i: discord.Interaction):
        await return_farm_interaction(i, int(self.values[0]))


async def return_farm_interaction(
    i: discord.Interaction, weekday: Optional[int] = None
):
    await i.response.defer()

    pool: asyncpg.pool.Pool = i.client.pool  # type: ignore
    session: aiohttp.ClientSession = i.client.session  # type: ignore

    locale = await get_user_lang(i.user.id, pool) or i.locale

    if weekday is None:
        uid = await get_uid(i.user.id, pool)
        now = get_dt_now() + timedelta(hours=get_uid_tz(uid))
        weekday = now.weekday()
    if weekday == 6:
        view = View(locale, 6)
        view.author = i.user
        view.message = await i.edit_original_response(
            embed=DefaultEmbed().set_title(309, locale, i.user),
            view=view,
            attachments=[],
        )
        return

    embed = DefaultEmbed().set_author(
        name=text_map.get(644, locale), icon_url=asset.loader
    )
    await i.edit_original_response(embed=embed, view=None, attachments=[])

    farm_data = await get_farm_data(locale, session, weekday)

    fp = await main_funcs.draw_farm_domain_card(
        DrawInput(
            loop=i.client.loop,
            session=session,
            locale=locale,
            dark_mode=await get_user_theme(i.user.id, pool),
        ),
        farm_data,
    )
    fp.seek(0)

    view = View(locale, weekday)
    view.author = i.user

    await i.edit_original_response(
        embed=None, attachments=[discord.File(fp, "farm.jpeg")], view=view
    )
    view.message = await i.original_response()
