from datetime import timedelta
from typing import Optional

import aiohttp
import asyncpg
import discord
from discord import ui

import asset
import config
from apps.draw import main_funcs
from apps.genshin.custom_model import DrawInput
from apps.genshin.utils import get_farm_data, get_uid, get_uid_tz
from apps.text_map import text_map
from apps.text_map.utils import get_user_locale
from base_ui import BaseView
from utility import DefaultEmbed, get_dt_now, get_user_appearance_mode


class View(BaseView):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(timeout=config.mid_timeout)

        self.add_item(WeekDaySelect(text_map.get(583, locale), locale))


class WeekDaySelect(ui.Select):
    def __init__(self, placeholder: str, locale: discord.Locale | str):
        options = []
        for index in range(0, 7):
            weekday_text = text_map.get(234 + index, locale)
            options.append(discord.SelectOption(label=weekday_text, value=str(index)))

        self.locale = locale
        super().__init__(options=options, placeholder=placeholder, row=4)

    async def callback(self, i: discord.Interaction):
        await return_farm_interaction(i, int(self.values[0]))


async def return_farm_interaction(
    i: discord.Interaction, weekday: Optional[int] = None
):
    await i.response.defer()

    pool: asyncpg.pool.Pool = i.client.pool  # type: ignore
    session: aiohttp.ClientSession = i.client.session  # type: ignore

    locale = await get_user_locale(i.user.id, pool) or i.locale

    if weekday is None:
        uid = await get_uid(i.user.id, pool)
        now = get_dt_now() + timedelta(hours=get_uid_tz(uid))
        weekday = now.weekday()
    if weekday == 6:
        view = View(locale)
        view.author = i.user
        view.message = await i.edit_original_response(
            embed=DefaultEmbed().set_author(
                name=text_map.get(309, locale), icon_url=i.user.display_avatar.url
            ),
            view=view,
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
            dark_mode=await get_user_appearance_mode(i.user.id, pool),
        ),
        farm_data,
    )
    fp.seek(0)

    view = View(locale)
    view.author = i.user

    await i.edit_original_response(
        embed=None, attachments=[discord.File(fp, "farm.jpeg")], view=view
    )
    view.message = await i.original_response()
