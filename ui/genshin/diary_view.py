import io
from typing import List

from discord import File, Locale, Member, User, utils
from discord.ui import Button, Select
from matplotlib import pyplot as plt

import dev.asset as asset
import dev.config as config
from utils import divide_chunks, get_user_lang
from apps.genshin import GenshinApp
from apps.text_map import text_map
from dev.base_ui import BaseView
from dev.models import DefaultEmbed, ErrorEmbed, Inter


class View(BaseView):
    def __init__(
        self,
        author: User | Member,
        member: User | Member,
        genshin_app: GenshinApp,
        locale: Locale | str,
    ):
        super().__init__(timeout=config.mid_timeout)
        self.author = author
        self.member = member
        self.genshin_app = genshin_app
        self.locale = locale
        self.add_item(MonthSelect(text_map.get(424, locale), locale))
        self.add_item(Primo(text_map.get(70, locale)))
        self.add_item(Mora(text_map.get(72, locale)))
        self.add_item(InfoButton())


class InfoButton(Button):
    def __init__(self):
        super().__init__(emoji=asset.info_emoji)
        self.view: View

    async def callback(self, i: Inter):
        await i.response.send_message(
            embed=DefaultEmbed(description=text_map.get(398, self.view.locale)),
            ephemeral=True,
        )


class MonthSelect(Select):
    def __init__(self, placeholder: str, locale: Locale | str):
        super().__init__(placeholder=placeholder)
        self.add_option(label=text_map.get(425, locale), value="0")
        self.add_option(label=text_map.get(506, locale), value="-1")
        self.add_option(label=text_map.get(427, locale), value="-2")

        self.view: View

    async def callback(self, i: Inter):
        user_locale = await get_user_lang(i.user.id, i.client.pool)
        embed = DefaultEmbed()
        embed.set_author(
            name=text_map.get(644, i.locale, user_locale),
            icon_url="https://i.imgur.com/V76M9Wa.gif",
        )
        await i.response.edit_message(embed=embed, attachments=[])
        user_locale = await get_user_lang(i.user.id, i.client.pool)
        r = await self.view.genshin_app.get_diary(
            self.view.member.id, i.user.id, i.locale, int(self.values[0])
        )
        if isinstance(r.result, ErrorEmbed):
            return await i.followup.send(embed=r.result)

        result = r.result
        fp = result.file
        fp.seek(0)
        view = View(
            i.user,
            self.view.member,
            self.view.genshin_app,
            user_locale or i.locale,
        )
        view.message = await i.edit_original_response(
            embed=result.embed,
            view=view,
            attachments=[File(fp, "diary.jpeg")],
        )


class Primo(Button):
    def __init__(self, label: str):
        super().__init__(label=label, emoji=asset.primo_emoji)
        self.view: View

    async def callback(self, i: Inter):
        if not self.label:
            raise AssertionError

        await primo_mora_button_callback(i, self.view, True, self.label)


class Mora(Button):
    def __init__(self, label: str):
        super().__init__(label=label, emoji=asset.mora_emoji)
        self.view: View

    async def callback(self, i: Inter):
        if not self.label:
            raise AssertionError

        await primo_mora_button_callback(i, self.view, False, self.label)


async def primo_mora_button_callback(i: Inter, view: View, is_primo: bool, label: str):
    await i.response.defer(ephemeral=True)
    result = await view.genshin_app.get_diary_logs(
        view.member.id, i.user.id, is_primo, i.locale
    )
    if isinstance(result.result, ErrorEmbed):
        await i.followup.send(embed=result.result, ephemeral=True)
        return

    log_result = result.result

    embed = DefaultEmbed()
    embed.title = label
    embed.set_image(url="attachment://diary.png")

    now = utils.utcnow()
    values: List[str] = []
    for day, amount in log_result.before_adding.items():
        values.append(f"{utils.format_dt(now.replace(day=day), 'd')} / **{amount}**\n")
    divided_values: List[List[str]] = list(divide_chunks(values, 15))
    for d_v in divided_values:
        embed.add_field(name="** **", value="".join(d_v), inline=True)

    plt.plot(
        log_result.primo_per_day.keys(),
        log_result.primo_per_day.values(),
        color="#617d9d",
    )
    plot = io.BytesIO()
    plt.savefig(plot, bbox_inches=None, format="png")
    plt.clf()

    plot.seek(0)
    file_ = File(plot, "diary.png")
    await i.followup.send(embed=embed, ephemeral=True, file=file_)
