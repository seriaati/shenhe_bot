import ast
from typing import Dict, List

from discord import ButtonStyle, File, Interaction, Locale, SelectOption
from discord.ui import Button, Select

import asset
import config
from ambr.client import AmbrTopAPI
from ambr.models import Character
from apps.draw import main_funcs
from apps.draw.utility import image_gen_transition
from apps.genshin.custom_model import (
    DrawInput,
    RunLeaderboardUser,
    SingleStrikeLeaderboardCharacter,
    SingleStrikeLeaderboardUser,
    UsageCharacter,
)
from apps.genshin.utils import (
    get_abyss_season_date_range,
    get_character_emoji,
    get_current_abyss_season,
)
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView
from utility.utils import default_embed, error_embed, get_user_appearance_mode


class EmptyLeaderboard(Exception):
    pass


class View(BaseView):
    def __init__(self, locale: Locale | str, uid: int):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        self.uid = uid
        self.type = "single_strike_damage"
        self.area = "global"
        self.season = 0
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
            SelectOption(label=text_map.get(160, locale), value="full_clear"),
        ]
        super().__init__(
            placeholder=placeholder, min_values=1, max_values=1, options=options
        )

    async def callback(self, i: Interaction):
        self.view: View
        self.view.type = self.values[0]
        await select_callback(self.view, i, self.values[0])


class AbyssSeasonSelect(Select):
    def __init__(self, locale: Locale | str):
        current_season = get_current_abyss_season()
        hashes = [435, 436, 151]
        options = [
            SelectOption(
                label=text_map.get(hashes[index], locale)
                + f" ({current_season - index})",
                description=get_abyss_season_date_range(current_season - index),
                value=str(current_season - index),
            )
            for index in range(3)
        ]
        options.insert(0, SelectOption(label=text_map.get(154, locale), value="0"))
        super().__init__(placeholder=text_map.get(153, locale), options=options)

    async def callback(self, i: Interaction):
        self.view: View
        self.view.season = int(self.values[0])
        await select_callback(self.view, i, self.view.type)


async def select_callback(view: View, i: Interaction, leaderboard: str):
    view.type = leaderboard
    query_str = "" if view.season == 0 else f"WHERE season = {view.season}"
    uid = view.uid
    locale = view.locale
    dark_mode = await get_user_appearance_mode(i.user.id, i.client.pool)
    await image_gen_transition(i, view, locale)

    # change color of button based on current region selection
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
    if view.area == "global":
        server.style = ButtonStyle.secondary
        glob.style = ButtonStyle.primary
    elif view.area == "server":
        server.style = ButtonStyle.primary
        glob.style = ButtonStyle.secondary

    # remove or add abyss season select based on current leaderboard type
    abyss_season_select = [
        item for item in view.children if isinstance(item, AbyssSeasonSelect)
    ]
    if (
        view.type in ["single_strike_damage", "character_usage_rate", "full_clear"]
        and not abyss_season_select
    ):
        view.add_item(AbyssSeasonSelect(locale))

    # enable all the items
    for item in view.children:
        if isinstance(item, (Button, Select)):
            item.disabled = False

    # server member ids
    if view.area == "server":
        if i.guild is not None:
            if not i.guild.chunked:
                await i.guild.chunk()
            guild_member_ids = [member.id for member in i.guild.members]
        else:
            guild_member_ids = [i.user.id]
    else:
        guild_member_ids = []

    # leaderbaord title
    title = ""
    if leaderboard == "single_strike_damage":
        title = text_map.get(80, locale)
    elif leaderboard == "character_usage_rate":
        title = text_map.get(617, locale)
    elif leaderboard == "full_clear":
        title = text_map.get(160, locale)

    # draw the leaderboard
    try:
        if leaderboard == "single_strike_damage":
            users = []
            uids = []
            
            async with i.client.pool.acquire() as db:
                async with db.execute(
                    f"SELECT uid, data_uuid, single_strike, floor, stars_collected, user_name, user_id, const, refine, c_level, c_icon FROM abyss_leaderboard {query_str} ORDER BY single_strike DESC"
                ) as c:
                    rank = 1
                    current_user = None
                    for row in c.get_cursor():
                        if view.area == "server" and row[6] not in guild_member_ids:
                            continue
                        if row[0] in uids:
                            continue

                        users.append(
                            user := SingleStrikeLeaderboardUser(
                                user_name=row[5],
                                rank=rank,
                                character=SingleStrikeLeaderboardCharacter(
                                    constellation=row[7],
                                    refinement=row[8],
                                    level=row[9],
                                    icon=row[10],
                                ),
                                single_strike=row[2],
                                floor=row[3],
                                stars_collected=row[4],
                                uid=row[0],
                            )
                        )
                        uids.append(row[0])
                        
                        if row[0] == uid:
                            current_user = user
                        rank += 1
                    
            if not users:
                raise EmptyLeaderboard
            fp = await main_funcs.draw_single_strike_leaderboard(
                DrawInput(
                    loop=i.client.loop,
                    session=i.client.session,
                    locale=locale,
                    dark_mode=dark_mode,
                ),
                uid,
                users,
            )
            fp.seek(0)
            embed = default_embed(
                title,
                f"""
                    {text_map.get(457, locale) if current_user is None else text_map.get(614, locale).format(rank=current_user.rank)}
                    {text_map.get(615, locale).format(num=len(users))}
                """,
            )
            embed.set_author(
                name=get_al_title(view.season, locale),
                icon_url=i.user.display_avatar.url,
            )
            embed.set_footer(text=text_map.get(619, locale).format(command="/abyss"))
            embed.set_image(url="attachment://leaderboard.jpeg")
            await i.edit_original_response(
                embed=embed,
                attachments=[File(fp, filename="leaderboard.jpeg")],
                view=view,
            )
        elif leaderboard == "character_usage_rate":
            async with i.client.pool.acquire() as db:
                async with db.execute(
                    f"SELECT * FROM abyss_character_leaderboard {query_str}"
                ) as c:
                    data = await c.fetchall()
            if view.area == "server":
                data = [item for item in data if item[2] in guild_member_ids]
            if not data:
                raise EmptyLeaderboard
            uc_list: List[UsageCharacter] = []
            temp_dict: Dict[int, int] = {}
            for d in data:
                characters = ast.literal_eval(d[1])
                for c in characters:
                    if c in temp_dict:
                        temp_dict[c] += 1
                    else:
                        temp_dict[c] = 1
            client = AmbrTopAPI(i.client.session, to_ambr_top(locale))
            for key, value in temp_dict.items():
                if key in asset.traveler_ids:
                    key = f"{key}-anemo"
                character = await client.get_character(str(key))
                if not isinstance(character, Character):
                    continue
                uc_list.append(UsageCharacter(character=character, usage_num=value))
            result = await main_funcs.abyss_character_usage_card(
                DrawInput(
                    loop=i.client.loop,
                    session=i.client.session,
                    locale=locale,
                    dark_mode=dark_mode,
                ),
                uc_list,
            )
            result.fp.seek(0)
            embed = default_embed(
                title,
                f"{text_map.get(618, locale).format(name=get_character_emoji(result.first_character.id)+' '+result.first_character.name, num=result.uses, percent=round(result.percentage, 1))}\n"
                f"{text_map.get(615, locale).format(num=len(data))}",
            )
            embed.set_author(
                name=get_al_title(view.season, locale),
                icon_url=i.user.display_avatar.url,
            )
            embed.set_footer(text=text_map.get(619, locale).format(command="/abyss"))
            embed.set_image(url="attachment://character_usage.jpeg")
            await i.edit_original_response(
                embed=embed,
                attachments=[File(result.fp, filename="character_usage.jpeg")],
                view=view,
            )
        elif leaderboard == "full_clear":
            users = []
            async with i.client.pool.acquire() as db:
                async with db.execute(
                    f"SELECT uid, wins, runs, level, icon_url, user_id, stars_collected, user_name FROM abyss_leaderboard WHERE {query_str.replace('WHERE', '')} {'AND' if query_str else ''} stars_collected = 36 ORDER BY runs ASC"
                ) as c:
                    rank = 1
                    current_user = None
                    for row in c.get_cursor():
                        if view.area == "server" and row[5] not in guild_member_ids:
                            continue
                        if row[0] in [u.uid for u in users]:
                            continue

                        users.append(
                            user := RunLeaderboardUser(
                                icon_url=row[4],
                                user_name=row[7],
                                level=row[3],
                                wins_slash_runs=f"{row[1]}/{row[2]}",
                                win_percentage=round(row[1] / row[2] * 100, 1),
                                stars_collected=row[6],
                                uid=row[0],
                                rank=rank,
                            )
                        )
                        if row[0] == uid:
                            current_user = user
                        rank += 1
            if not users:
                raise EmptyLeaderboard
            fp = await main_funcs.draw_run_leaderboard(
                DrawInput(
                    loop=i.client.loop,
                    session=i.client.session,
                    locale=locale,
                    dark_mode=dark_mode,
                ),
                uid,
                users,
            )
            fp.seek(0)
            embed = default_embed(
                title,
                f"""
                    {text_map.get(457, locale) if current_user is None else text_map.get(614, locale).format(rank=current_user.rank)}
                    {text_map.get(615, locale).format(num=len(users))}
                """,
            )
            embed.set_author(
                name=get_al_title(view.season, locale),
                icon_url=i.user.display_avatar.url,
            )
            embed.set_footer(text=text_map.get(619, locale).format(command="/abyss"))
            embed.set_image(url="attachment://leaderboard.jpeg")
            await i.edit_original_response(
                embed=embed,
                attachments=[File(fp, filename="leaderboard.jpeg")],
                view=view,
            )

    except EmptyLeaderboard:
        for item in view.children:
            if isinstance(item, Select):
                item.disabled = False
        glob.disabled = True
        server.disabled = True
        await i.edit_original_response(
            embed=error_embed(title, text_map.get(620, locale)).set_author(
                name=get_al_title(view.season, locale), icon_url=asset.error_icon
            ),
            view=view,
            attachments=[],
        )


class Global(Button):
    def __init__(self, label: str):
        super().__init__(
            label=label, emoji="🌎", custom_id="global", style=ButtonStyle.primary, row=4
        )

    async def callback(self, i: Interaction):
        self.view: View
        self.view.area = "global"
        await select_callback(self.view, i, self.view.type)


class Server(Button):
    def __init__(self, label: str):
        super().__init__(label=label, emoji="🏠", custom_id="server", row=4)

    async def callback(self, i: Interaction):
        self.view: View
        self.view.area = "server"
        await select_callback(self.view, i, self.view.type)


def get_al_title(season: int, locale: Locale | str):
    """Get the title of the abyss leaderboard."""
    if season != 0:
        return text_map.get(88, locale).format(
            phase=text_map.get(430, locale) + " ", num=season
        )
    else:
        return text_map.get(88, locale).format(phase="", num=text_map.get(154, locale))
