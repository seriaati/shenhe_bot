from typing import Dict, List

import discord
from discord import ui, utils

import dev.asset as asset
import dev.config as config
import dev.models as models
from ambr import AmbrTopAPI, Character
from apps.db.tables import AbyssCharacterLeaderboard, AbyssLeaderboard
from apps.draw import main_funcs
from apps.text_map import text_map, to_ambr_top
from dev.base_ui import BaseView
from utils import (get_abyss_season_date_range, get_character_emoji,
                   get_current_abyss_season, get_user_theme,
                   image_gen_transition)


class EmptyLeaderboard(Exception):
    pass


class View(BaseView):
    def __init__(self, locale: discord.Locale | str, uid: int):
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


class LeaderboardSelect(ui.Select):
    def __init__(self, placeholder: str, locale: discord.Locale | str):
        options = [
            discord.SelectOption(
                label=text_map.get(80, locale), value="single_strike_damage"
            ),
            discord.SelectOption(
                label=text_map.get(617, locale), value="character_usage_rate"
            ),
            discord.SelectOption(label=text_map.get(160, locale), value="full_clear"),
        ]
        super().__init__(placeholder=placeholder, options=options)
        self.view: View

    async def callback(self, i: models.Inter):
        self.view.type = self.values[0]
        await select_callback(self.view, i, self.values[0])


class AbyssSeasonSelect(ui.Select):
    def __init__(self, locale: discord.Locale | str):
        current_season = get_current_abyss_season()
        hashes = [435, 436, 151]
        options = [
            discord.SelectOption(
                label=text_map.get(hashes[index], locale)
                + f" ({current_season - index})",
                description=get_abyss_season_date_range(current_season - index),
                value=str(current_season - index),
            )
            for index in range(3)
        ]
        options.insert(
            0, discord.SelectOption(label=text_map.get(154, locale), value="0")
        )
        super().__init__(
            placeholder=text_map.get(153, locale),
            options=options,
            custom_id="abyss_season_select",
        )
        self.view: View

    async def callback(self, i: models.Inter):
        self.view.season = int(self.values[0])
        await select_callback(self.view, i, self.view.type)


async def select_callback(view: View, i: models.Inter, leaderboard: str):
    view.type = leaderboard
    pool = i.client.pool
    session = i.client.session
    abyss_command = "/abyss"

    uid = view.uid
    locale = view.locale
    dark_mode = await get_user_theme(i.user.id, pool)
    await image_gen_transition(i, view, locale)

    # change color of button based on current region selection
    glob = utils.get(view.children, custom_id="global")
    server = utils.get(view.children, custom_id="server")
    if not isinstance(glob, ui.Button) or not isinstance(server, ui.Button):
        raise AssertionError
    if view.area == "global":
        server.style = discord.ButtonStyle.secondary
        glob.style = discord.ButtonStyle.primary
    elif view.area == "server":
        server.style = discord.ButtonStyle.primary
        glob.style = discord.ButtonStyle.secondary

        # also chunk the guild if it hasn't been chunked yet
        if i.guild and not i.guild.chunked:
            await i.guild.chunk(cache=True)

    # remove or add abyss season select based on current leaderboard type
    abyss_season_select = utils.get(view.children, custom_id="abyss_season_select")
    if (
        view.type in ["single_strike_damage", "character_usage_rate", "full_clear"]
        and not abyss_season_select
    ):
        view.add_item(AbyssSeasonSelect(locale))

    # enable all the items
    for item in view.children:
        if isinstance(item, (ui.Button, ui.Select)):
            item.disabled = False

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
            await return_single_strike(
                view, i, pool, session, abyss_command, uid, locale, dark_mode, title
            )

        elif leaderboard == "character_usage_rate":
            await return_usage_rate(
                view, i, pool, session, abyss_command, locale, dark_mode, title
            )

        elif leaderboard == "full_clear":
            await return_full_clear(
                view, i, pool, session, abyss_command, uid, locale, dark_mode, title
            )

    except EmptyLeaderboard:
        view.disable_items()
        glob.disabled = True
        server.disabled = True

        await i.edit_original_response(
            embed=models.ErrorEmbed(title, text_map.get(620, locale)).set_author(
                name=get_al_title(view.season, locale), icon_url=asset.error_icon
            ),
            view=view,
            attachments=[],
        )


async def return_single_strike(
    view, i, pool, session, abyss_command, uid, locale, dark_mode, title
):
    single_strike_users: List[models.SingleStrikeLeaderboardUser] = []
    uids: List[int] = []

    if view.season != 0:
        rows = await pool.fetch(
            """
            SELECT *
            FROM
                abyss_leaderboard
            WHERE
                season = $1
            ORDER BY
                single_strike DESC
            """,
            view.season,
        )
    else:
        rows = await pool.fetch(
            """
            SELECT *
            FROM
                abyss_leaderboard
            ORDER BY
                single_strike DESC
            """
        )
    if not rows:
        raise EmptyLeaderboard

    data = [AbyssLeaderboard(**row) for row in rows]

    current_user = None
    rank = 1
    for d in data:
        # filter out users that are not in the server
        if i.guild and view.area == "server":
            member = i.guild.get_member(d.user_id)
            if member is None:
                continue

                # filter out users with UID that are already in the list
        if d.uid in uids:
            continue

        single_strike_users.append(
            user := models.SingleStrikeLeaderboardUser(
                uid=d.uid,
                user_name=d.user_name,
                rank=rank,
                character=models.SingleStrikeLeaderboardCharacter(
                    constellation=d.constellation,
                    refinement=d.refinemenet,
                    level=d.character_level,
                    icon=d.character_icon,
                ),
                single_strike=d.single_strike,
                floor=d.floor,
                stars_collected=d.stars_collected,
                season=d.season,
            )
        )
        uids.append(d.uid)

        if d.uid == uid:
            current_user = user
        rank += 1

    fp = await main_funcs.draw_single_strike_leaderboard(
        models.DrawInput(
            loop=i.client.loop,
            session=session,
            locale=locale,
            dark_mode=dark_mode,
        ),
        uid,
        single_strike_users,
    )
    fp.seek(0)

    embed = models.DefaultEmbed(
        title,
        f"""
        {text_map.get(457, locale) if current_user is None else text_map.get(614, locale).format(rank=current_user.rank)}
        {text_map.get(615, locale).format(num=len(single_strike_users))}
        """,
    )
    embed.set_author(
        name=get_al_title(view.season, locale),
        icon_url=i.user.display_avatar.url,
    )
    embed.set_footer(text=text_map.get(619, locale).format(command=abyss_command))
    embed.set_image(url="attachment://leaderboard.jpeg")

    await i.edit_original_response(
        embed=embed,
        attachments=[discord.File(fp, filename="leaderboard.jpeg")],
        view=view,
    )


async def return_usage_rate(
    view, i, pool, session, abyss_command, locale, dark_mode, title
):
    if view.season != 0:
        rows = await pool.fetch(
            """
            SELECT *
            FROM abyss_character_leaderboard
            WHERE season = $1
            """,
            view.season,
        )
    else:
        rows = await pool.fetch(
            """
            SELECT *
            FROM abyss_character_leaderboard
            """,
        )
    if not rows:
        raise EmptyLeaderboard

    data = [AbyssCharacterLeaderboard(**row) for row in rows]
    uc_list: List[models.UsageCharacter] = []
    temp_dict: Dict[int, int] = {}
    for d in data:
        if d.characters is None:
            continue
        for c in d.characters:
            if c in temp_dict:
                temp_dict[c] += 1
            else:
                temp_dict[c] = 1

    client = AmbrTopAPI(session, to_ambr_top(locale))
    for key, value in temp_dict.items():
        if key in asset.traveler_ids:
            key = f"{key}-anemo"
        character = await client.get_character(str(key))
        if not isinstance(character, Character):
            raise AssertionError
        uc_list.append(models.UsageCharacter(character=character, usage_num=value))

    result = await main_funcs.abyss_character_usage_card(
        models.DrawInput(
            loop=i.client.loop,
            session=session,
            locale=locale,
            dark_mode=dark_mode,
        ),
        uc_list,
    )
    result.fp.seek(0)

    character_emoji = get_character_emoji(result.first_character.id)
    character_name = f"{character_emoji} {result.first_character.name}"
    embed = models.DefaultEmbed(
        title,
        f"{text_map.get(618, locale).format(name=character_name, num=result.uses, percent=round(result.percentage, 1))}\n"
        f"{text_map.get(615, locale).format(num=len(data))}",
    )
    embed.set_author(
        name=get_al_title(view.season, locale),
        icon_url=i.user.display_avatar.url,
    )
    embed.set_footer(text=text_map.get(619, locale).format(command=abyss_command))
    embed.set_image(url="attachment://character_usage.jpeg")

    await i.edit_original_response(
        embed=embed,
        attachments=[discord.File(result.fp, filename="character_usage.jpeg")],
        view=view,
    )


async def return_full_clear(
    view, i, pool, session, abyss_command, uid, locale, dark_mode, title
):
    run_users: List[models.RunLeaderboardUser] = []
    uids: List[int] = []

    if view.season != 0:
        rows = await pool.fetch(
            """
            SELECT *
            FROM abyss_leaderboard
            WHERE season = $1
            AND stars_collected = 36
            ORDER BY runs ASC
            """,
            view.season,
        )
    else:
        rows = await pool.fetch(
            """
            SELECT *
            FROM abyss_leaderboard
            WHERE stars_collected = 36
            ORDER BY runs ASC
            """
        )
    if not rows:
        raise EmptyLeaderboard

    data = [AbyssLeaderboard(**row) for row in rows]

    current_user = None
    rank = 1
    for d in data:
        if i.guild and view.area == "server":
            member = i.guild.get_member(d.user_id)
            if not member:
                continue

        if d.uid in uids:
            continue

        if d.runs == 0:
            win_percentage = 0
        else:
            win_percentage = round(d.wins / d.runs * 100, 1)

        run_users.append(
            user := models.RunLeaderboardUser(
                icon_url=d.icon_url,
                user_name=d.user_name,
                level=d.level,
                wins_slash_runs=f"{d.wins}/{d.runs}",
                win_percentage=str(win_percentage),
                stars_collected=36,
                uid=d.uid,
                rank=rank,
            )
        )
        if d.uid == uid:
            current_user = user
        uids.append(d.uid)
        rank += 1

    if not run_users:
        raise EmptyLeaderboard

    fp = await main_funcs.draw_run_leaderboard(
        models.DrawInput(
            loop=i.client.loop,
            session=session,
            locale=locale,
            dark_mode=dark_mode,
        ),
        uid,
        run_users,
    )
    fp.seek(0)

    embed = models.DefaultEmbed(
        title,
        f"""
        {text_map.get(457, locale) if current_user is None else text_map.get(614, locale).format(rank=current_user.rank)}
        {text_map.get(615, locale).format(num=len(run_users))}
        """,
    )
    embed.set_author(
        name=get_al_title(view.season, locale),
        icon_url=i.user.display_avatar.url,
    )
    embed.set_footer(text=text_map.get(619, locale).format(command=abyss_command))
    embed.set_image(url="attachment://leaderboard.jpeg")

    await i.edit_original_response(
        embed=embed,
        attachments=[discord.File(fp, filename="leaderboard.jpeg")],
        view=view,
    )


class Global(ui.Button):
    def __init__(self, label: str):
        super().__init__(
            label=label,
            emoji="🌎",
            custom_id="global",
            style=discord.ButtonStyle.primary,
            row=4,
        )
        self.view: View

    async def callback(self, i: models.Inter):
        self.view.area = "global"
        await select_callback(self.view, i, self.view.type)


class Server(ui.Button):
    def __init__(self, label: str):
        super().__init__(label=label, emoji="🏠", custom_id="server", row=4)
        self.view: View

    async def callback(self, i: models.Inter):
        self.view.area = "server"
        await select_callback(self.view, i, self.view.type)


def get_al_title(season: int, locale: discord.Locale | str):
    """Get the title of the abyss leaderboard."""
    if season != 0:
        return text_map.get(88, locale).format(
            phase=text_map.get(430, locale) + " ", num=season
        )
    return text_map.get(88, locale).format(phase="", num=text_map.get(154, locale))
