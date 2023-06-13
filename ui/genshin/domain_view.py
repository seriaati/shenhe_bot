from datetime import timedelta
from typing import Optional

import aiohttp
import discord
from discord import ui

import dev.asset as asset
import dev.config as config
from apps.db.tables.user_settings import Settings
from apps.draw import main_funcs
from apps.text_map import text_map
from dev.base_ui import BaseView
from dev.models import DefaultEmbed, DrawInput, Inter
from utils import get_dt_now, get_farm_data, get_uid_tz


class View(BaseView):
    def __init__(self, lang: discord.Locale | str, weekday: int):
        super().__init__(timeout=config.mid_timeout)

        self.add_item(WeekDaySelect(weekday, lang))


class WeekDaySelect(ui.Select):
    def __init__(self, weekday: int, lang: discord.Locale | str):
        options = []
        for index in range(0, 7):
            weekday_text = text_map.get(234 + index, lang)
            options.append(
                discord.SelectOption(
                    label=weekday_text, value=str(index), default=(index == weekday)
                )
            )

        self.lang = lang
        super().__init__(options=options, placeholder=text_map.get(583, lang), row=4)

    async def callback(self, i: Inter):
        await return_farm_interaction(i, int(self.values[0]))


async def return_farm_interaction(i: Inter, weekday: Optional[int] = None):
    await i.response.defer()

    session: aiohttp.ClientSession = i.client.session

    lang = await i.client.db.settings.get(i.user.id, Settings.LANG) or str(i.locale)

    if weekday is None:
        uid = await i.client.db.users.get_uid(i.user.id)
        now = get_dt_now() + timedelta(hours=get_uid_tz(uid))
        weekday = now.weekday()
    if weekday == 6:
        view = View(lang, 6)
        view.author = i.user
        view.message = await i.edit_original_response(
            embed=DefaultEmbed().set_title(309, lang, i.user),
            view=view,
            attachments=[],
        )
        return

    embed = DefaultEmbed().set_author(
        name=text_map.get(644, lang), icon_url=asset.loader
    )
    await i.edit_original_response(embed=embed, view=None, attachments=[])

    farm_data = await get_farm_data(lang, session, weekday)

    fp = await main_funcs.draw_farm_domain_card(
        DrawInput(
            loop=i.client.loop,
            session=session,
            lang=lang,
            dark_mode=await i.client.db.settings.get(i.user.id, Settings.DARK_MODE),
        ),
        farm_data,
    )
    fp.seek(0)

    view = View(lang, weekday)
    view.author = i.user

    await i.edit_original_response(
        embed=None, attachments=[discord.File(fp, "farm.png")], view=view
    )
    view.message = await i.original_response()
