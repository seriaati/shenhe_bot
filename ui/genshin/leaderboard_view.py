import asyncio
import io
import typing
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

import aiohttp
import discord

import dev.asset as asset
import dev.config as config
import dev.models as models
from ambr import AmbrTopAPI, Character
from apps.db.tables.abyss_board import AbyssBoardEntry
from apps.db.tables.abyss_chara_board import AbyssCharaBoardEntry
from apps.db.tables.user_settings import Settings
from apps.draw import main_funcs
from apps.text_map import text_map, to_ambr_top
from dev.base_ui import BaseButton, BaseSelect, BaseView
from dev.enum import Category
from utils import get_abyss_season_date_range, get_character_emoji
from utils.genshin import get_current_abyss_season


class Area(Enum):
    GLOBAL = "global"
    SERVER = "server"


class View(BaseView):
    def __init__(self) -> None:
        super().__init__(timeout=config.mid_timeout)
        self.lang: str
        self.uid: int
        self.dark_mode: bool
        self.author: Union[discord.User, discord.Member]

        self.category: typing.Optional[Category] = None
        self.area: Area = Area.GLOBAL
        self.season: int = 0

    async def _init(self, i: models.Inter) -> None:
        """Init"""
        self.lang = await i.client.db.settings.get(i.user.id, Settings.LANG)
        self.lang = self.lang or str(i.locale)
        self.uid = await i.client.db.users.get_uid(i.user.id)
        self.dark_mode = await i.client.db.settings.get(i.user.id, Settings.DARK_MODE)

    def _get_leaderboard_options(self) -> List[discord.SelectOption]:
        """Get leaderboard select options"""
        options = [
            discord.SelectOption(
                label=text_map.get(80, self.lang), value="single_strike_damage"
            ),
            discord.SelectOption(
                label=text_map.get(617, self.lang), value="character_usage_rate"
            ),
            discord.SelectOption(
                label=text_map.get(160, self.lang), value="full_clear"
            ),
        ]
        return options

    def add_components(self) -> None:
        """Add items to the view"""
        self.clear_items()
        self.add_item(
            LeaderboardSelect(
                text_map.get(616, self.lang), self._get_leaderboard_options()
            )
        )
        self.add_item(Global(text_map.get(453, self.lang)))
        self.add_item(Server(text_map.get(455, self.lang)))

    async def start(self, i: models.Inter):
        """Start the view"""
        await i.response.defer()
        await self._init(i)

        embed = models.DefaultEmbed(description=text_map.get(253, self.lang))
        embed.set_author(name=f"👑 {text_map.get(252, self.lang)}")
        self.add_components()

        self.author = i.user
        await i.followup.send(embed=embed, view=self)
        self.message = await i.original_response()

    @staticmethod
    def _filter_guild_members(
        entries: Union[List[AbyssBoardEntry], List[AbyssCharaBoardEntry]],
        guild: discord.Guild,
    ):
        """Filter out leaderboard entries that are not in the guild member list"""
        for e in entries:
            if guild.get_member(e.user_id) is None:
                entries.remove(e)  # type: ignore

        return entries

    @staticmethod
    async def _filter_invalid_entries(
        entries: Union[List[AbyssBoardEntry], List[AbyssCharaBoardEntry]],
        db: models.Database,
    ):
        for e in entries:
            if isinstance(e, AbyssBoardEntry) and e.runs == 0:
                entries.remove(e)  # type: ignore
                await db.leaderboard.abyss.delete(e.uid, e.season)

        return entries

    async def return_leaderboard(self, i: models.Inter):
        """Draw the leaderboard image and return leaderboard interaction"""
        if i.guild and not i.guild.chunked:
            await i.guild.chunk()

        # get leaderboard entries
        season = None if self.season == 0 else self.season
        if self.category is Category.SINGLE_STRIKE:
            entries = await i.client.db.leaderboard.abyss.get_all(self.category, season)
        elif self.category is Category.CHARACTER_USAGE_RATE:
            entries = await i.client.db.leaderboard.abyss_character.get_all(season)
        elif self.category is Category.FULL_CLEAR:
            entries = await i.client.db.leaderboard.abyss.get_all(self.category, season)
        else:
            entries = []

        # filter out invalid entries
        entries = await self._filter_invalid_entries(entries, i.client.db)

        # filter out users that are not in the guild
        if i.guild and self.area is Area.SERVER:
            entries = self._filter_guild_members(entries, i.guild)

        if not entries:
            embed = models.ErrorEmbed()
            embed.set_author(
                name=text_map.get(620, self.lang), icon_url=i.user.display_avatar.url
            )
            return await i.followup.send(embed=embed, ephemeral=True)

        # draw leaderboards
        if isinstance(entries[0], AbyssBoardEntry):
            current_user, users = self.get_board_users(entries)  # type: ignore
            if self.category is Category.SINGLE_STRIKE:
                embed, fp = await self.draw_single_strike(
                    current_user, users, i.client.session, i.client.loop
                )
            else:  # self.category is Category.FULL_CLEAR
                embed, fp = await self.draw_full_clear(
                    current_user, users, i.client.session, i.client.loop
                )
        else:
            embed, fp = await self.draw_character_usage(
                entries, i.client.session, i.client.loop  # type: ignore
            )

        # enable the global and server buttons
        glob: Global = self.get_item("global")
        server: Server = self.get_item("server")
        glob.disabled = False
        server.disabled = False

        # set the global and server button styles to primary if they are selected
        glob.style = (
            discord.ButtonStyle.primary
            if self.area is Area.GLOBAL
            else discord.ButtonStyle.secondary
        )
        server.style = (
            discord.ButtonStyle.primary
            if self.area is Area.SERVER
            else discord.ButtonStyle.secondary
        )

        # send leaderboard
        fp.seek(0)
        await i.edit_original_response(
            embed=embed, attachments=[discord.File(fp, "board.jpeg")], view=self
        )

    def get_board_users(
        self, entries: List[AbyssBoardEntry]
    ) -> Tuple[
        Optional[models.BoardUser[AbyssBoardEntry]],
        List[models.BoardUser[AbyssBoardEntry]],
    ]:
        current_user = None
        rank = 1
        uids: List[int] = []
        users: List[models.BoardUser[AbyssBoardEntry]] = []
        for e in entries:
            if e.uid in uids:
                continue

            user = models.BoardUser(rank=rank, entry=e)
            users.append(user)
            uids.append(e.uid)

            if e.uid == self.uid:
                current_user = user
            rank += 1

        return current_user, users

    async def draw_single_strike(
        self,
        current_user: Optional[models.BoardUser[AbyssBoardEntry]],
        users: List[models.BoardUser[AbyssBoardEntry]],
        session: aiohttp.ClientSession,
        loop: asyncio.AbstractEventLoop,
    ) -> Tuple[discord.Embed, io.BytesIO]:
        fp = await main_funcs.draw_single_strike_leaderboard(
            models.DrawInput(
                loop=loop,
                session=session,
                lang=self.lang,
                dark_mode=self.dark_mode,
            ),
            self.uid,
            users,
        )

        embed = models.DefaultEmbed(
            text_map.get(80, self.lang),
            f"""
            {text_map.get(457, self.lang) if current_user is None else text_map.get(614, self.lang).format(rank=current_user.rank)}
            {text_map.get(615, self.lang).format(num=len(users))}
            """,
        )
        embed.set_author(
            name=get_al_title(self.season, self.lang),
            icon_url=self.author.display_avatar.url,
        )
        embed.set_footer(text=text_map.get(619, self.lang).format(command="abyss"))
        embed.set_image(url="attachment://board.jpeg")

        return embed, fp

    async def draw_full_clear(
        self,
        current_user: Optional[models.BoardUser[AbyssBoardEntry]],
        users: List[models.BoardUser[AbyssBoardEntry]],
        session: aiohttp.ClientSession,
        loop: asyncio.AbstractEventLoop,
    ) -> Tuple[discord.Embed, io.BytesIO]:
        fp = await main_funcs.draw_run_leaderboard(
            models.DrawInput(
                loop=loop,
                session=session,
                lang=self.lang,
                dark_mode=self.dark_mode,
            ),
            self.uid,
            users,
        )

        embed = models.DefaultEmbed(
            text_map.get(160, self.lang),
            f"""
            {text_map.get(457, self.lang) if current_user is None else text_map.get(614, self.lang).format(rank=current_user.rank)}
            {text_map.get(615, self.lang).format(num=len(users))}
            """,
        )
        embed.set_author(
            name=get_al_title(self.season, self.lang),
            icon_url=self.author.display_avatar.url,
        )
        embed.set_footer(text=text_map.get(619, self.lang).format(command="/abyss"))
        embed.set_image(url="attachment://board.jpeg")

        return embed, fp

    async def draw_character_usage(
        self,
        entries: List[AbyssCharaBoardEntry],
        session: aiohttp.ClientSession,
        loop: asyncio.AbstractEventLoop,
    ) -> Tuple[discord.Embed, io.BytesIO]:
        uc_list: List[models.UsageCharacter] = []
        temp_dict: Dict[int, int] = {}
        for e in entries:
            if e.character_ids is None:
                continue
            for c in e.character_ids:
                if c in temp_dict:
                    temp_dict[c] += 1
                else:
                    temp_dict[c] = 1

        client = AmbrTopAPI(session, to_ambr_top(self.lang))
        for key, value in temp_dict.items():
            if key in asset.traveler_ids:
                key = f"{key}-anemo"
            character = await client.get_character(str(key))
            if not isinstance(character, Character):
                raise AssertionError
            uc_list.append(models.UsageCharacter(character=character, usage_num=value))

        result = await main_funcs.abyss_character_usage_card(
            models.DrawInput(
                loop=loop,
                session=session,
                lang=self.lang,
                dark_mode=self.dark_mode,
            ),
            uc_list,
        )

        character_emoji = get_character_emoji(result.first_character.id)
        character_name = f"{character_emoji} {result.first_character.name}"
        embed = models.DefaultEmbed(
            text_map.get(617, self.lang),
            f"{text_map.get(618, self.lang).format(name=character_name, num=result.uses, percent=round(result.percentage, 1))}\n"
            f"{text_map.get(615, self.lang).format(num=len(entries))}",
        )
        embed.set_author(
            name=get_al_title(self.season, self.lang),
            icon_url=self.author.display_avatar.url,
        )
        embed.set_footer(text=text_map.get(619, self.lang).format(command="/abyss"))
        embed.set_image(url="attachment://board.jpeg")

        return embed, result.fp


class LeaderboardSelect(BaseSelect):
    def __init__(self, placeholder: str, options: List[discord.SelectOption]):
        super().__init__(placeholder=placeholder, options=options)
        self.view: View

    async def callback(self, i: models.Inter):
        self.view.category = Category(self.values[0])
        await self.loading(i)
        await self.view.return_leaderboard(i)
        await self.restore(i)


class AbyssSeasonSelect(BaseSelect):
    def __init__(self, lang: discord.Locale | str):
        current_season = get_current_abyss_season()
        hashes = (435, 436, 151)
        options = [
            discord.SelectOption(
                label=text_map.get(hashes[index], lang)
                + f" ({current_season - index})",
                description=get_abyss_season_date_range(current_season - index),
                value=str(current_season - index),
            )
            for index in range(3)
        ]
        options.insert(
            0, discord.SelectOption(label=text_map.get(154, lang), value="0")
        )
        super().__init__(
            placeholder=text_map.get(153, lang),
            options=options,
            custom_id="season_select",
        )
        self.view: View

    async def callback(self, i: models.Inter):
        self.view.season = int(self.values[0])
        await self.loading(i)
        await self.view.return_leaderboard(i)
        await self.restore(i)


class Global(BaseButton):
    def __init__(self, label: str):
        super().__init__(
            label=label,
            emoji="🌎",
            custom_id="global",
            style=discord.ButtonStyle.primary,
            row=4,
            disabled=True,
        )
        self.view: View

    async def callback(self, i: models.Inter):
        self.view.area = Area.GLOBAL
        await self.loading(i)
        await self.view.return_leaderboard(i)
        await self.restore(i)


class Server(BaseButton):
    def __init__(self, label: str):
        super().__init__(
            label=label,
            emoji="🏠",
            custom_id="server",
            style=discord.ButtonStyle.secondary,
            row=4,
            disabled=True,
        )
        self.view: View

    async def callback(self, i: models.Inter):
        self.view.area = Area.SERVER
        await self.loading(i)
        await self.view.return_leaderboard(i)
        await self.restore(i)


def get_al_title(season: int, lang: discord.Locale | str):
    """Get the title of the abyss leaderboard."""
    if season != 0:
        return text_map.get(88, lang).format(
            phase=text_map.get(430, lang) + " ", num=season
        )
    return text_map.get(88, lang).format(phase="", num=text_map.get(154, lang))
