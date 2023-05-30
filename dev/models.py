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
from logingateway.model import Player
from pyppeteer.browser import Browser

import ambr.models as ambr
from apps.db.main import Database
from apps.text_map import text_map
from dev.enum import GameType


@define
class DamageResult:
    result_embed: discord.Embed
    cond_embed: typing.Optional[discord.Embed] = None


@define
class DrawInput:
    loop: asyncio.AbstractEventLoop
    session: aiohttp.ClientSession
    locale: discord.Locale | str = "en-US"
    dark_mode: bool = False


@define
class LoginInfo:
    message: discord.Message
    lang: str
    author: typing.Union[discord.User, discord.Member]


class BotModel(commands.AutoShardedBot):
    session: aiohttp.ClientSession
    browsers: typing.Dict[str, Browser]
    gateway: HuTaoLoginAPI
    pool: asyncpg.Pool
    debug: bool
    user: discord.ClientUser
    owner_id: int = 410036441129943050
    db: Database

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
    token_store: typing.Dict[str, LoginInfo] = {}
    player_store: typing.Dict[int, Player] = {}
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


T = typing.TypeVar("T")


@define
class BoardUser(typing.Generic[T]):
    rank: int
    entry: T


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


@define
class AbyssResult:
    embed_title: str
    abyss: genshin.models.SpiralAbyss
    genshin_user: genshin.models.PartialGenshinUserStats
    discord_user: discord.User | discord.Member | discord.ClientUser
    overview_embed: discord.Embed
    overview_file: io.BytesIO
    abyss_floors: typing.List[genshin.models.Floor]
    characters: typing.List[genshin.models.Character]
    uid: int