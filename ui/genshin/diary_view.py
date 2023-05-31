import calendar
import io
from datetime import timedelta
from typing import Dict, List, Optional, Union

from dateutil.relativedelta import relativedelta
from discord import File, Member, User, utils
from discord.ui import Button
from genshin.models import DiaryType
from matplotlib import pyplot as plt

import dev.asset as asset
import dev.config as config
from apps.db.tables.hoyo_account import HoyoAccount
from apps.draw.main_funcs import draw_diary_card
from apps.text_map import text_map
from apps.text_map.convert_locale import to_genshin_py
from dev.base_ui import BaseButton, BaseSelect, BaseView
from dev.enum import GameType
from dev.exceptions import GameNotSupported
from dev.models import DefaultEmbed, DrawInput, Inter
from utils import divide_chunks
from utils.general import get_dt_now
from utils.genshin import convert_ar_to_wl, convert_wl_to_mora, get_uid_tz


class View(BaseView):
    def __init__(
        self,
    ):
        super().__init__(timeout=config.mid_timeout)
        self.user: HoyoAccount
        self.lang: str
        self.dark_mode: bool
        self.member: Union[Member, User]

    async def _init(self, i: Inter):
        self.user = await i.client.db.users.get(self.member.id)
        if self.user.game is not GameType.GENSHIN:
            raise GameNotSupported(self.user.game, [GameType.GENSHIN])

        settings = await self.user.settings
        lang = settings.lang
        self.lang = lang or str(i.locale)
        self.dark_mode = settings.dark_mode

    async def start(self, i: Inter, member: Union[Member, User]):
        await i.response.defer()
        self.member = member
        await self._init(i)
        self._add_items()

        fp = await self.get_diary(i)
        fp.seek(0)

        self.author = i.user
        await i.followup.send(view=self, file=File(fp, "diary.jpeg"))
        self.message = await i.original_response()

    def _add_items(self):
        self.clear_items()
        self.add_item(MonthSelect(text_map.get(424, self.lang), self.lang))
        self.add_item(Primo(text_map.get(70, self.lang)))
        self.add_item(Mora(text_map.get(72, self.lang)))
        self.add_item(InfoButton())

    async def get_diary(
        self, i: Inter, month_offset: Optional[int] = None
    ) -> io.BytesIO:
        tz = get_uid_tz(self.user.uid)
        now = get_dt_now() + timedelta(hours=tz)
        if month_offset:
            now += relativedelta(months=month_offset)
        month = now.month

        client = await self.user.client
        diary = await client.get_diary(
            self.user.uid, month=month, lang=to_genshin_py(self.lang)
        )

        fp = await draw_diary_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                lang=self.lang,
                dark_mode=self.dark_mode,
            ),
            diary,
            convert_wl_to_mora(convert_ar_to_wl(60)),
            now.month,
        )
        return fp

    async def get_logs(self, diary_type: DiaryType):
        now = get_dt_now()
        now += timedelta(hours=get_uid_tz(self.user.uid))
        primo_per_day: Dict[int, int] = {}

        client = await self.user.client
        async for action in client.diary_log(uid=self.user.uid, type=diary_type):
            if action.time.day not in primo_per_day:
                primo_per_day[action.time.day] = 0
            primo_per_day[action.time.day] += action.amount

        before_adding: Dict[int, int] = primo_per_day.copy()
        before_adding = dict(sorted(before_adding.items()))

        for i in range(1, calendar.monthrange(now.year, now.month)[1] + 1):
            if i not in primo_per_day:
                primo_per_day[i] = 0

        primo_per_day = dict(sorted(primo_per_day.items()))

        embed = DefaultEmbed()
        embed.set_image(url="attachment://diary.png")

        now = utils.utcnow()
        values: List[str] = []
        for day, amount in before_adding.items():
            values.append(
                f"{utils.format_dt(now.replace(day=day), 'd')} / **{amount}**\n"
            )
        divided_values: List[List[str]] = list(divide_chunks(values, 15))
        for d_v in divided_values:
            embed.add_field(name="** **", value="".join(d_v), inline=True)

        plt.plot(
            primo_per_day.keys(),
            primo_per_day.values(),
            color="#617d9d",
        )
        plot = io.BytesIO()
        plt.savefig(plot, bbox_inches=None, format="png")
        plt.clf()

        return plot, embed


class InfoButton(Button):
    def __init__(self):
        super().__init__(emoji=asset.info_emoji)
        self.view: View

    async def callback(self, i: Inter):
        await i.response.send_message(
            embed=DefaultEmbed(description=text_map.get(398, self.view.lang)),
            ephemeral=True,
        )


class MonthSelect(BaseSelect):
    def __init__(self, placeholder: str, lang: str):
        super().__init__(placeholder=placeholder)
        self.add_option(label=text_map.get(425, lang), value="0")
        self.add_option(label=text_map.get(506, lang), value="-1")
        self.add_option(label=text_map.get(427, lang), value="-2")

        self.view: View

    async def callback(self, i: Inter):
        await self.loading(i)
        fp = await self.view.get_diary(i, int(self.values[0]))
        fp.seek(0)
        await self.restore(i)
        await i.edit_original_response(attachments=[File(fp, filename="diary.jpeg")])


class Primo(BaseButton):
    def __init__(self, label: str):
        super().__init__(label=label, emoji=asset.primo_emoji)
        self.view: View

    async def callback(self, i: Inter):
        await self.loading(i)
        plot, embed = await self.view.get_logs(DiaryType.PRIMOGEMS)
        await self.restore(i)

        plot.seek(0)
        await i.followup.send(embed=embed, file=File(plot, "diary.png"), ephemeral=True)


class Mora(BaseButton):
    def __init__(self, label: str):
        super().__init__(label=label, emoji=asset.mora_emoji)
        self.view: View

    async def callback(self, i: Inter):
        await self.loading(i)
        plot, embed = await self.view.get_logs(DiaryType.MORA)
        await self.restore(i)

        plot.seek(0)
        await i.followup.send(embed=embed, file=File(plot, "diary.png"), ephemeral=True)
