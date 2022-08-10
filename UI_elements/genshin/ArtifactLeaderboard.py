from typing import Any

import aiosqlite
from apps.genshin.utils import get_artifact, get_character, get_fight_prop
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.game.equip_types import equip_types
from data.game.fight_prop import fight_prop
from debug import DefaultView
from discord import ButtonStyle, Interaction, Locale, Member
from discord.ui import Button
from utility.paginator import GeneralPaginator
from utility.utils import (default_embed, divide_chunks, error_embed, rank_user)


class View(DefaultView):
    def __init__(self, author: Member, db: aiosqlite.Connection, locale: Locale, user_locale: str):
        super().__init__(timeout=None)
        self.author = author
        self.sub_stat = None
        self.db = db
        self.locale = locale
        self.user_locale = user_locale
        for prop_id, prop_info in fight_prop.items():
            if prop_info['substat']:
                self.add_item(SubStatButton(
                    prop_id, text_map.get(prop_info['text_map_hash'], locale, user_locale)))

    async def interaction_check(self, i: Interaction) -> bool:
        user_locale = await get_user_locale(i.user.id, self.db)
        if i.user.id != self.author.id:
            await i.response.send_message(embed=error_embed().set_author(name=text_map.get(143, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        return i.user.id == self.author.id


class SubStatButton(Button):
    def __init__(self, prop_id: str, prop_name: str):
        super().__init__(label=prop_name, emoji=get_fight_prop(prop_id)['emoji'])
        self.prop_id = prop_id

    async def callback(self, i: Interaction) -> Any:
        await i.response.defer()
        self.view.sub_stat = self.prop_id
        self.view.stop()


class GoBack(Button):
    def __init__(self, c: aiosqlite.Cursor, label: str, db: aiosqlite.Connection):
        super().__init__(label=label, row=2, style=ButtonStyle.green)
        self.c = c
        self.db = db

    async def callback(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.db)
        view = View(i.user, self.db, i.locale, user_locale)
        await i.response.edit_message(embed=default_embed().set_author(name=text_map.get(255, i.locale, user_locale), icon_url=i.user.avatar), view=view)
        await view.wait()
        await self.c.execute('SELECT * FROM substat_leaderboard WHERE sub_stat = ?', (view.sub_stat,))
        leaderboard = await self.c.fetchall()
        leaderboard.sort(key=lambda index: float(
            str(index[5]).replace('%', '')), reverse=True)
        user_rank = rank_user(i.user.id, leaderboard)
        leaderboard = divide_chunks(leaderboard, 10)
        rank = 1
        embeds = []
        for small_leaderboard in leaderboard:
            message = ''
            for index, tuple in enumerate(small_leaderboard):
                user_id = tuple[0]
                avatar_id = tuple[1]
                artifact_name = tuple[2]
                equip_type = tuple[3]
                sub_stat_value = tuple[5]
                member = i.guild.get_member(user_id)
                if member is None:
                    continue
                message += f'{rank}. {get_character(avatar_id)["emoji"]} {get_artifact(name=artifact_name)["emoji"]} {equip_types.get(equip_type)} {member.display_name} • {sub_stat_value}\n\n'
                rank += 1
            embed = default_embed(
                f'🏆 {text_map.get(256, i.locale, user_locale)} - {text_map.get(fight_prop.get(view.sub_stat)["text_map_hash"], i.locale, user_locale)} ({text_map.get(252, i.locale, user_locale)}: #{user_rank})', message)
            embeds.append(embed)
        await GeneralPaginator(i, embeds, [GoBack(self.c, text_map.get(282, i.locale, user_locale), self.db)]).start(edit=True)
