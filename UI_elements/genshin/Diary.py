import io
from typing import List
from discord import File, Interaction, Locale, Member, User, utils
from discord.ui import Button, Select

import asset
import config
from apps.genshin.custom_model import DiaryLogsResult, DiaryResult
from apps.genshin.genshin_app import GenshinApp
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseView
from utility.utils import DefaultEmbed, divide_chunks
from matplotlib import pyplot as plt


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

    async def callback(self, i: Interaction):
        self.view: View
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

    async def callback(self, i: Interaction):
        self.view: View
        user_locale = await get_user_locale(i.user.id, i.client.pool)
        embed = DefaultEmbed()
        embed.set_author(
            name=text_map.get(644, i.locale, user_locale),
            icon_url="https://i.imgur.com/V76M9Wa.gif",
        )
        await i.response.edit_message(embed=embed, attachments=[])
        user_locale = await get_user_locale(i.user.id, i.client.pool)
        result = await self.view.genshin_app.get_diary(
            self.view.member.id, i.user.id, i.locale, int(self.values[0])
        )
        if not result.success:
            await i.followup.send(embed=result.result)
        else:
            diary_result: DiaryResult = result.result
            fp = diary_result.file
            fp.seek(0)
            view = View(
                i.user,
                self.view.member,
                self.view.genshin_app,
                user_locale or i.locale,
            )
            view.message = await i.edit_original_response(
                embed=diary_result.embed,
                view=view,
                attachments=[File(fp, "diary.jpeg")],
            )


class Primo(Button):
    def __init__(self, label: str):
        super().__init__(label=label, emoji=asset.primo_emoji)

    async def callback(self, i: Interaction):
        self.view: View
        assert self.label

        await primo_mora_button_callback(i, self.view, True, self.label)


class Mora(Button):
    def __init__(self, label: str):
        super().__init__(label=label, emoji=asset.mora_emoji)

    async def callback(self, i: Interaction):
        self.view: View
        assert self.label

        await primo_mora_button_callback(i, self.view, False, self.label)


async def primo_mora_button_callback(
    i: Interaction, view: View, is_primo: bool, label: str
):
    await i.response.defer(ephemeral=True)
    result = await view.genshin_app.get_diary_logs(
        view.member.id, i.user.id, is_primo, i.locale
    )
    log_result: DiaryLogsResult = result.result

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
