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
from utility.utils import default_embed, divide_chunks, error_embed
import config


class View(DefaultView):
    def __init__(self, author: Member, db: aiosqlite.Connection, locale: Locale, user_locale: str):
        super().__init__(timeout=config.short_timeout)
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
            await i.response.send_message(embed=error_embed().set_author(name=text_map.get(143, i.locale, user_locale), icon_url=i.user.display_avatar.url), ephemeral=True)
        return i.user.id == self.author.id


class SubStatButton(Button):
    def __init__(self, prop_id: str, prop_name: str):
        super().__init__(label=prop_name,
                         emoji=get_fight_prop(prop_id)['emoji'])
        self.prop_id = prop_id

    async def callback(self, i: Interaction) -> Any:
        await i.response.defer()
        self.view.sub_stat = self.prop_id
        self.view.stop()


class GoBack(Button):
    def __init__(self, label: str, db: aiosqlite.Connection):
        super().__init__(label=label, row=2, style=ButtonStyle.green)
        self.db = db

    async def callback(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.db)
        c = await self.db.cursor()
        
        view = View(
            i.user, self.db, i.locale, user_locale)
        await i.response.send_message(embed=default_embed().set_author(name=text_map.get(255, i.locale, user_locale), icon_url=i.user.display_avatar.url), view=view)
        await view.wait()
        view.message = await i.original_response()
        if view.sub_stat is None:
            return

        await c.execute('SELECT user_id, avatar_id, artifact_name, equip_type, sub_stat_value FROM substat_leaderboard WHERE sub_stat = ?', (view.sub_stat,))
        leaderboard = await c.fetchall()
        if len(leaderboard) == 0:
            return await i.followup.send(embed=error_embed().set_author(name=text_map.get(254, i.locale, user_locale), icon_url=i.user.display_avatar.url), ephemeral=True)
        
        leaderboard.sort(key=lambda tup: float(str(tup[4]).replace('%', '')), reverse=True)

        str_list = []
        rank = 1
        user_rank = text_map.get(253, i.locale, user_locale)
        for index, tuple in enumerate(leaderboard):
            user_id = tuple[0]
            avatar_id = tuple[1]
            artifact_name = tuple[2]
            equip_type = tuple[3]
            sub_stat_value = tuple[4]
            member = i.guild.get_member(user_id)
            if member is None:
                continue
            if member.id == i.user.id:
                user_rank = f'#{rank}'
            str_list.append(
                f'{rank}. {get_character(avatar_id)["emoji"]} {get_artifact(name=artifact_name)["emoji"]} {equip_types.get(equip_type)} {member.display_name} | {sub_stat_value}\n\n')
            rank += 1
            
        str_list = divide_chunks(str_list, 10)

        embeds = []
        for str_list in str_list:
            message = ''
            for string in str_list:
                message += string
            embed = default_embed(
                f'🏆 {text_map.get(256, i.locale, user_locale)} - {text_map.get(fight_prop.get(view.sub_stat)["text_map_hash"], i.locale, user_locale)} ({text_map.get(252, i.locale, user_locale)}: {user_rank})', message)
            embeds.append(embed)

        await GeneralPaginator(i, embeds, self.db, [GoBack(text_map.get(282, i.locale, user_locale), self.db)]).start(edit=True)