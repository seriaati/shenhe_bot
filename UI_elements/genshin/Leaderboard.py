from typing import List, Tuple

from discord import ButtonStyle, File, Interaction, Locale, SelectOption
from discord.ui import Button, Select

import asset
import config
from apps.genshin.utils import get_character_emoji
from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView
from utility.utils import default_embed, error_embed, get_user_appearance_mode
from yelan.draw import draw_abyss_leaderboard, draw_character_usage_card


class EmptyLeaderboard(Exception):
    pass


class View(BaseView):
    def __init__(self, locale: Locale | str, uid: int):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        self.uid = uid
        self.type = "single_strike_damage"
        self.area = "global"
        self.add_item(LeaderboardSelect(text_map.get(616, locale), locale))
        self.add_item(glob := Global(text_map.get(453, locale)))
        self.add_item(server := Server(text_map.get(455, locale)))
        glob.disabled = True
        server.disabled = True


class LeaderboardSelect(Select):
    def __init__(self, placeholder: str, locale: Locale | str):
        options = [
            SelectOption(label=text_map.get(80, locale), value="single_strike_damage"),
            SelectOption(label=text_map.get(617, locale), value="character_usage_rate"),
        ]
        super().__init__(
            placeholder=placeholder, min_values=1, max_values=1, options=options
        )

    async def callback(self, i: Interaction):
        self.view: View
        self.view.type = self.values[0]
        await select_callback(self.view, i, self.values[0])


async def select_callback(view: View, i: Interaction, leaderboard: str):
    view.type = leaderboard
    uid = view.uid
    locale = view.locale
    dark_mode = await get_user_appearance_mode(i.user.id, i.client.db)
    embed = default_embed().set_author(
        name=text_map.get(644, locale), icon_url=asset.loader
    )
    await i.response.edit_message(embed=embed, attachments=[], view=None)
    glob = [
        item
        for item in view.children
        if isinstance(item, Button) and item.custom_id == "global"
    ][0]
    server = [
        item
        for item in view.children
        if isinstance(item, Button) and item.custom_id == "server"
    ][0]
    glob.disabled = False
    server.disabled = False
    if view.area == "global":
        server.style = ButtonStyle.secondary
        glob.style = ButtonStyle.primary
    elif view.area == "server":
        server.style = ButtonStyle.primary
        glob.style = ButtonStyle.secondary
    if view.area == "server":
        if i.guild is not None:
            if not i.guild.chunked:
                await i.guild.chunk()
            guild_member_ids = [member.id for member in i.guild.members]
        else:
            guild_member_ids = [i.user.id]
    else:
        guild_member_ids = []
    try:
        if leaderboard == "single_strike_damage":
            async with i.client.db.execute(
                "SELECT * FROM abyss_leaderboard ORDER BY single_strike DESC"
            ) as c:
                data: List[Tuple] = await c.fetchall()
            if view.area == "server":
                data = [item for item in data if item[6] in guild_member_ids]
            if not data:
                raise EmptyLeaderboard
            result = await draw_abyss_leaderboard(
                dark_mode, i.client.session, uid, data, locale
            )
            result.fp.seek(0)
            embed = default_embed(
                message=f"""
                    {text_map.get(457, locale) if result.user_rank is None else text_map.get(614, locale).format(rank=result.user_rank)}
                    {text_map.get(615, locale).format(num=len(data))}
                """
            )
            embed.set_author(
                name=text_map.get(88, locale), icon_url=i.user.display_avatar.url
            )
            embed.set_footer(text=text_map.get(619, locale).format(command="/abyss"))
            embed.set_image(url="attachment://leaderboard.jpeg")
            await i.edit_original_response(
                embed=embed,
                attachments=[File(result.fp, filename="leaderboard.jpeg")],
                view=view,
            )
        elif leaderboard == "character_usage_rate":
            async with i.client.db.execute(
                "SELECT * FROM abyss_character_leaderboard"
            ) as c:
                data = await c.fetchall()
            if view.area == "server":
                data = [item for item in data if item[2] in guild_member_ids]
            if not data:
                raise EmptyLeaderboard
            result = await draw_character_usage_card(
                data, i.client.session, dark_mode, locale
            )
            result.fp.seek(0)
            embed = default_embed(
                message=f"{text_map.get(618, locale).format(name=get_character_emoji(result.first_character.id)+' '+result.first_character.name, num=result.uses, percent=round(result.percentage, 1))}\n"
                f"{text_map.get(615, locale).format(num=len(data))}"
            )
            embed.set_author(
                name=text_map.get(617, locale), icon_url=i.user.display_avatar.url
            )
            embed.set_footer(text=text_map.get(619, locale).format(command="/abyss"))
            embed.set_image(url="attachment://character_usage.jpeg")
            await i.edit_original_response(
                embed=embed,
                attachments=[File(result.fp, filename="character_usage.jpeg")],
                view=view,
            )
    except EmptyLeaderboard:
        glob.disabled = True
        server.disabled = True
        await i.edit_original_response(
            embed=error_embed().set_author(
                name=text_map.get(620, locale), icon_url=asset.error_icon
            ),
            view=view,
            attachments=[],
        )


class Global(Button):
    def __init__(self, label: str):
        super().__init__(
            label=label, emoji="🌎", custom_id="global", style=ButtonStyle.primary
        )

    async def callback(self, i: Interaction):
        self.view: View
        self.view.area = "global"
        await select_callback(self.view, i, self.view.type)


class Server(Button):
    def __init__(self, label: str):
        super().__init__(label=label, emoji="🏠", custom_id="server")

    async def callback(self, i: Interaction):
        self.view: View
        self.view.area = "server"
        await select_callback(self.view, i, self.view.type)
