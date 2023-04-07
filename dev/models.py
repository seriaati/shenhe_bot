import asyncio
import io
import typing
from datetime import datetime
from enum import Enum

import aiohttp
import asyncpg
import cachetools
import discord
import genshin
from discord.ext import commands
from enkanetwork.model.base import EnkaNetworkResponse
from logingateway import HuTaoLoginAPI
from pydantic import BaseModel
from pyppeteer.browser import Browser

import ambr.models as ambr
from apps.text_map import text_map


class ShenheAccount(BaseModel):
    client: genshin.Client
    uid: int
    discord_user: typing.Union[discord.User, discord.Member]
    user_locale: typing.Optional[str] = None
    china: bool
    daily_checkin: bool

    class Config:
        arbitrary_types_allowed = True


class DamageResult(BaseModel):
    result_embed: discord.Embed
    cond_embed: typing.Optional[discord.Embed] = None

    class Config:
        arbitrary_types_allowed = True


class NotificationUser(BaseModel):
    user_id: int
    threshold: int = 0
    current: int
    max: int
    uid: int
    last_notif: typing.Optional[datetime] = None


class DrawInput(BaseModel):
    loop: asyncio.AbstractEventLoop
    session: aiohttp.ClientSession
    locale: discord.Locale | str = "en-US"
    dark_mode: bool = False

    class Config:
        arbitrary_types_allowed = True


class BotModel(commands.AutoShardedBot):
    genshin_client: genshin.Client
    session: aiohttp.ClientSession
    browsers: typing.Dict[str, Browser]
    gateway: HuTaoLoginAPI
    pool: asyncpg.Pool
    debug: bool

    launch_browser_in_debug: bool = False
    maintenance: bool = False
    maintenance_time: str = ""
    launch_time = datetime.utcnow()
    gd_text_map: typing.Dict[str, typing.Dict[str, str]]
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
    ):
        super().__init__(title=title, description=description, color=color)

    def set_title(
        self,
        map_hash: int,
        locale: typing.Union[discord.Locale, str],
        user: typing.Union[discord.Member, discord.User],
    ):
        self.set_author(
            name=text_map.get(map_hash, locale), icon_url=user.display_avatar.url
        )
        return self


class DefaultEmbed(ShenheEmbed):
    def __init__(
        self,
        title: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
    ):
        super().__init__(title=title, description=description, color=0xA68BD3)


class ErrorEmbed(ShenheEmbed):
    def __init__(
        self,
        title: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
    ):
        super().__init__(title=title, description=description, color=0xFC5165)


class EmbedField(BaseModel):
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


class UserCustomImage(BaseModel):
    url: str
    nickname: str
    character_id: int
    user_id: int
    from_shenhe: bool


class CharacterBuild(BaseModel):
    embed: discord.Embed
    weapon: typing.Optional[str] = None
    artifact: typing.Optional[str] = None
    is_thought: bool

    class Config:
        arbitrary_types_allowed = True


class FightProp(BaseModel):
    name: str
    emoji: str
    substat: bool
    text_map_hash: int


class EnkanetworkData(BaseModel):
    data: EnkaNetworkResponse
    eng_data: EnkaNetworkResponse
    cache: EnkaNetworkResponse
    eng_cache: EnkaNetworkResponse


class TopPadding(BaseModel):
    with_title: int
    without_title: int


class DynamicBackgroundInput(BaseModel):
    top_padding: typing.Union[TopPadding, int]
    left_padding: int
    right_padding: int
    bottom_padding: int
    card_height: int
    card_width: int
    card_x_padding: int
    card_y_padding: int
    card_num: int
    max_card_num: typing.Optional[int] = None
    background_color: str
    draw_title: bool = True


class SingleStrikeLeaderboardCharacter(BaseModel):
    constellation: int
    refinement: int
    level: int
    icon: str


class SingleStrikeLeaderboardUser(BaseModel):
    user_name: str
    rank: int
    character: SingleStrikeLeaderboardCharacter
    single_strike: int
    floor: str
    stars_collected: int
    uid: int
    rank: int


class CharacterUsageResult(BaseModel):
    fp: io.BytesIO
    first_character: ambr.Character
    uses: int
    percentage: float

    class Config:
        arbitrary_types_allowed = True


class UsageCharacter(BaseModel):
    character: ambr.Character
    usage_num: int


class RunLeaderboardUser(BaseModel):
    icon_url: str
    user_name: str
    level: int
    wins_slash_runs: str
    win_percentage: str
    stars_collected: int
    uid: int
    rank: int


class LeaderboardResult(BaseModel):
    fp: io.BytesIO
    current_user: typing.Union[RunLeaderboardUser, SingleStrikeLeaderboardUser]

    class Config:
        arbitrary_types_allowed = True


class TodoItem(BaseModel):
    name: str
    current: int
    max: int


class AbyssHalf(BaseModel):
    num: int
    enemies: typing.List[str]


class AbyssChamber(BaseModel):
    num: int
    enemy_level: int
    halfs: typing.List[AbyssHalf]


class AbyssFloor(BaseModel):
    num: int
    chambers: typing.List[AbyssChamber]


class InitLevels(BaseModel):
    level: typing.Optional[int] = None
    a_level: typing.Optional[int] = None
    e_level: typing.Optional[int] = None
    q_level: typing.Optional[int] = None
    ascension_phase: typing.Optional[int] = None


class TodoAction(str, Enum):
    REMOVE = "remove"
    EDIT = "edit"


class OriginalInfo(BaseModel):
    view: discord.ui.View
    children: typing.List[discord.ui.Item]
    embed: typing.Optional[discord.Embed] = None
    attachments: typing.Optional[typing.List[discord.Attachment]] = None

    class Config:
        arbitrary_types_allowed = True


class FarmData:
    domain: ambr.Domain
    characters: typing.List[ambr.Character] = []
    weapons: typing.List[ambr.Weapon] = []


class ConditionalResult(BaseModel):
    cond: typing.Dict[str, typing.Any]
    desc: str
    effect: str


class Inter(discord.Interaction):
    client: BotModel


class TalentBoost(Enum):
    BOOST_E = "boost_e"
    BOOST_Q = "boost_q"
