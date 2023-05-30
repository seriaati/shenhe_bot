from typing import List, Sequence, Union

import discord
import genshin
from discord import ui
from genshin.models import GenshinAccount

from apps.db.tables.hoyo_account import convert_game
from apps.db.tables.user_settings import Settings
from apps.text_map import text_map
from apps.text_map.convert_locale import to_genshin_py
from dev.base_ui import BaseView
from dev.config import mid_timeout
from dev.models import DefaultEmbed, Inter
from utils.text_map import get_game_name


class View(BaseView):
    def __init__(self):
        super().__init__(timeout=mid_timeout)
        self.author: Union[discord.User, discord.Member]
        self.lang: str
        self.accs: Sequence[GenshinAccount]
        self.current_acc: GenshinAccount
        self.ltuid: int

    async def init(self, i: Inter) -> None:
        lang = await i.client.db.settings.get(i.user.id, Settings.LANG)
        self.lang = lang or str(i.locale)

    async def start(self, i: Inter, ltuid: int) -> None:
        await self.init(i)

        self.ltuid = ltuid
        cookie = await i.client.db.cookies.get(ltuid)
        client = genshin.Client({"ltuid": cookie.ltuid, "ltoken": cookie.ltoken})
        self.accs = await client.get_game_accounts(lang=to_genshin_py(self.lang))

        self.author = i.user
        self.current_acc = self.accs[0]
        embed = self.acc_embed()
        self.add_components()

        await i.edit_original_response(embed=embed, view=self)
        self.message = await i.original_response()

    def add_components(self) -> None:
        self.clear_items()
        self.add_item(Add(text_map.get(786, self.lang)))
        self.add_item(Cancel(text_map.get(787, self.lang)))
        self.add_item(AccSelect(text_map.get(785, self.lang), self.acc_options()))

    def acc_embed(self) -> DefaultEmbed:
        lang = self.lang
        acc = self.current_acc
        game_type = convert_game(acc.game)

        embed = DefaultEmbed()
        embed.set_title(782, lang, self.author)
        embed.add_field(name="UID", value=str(acc.uid), inline=False)
        embed.add_field(name=text_map.get(601, lang), value=acc.nickname, inline=False)
        embed.add_field(
            name=text_map.get(783, lang), value=f"Lv. {acc.level}", inline=False
        )
        embed.add_field(
            name=text_map.get(784, lang),
            value=get_game_name(game_type, lang),
            inline=False,
        )
        return embed

    def acc_options(self) -> List[discord.SelectOption]:
        options: List[discord.SelectOption] = []
        for acc in self.accs:
            desc = get_game_name(convert_game(acc.game), self.lang)
            option = discord.SelectOption(
                label=f"{acc.nickname} ({acc.uid})",
                description=desc,
                value=str(acc.uid),
            )
            options.append(option)
        return options


class Add(ui.Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.view: View

    async def callback(self, i: Inter) -> None:
        await i.response.defer()
        acc = self.view.current_acc
        await i.client.db.users.insert(
            user_id=i.user.id,
            uid=acc.uid,
            ltuid=self.view.ltuid,
            game=convert_game(acc.game),
            nickname=acc.nickname,
        )
        await i.client.db.users.set_current(i.user.id, acc.uid)
        
        embed = DefaultEmbed()
        embed.set_title(39, self.view.lang, i.user)
        await i.edit_original_response(embed=embed, view=None)


class Cancel(ui.Button):
    def __init__(self, label: str):
        super().__init__(label=label)
        self.view: View

    async def callback(self, i: Inter) -> None:
        text = text_map.get(788, self.view.lang)
        exist = await i.client.db.users.check_exist(self.view.ltuid)
        if not exist:
            await i.client.db.cookies.delete(self.view.ltuid)
        await i.response.edit_message(content=f"||{text}||", embed=None, view=None)


class AccSelect(ui.Select):
    def __init__(self, placeholder: str, options: List[discord.SelectOption]):
        super().__init__(placeholder=placeholder, options=options)
        self.view: View

    async def callback(self, i: Inter) -> None:
        self.view.current_acc = next(
            filter(lambda x: x.uid == int(self.values[0]), self.view.accs)
        )
        embed = self.view.acc_embed()
        self.view.add_components()
        await i.response.edit_message(embed=embed, view=self.view)
