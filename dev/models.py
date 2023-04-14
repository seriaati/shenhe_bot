import asyncio
import io
import typing
from datetime import datetime

import aiohttp
import asyncpg
import cachetools
import discord
import genshin
from attr import define, field
from discord.ext import commands
from enkanetwork.model.base import EnkaNetworkResponse
from logingateway import HuTaoLoginAPI
from pyppeteer.browser import Browser
from sqlalchemy import future

import ambr.models as ambr
from apps.text_map import text_map


@define
class ShenheAccount:
    client: genshin.Client
    uid: int
    discord_user: typing.Union[discord.User, discord.Member]
    china: bool
    daily_checkin: bool
    user_locale: typing.Optional[str] = None


@define
class User:
    uid: int
    user_id: int

    current: bool
    daily_checkin: bool
    china: bool
    client: genshin.Client = field(init=False)

    nickname: typing.Optional[str] = None
    ltuid: typing.Optional[str] = None
    ltoken: typing.Optional[str] = None
    cookie_token: typing.Optional[str] = None
    last_checkin_date: typing.Optional[datetime] = None

    def __attrs_post_init__(self) -> None:
        self.client = genshin.Client(
            {
                "ltuid": self.ltuid,
                "ltoken": self.ltoken,
                "cookie_token": self.cookie_token,
            },
            uid=self.uid,
            game=genshin.Game.GENSHIN,
            region=genshin.Region.CHINESE if self.china else genshin.Region.OVERSEAS,
        )

    @staticmethod
    def from_row(row: asyncpg.Record) -> "User":
        return User(
            uid=row["uid"],
            user_id=row["user_id"],
            current=row["current"],
            daily_checkin=row["daily_checkin"],
            china=row["china"],
            nickname=row["nickname"],
            ltuid=row["ltuid"],
            ltoken=row["ltoken"],
            cookie_token=row["cookie_token"],
            last_checkin_date=row["last_checkin_date"],
        )


@define
class DamageResult:
    result_embed: discord.Embed
    cond_embed: typing.Optional[discord.Embed] = None


@define
class NotificationUser:
    user_id: int
    current: int
    max: int
    uid: int
    threshold: int = 0
    last_notif: typing.Optional[datetime] = None


@define
class DrawInput:
    loop: asyncio.AbstractEventLoop
    session: aiohttp.ClientSession
    locale: typing.Union[discord.Locale, str] = "en-US"
    dark_mode: bool = False

class BotModel(commands.AutoShardedBot):
    genshin_client: genshin.Client
    session: aiohttp.ClientSession
    browsers: typing.Dict[str, Browser]
    gateway: HuTaoLoginAPI
    pool: asyncpg.Pool
    debug: bool
    user: discord.ClientUser
    gd_text_map: typing.Dict[str, typing.Dict[str, str]]
    engine: future.Engine
    
    owner_id: int = 410036441129943050
    launch_browser_in_debug: bool = False
    maintenance: bool = False
    maintenance_time: str = ""
    launch_time = datetime.utcnow()
    stats_card_cache = cachetools.TTLCache(maxsize=512, ttl=120)
    area_card_cache = cachetools.TTLCache(maxsize=512, ttl=120)
    abyss_overview_card_cache = cachetools.TTLCache(maxsize=512, ttl=120)
    abyss_floor_card_cache = cachetools.TTLCache(maxsize=512, ttl=120)
    abyss_one_page_cache = cachetools.TTLCache(maxsize=512, ttl=120)
    tokenStore: typing.Dict[str, typing.Any] = {}
    disabled_commands: typing.List[str] = []


class ShenheEmbed(discord.Embed):
    def __init__(
        self,
        title: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        color: typing.Optional[int] = 0xA68BD3,
    ) -> None:
        super().__init__(title=title, description=description, color=color)

    def set_title(
        self,
        map_hash: int,
        locale: typing.Union[discord.Locale, str],
        user: typing.Union[discord.Member, discord.User],
    ) -> "ShenheEmbed":
        self.set_author(
            name=text_map.get(map_hash, locale), icon_url=user.display_avatar.url
        )
        return self

    def set_user_footer(
        self,
        user: typing.Union[discord.Member, discord.User],
        uid: typing.Optional[int] = None,
    ) -> "ShenheEmbed":
        text = user.display_name
        if uid:
            text += f" | {uid}"
        self.set_footer(text=text, icon_url=user.display_avatar.url)
        return self


class DefaultEmbed(ShenheEmbed):
    def __init__(
        self,
        title: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
    ) -> None:
        super().__init__(title=title, description=description, color=0xA68BD3)


class ErrorEmbed(ShenheEmbed):
    def __init__(
        self,
        title: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
    ):
        super().__init__(title=title, description=description, color=0xFC5165)


@define
class EmbedField:
    name: str
    value: str


class TodoList:
    def __init__(self):
        self.dict: typing.Dict[int, int] = {}

    def add_item(self, item: typing.Dict[int, int]):
        key = list(item.keys())[0]
        value = list(item.values())[0]
        if value <= 0:
            return
        if key in self.dict:
            self.dict[key] += value
        else:
            self.dict[key] = value

    def remove_item(self, item: typing.Dict[int, int]):
        key = list(item.keys())[0]
        value = list(item.values())[0]
        if key in self.dict:
            self.dict[key] -= value
            if self.dict[key] <= 0:
                self.dict.pop(key)

    def return_list(self) -> typing.Dict[int, int]:
        return self.dict


@define
class UserCustomImage:
    url: str
    nickname: str
    character_id: int
    user_id: int
    from_shenhe: bool


@define
class CharacterBuild:
    embed: discord.Embed
    is_thought: bool
    weapon: typing.Optional[str] = None
    artifact: typing.Optional[str] = None


@define
class FightProp:
    name: str
    emoji: str
    substat: bool
    text_map_hash: int


@define
class EnkanetworkData:
    data: EnkaNetworkResponse
    eng_data: EnkaNetworkResponse
    cache: EnkaNetworkResponse
    eng_cache: EnkaNetworkResponse


@define
class TopPadding:
    with_title: int
    without_title: int


@define
class DynamicBackgroundInput:
    top_padding: typing.Union[TopPadding, int]
    left_padding: int
    right_padding: int
    bottom_padding: int
    card_height: int
    card_width: int
    card_x_padding: int
    card_y_padding: int
    card_num: int
    background_color: str
    max_card_num: typing.Optional[int] = None
    draw_title: bool = True


@define
class SingleStrikeLeaderboardCharacter:
    constellation: int
    refinement: int
    level: int
    icon: str


@define
class SingleStrikeLeaderboardUser:
    user_name: str
    rank: int
    character: SingleStrikeLeaderboardCharacter
    single_strike: int
    floor: str
    stars_collected: int
    uid: int
    rank: int


@define
class CharacterUsageResult:
    fp: io.BytesIO
    first_character: ambr.Character
    uses: int
    percentage: float


@define
class UsageCharacter:
    character: ambr.Character
    usage_num: int


@define
class RunLeaderboardUser:
    icon_url: str
    user_name: str
    level: int
    wins_slash_runs: str
    win_percentage: str
    stars_collected: int
    uid: int
    rank: int


@define
class LeaderboardResult:
    fp: io.BytesIO
    current_user: typing.Union[RunLeaderboardUser, SingleStrikeLeaderboardUser]


@define
class TodoItem:
    name: str
    current: int
    max: int


@define
class AbyssHalf:
    num: int
    enemies: typing.List[str]


@define
class AbyssChamber:
    num: int
    enemy_level: int
    halfs: typing.List[AbyssHalf]


@define
class AbyssFloor:
    num: int
    chambers: typing.List[AbyssChamber]


@define
class InitLevels:
    level: typing.Optional[int] = None
    a_level: typing.Optional[int] = None
    e_level: typing.Optional[int] = None
    q_level: typing.Optional[int] = None
    ascension_phase: typing.Optional[int] = None


@define
class OriginalInfo:
    view: discord.ui.View
    children: typing.List[discord.ui.Item]
    embed: typing.Optional[discord.Embed] = None
    attachments: typing.Optional[typing.List[discord.Attachment]] = None


class FarmData:
    def __init__(self, domain: ambr.Domain) -> None:
        self.domain = domain
        self.characters: typing.List[ambr.Character] = []
        self.weapons: typing.List[ambr.Weapon] = []


@define
class ConditionalResult:
    cond: typing.Dict[str, typing.Any]
    desc: str
    effect: str


class Inter(discord.Interaction):
    client: BotModel
