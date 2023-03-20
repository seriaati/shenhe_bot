import asyncio
import io
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import aiohttp
import asyncpg
import cachetools
import discord
import genshin
from discord.ext import commands
from enkanetwork.model.base import EnkaNetworkResponse
from logingateway import HuTaoLoginAPI
from pydantic import BaseModel, Field
from pyppeteer.browser import Browser

import ambr.models as ambr


class ShenheAccount(BaseModel):
    client: genshin.Client
    uid: int
    discord_user: Union[discord.User, discord.Member]
    user_locale: Optional[str] = None
    china: bool
    daily_checkin: bool

    class Config:
        arbitrary_types_allowed = True


class DamageResult(BaseModel):
    result_embed: discord.Embed
    cond_embed: Optional[discord.Embed] = None

    class Config:
        arbitrary_types_allowed = True


class NotificationUser(BaseModel):
    user_id: int
    threshold: int = 0
    current: int
    max: int
    uid: int
    last_notif: Optional[datetime] = None


class DrawInput(BaseModel):
    loop: asyncio.AbstractEventLoop
    session: aiohttp.ClientSession
    locale: discord.Locale | str = "en-US"
    dark_mode: bool = False

    class Config:
        arbitrary_types_allowed = True


class RecentWish(BaseModel):
    name: str
    pull_num: int
    icon: Optional[str] = None


class WishItem(BaseModel):
    name: str
    banner: int
    rarity: int
    time: datetime


class WishData(BaseModel):
    title: str
    total_wishes: int
    pity: int
    four_star: int
    five_star: int
    recents: List[RecentWish]


class Wish(BaseModel):
    time: datetime
    rarity: int
    name: str


class WishInfo(BaseModel):
    total: int
    newest_wish: Wish
    oldest_wish: Wish
    character_banner_num: int
    permanent_banner_num: int
    weapon_banner_num: int
    novice_banner_num: int


class ShenheBot(commands.AutoShardedBot):
    genshin_client: genshin.Client
    session: aiohttp.ClientSession
    gd_text_map: Dict[str, Dict[str, str]]
    browsers: Dict[str, Browser]
    gateway: HuTaoLoginAPI
    debug: bool
    maintenance: bool = False
    maintenance_time: Optional[str] = ""
    launch_time: datetime
    stats_card_cache: cachetools.TTLCache
    area_card_cache: cachetools.TTLCache
    abyss_overview_card_cache: cachetools.TTLCache
    abyss_floor_card_cache: cachetools.TTLCache
    abyss_one_page_cache: cachetools.TTLCache
    tokenStore: Dict[str, Any]
    pool: asyncpg.Pool


class TodoList:
    def __init__(self):
        self.dict: Dict[int, int] = {}

    def add_item(self, item: Dict[int, int]):
        key = list(item.keys())[0]
        value = list(item.values())[0]
        if value <= 0:
            return
        if key in self.dict:
            self.dict[key] += value
        else:
            self.dict[key] = value

    def remove_item(self, item: Dict[int, int]):
        key = list(item.keys())[0]
        value = list(item.values())[0]
        if key in self.dict:
            self.dict[key] -= value
            if self.dict[key] <= 0:
                self.dict.pop(key)

    def return_list(self) -> Dict[int, int]:
        return self.dict


class EnkaView(discord.ui.View):
    overview_embeds: List[discord.Embed]
    overview_fps: List[io.BytesIO]
    data: EnkaNetworkResponse
    en_data: EnkaNetworkResponse
    member: Union[discord.User, discord.Member]
    author: Union[discord.User, discord.Member]
    message: discord.Message
    character_options: List[discord.SelectOption]
    locale: Union[discord.Locale, str]

    original_children: List[discord.ui.Item] = []
    character_id: str = "0"
    card_data: Optional[EnkaNetworkResponse] = None

    class Config:
        arbitrary_types_allowed = True


class UserCustomImage(BaseModel):
    url: str
    nickname: str
    character_id: int
    user_id: int


class GenshinAppResult(BaseModel):
    success: bool
    result: Any


class AbyssResult(BaseModel):
    embed_title: str = Field(alias="title")
    abyss: genshin.models.SpiralAbyss
    genshin_user: genshin.models.PartialGenshinUserStats = Field(alias="user")
    discord_user: discord.User | discord.Member | discord.ClientUser
    overview_embed: discord.Embed = Field(alias="overview")
    overview_file: io.BytesIO = Field(alias="overview_card")
    abyss_floors: List[genshin.models.Floor] = Field(alias="floors")
    characters: List[genshin.models.Character]
    uid: int

    class Config:
        arbitrary_types_allowed = True


class RealtimeNoteResult(BaseModel):
    embed: discord.Embed
    draw_input: DrawInput
    notes: genshin.models.Notes

    class Config:
        arbitrary_types_allowed = True


class StatsResult(BaseModel):
    embed: discord.Embed
    file: io.BytesIO

    class Config:
        arbitrary_types_allowed = True


class AreaResult(BaseModel):
    embed: discord.Embed
    file: io.BytesIO

    class Config:
        arbitrary_types_allowed = True


class DiaryResult(BaseModel):
    embed: discord.Embed
    file: io.BytesIO

    class Config:
        arbitrary_types_allowed = True


class CharacterResult(BaseModel):
    embeds: Dict[str, discord.Embed]
    options: List[discord.SelectOption]
    file: io.BytesIO
    characters: List[genshin.models.Character]

    class Config:
        arbitrary_types_allowed = True


class CharacterBuild(BaseModel):
    embed: discord.Embed
    weapon: Optional[str] = None
    artifact: Optional[str] = None
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
    top_padding: TopPadding
    left_padding: int
    right_padding: int
    bottom_padding: int
    card_height: int
    card_width: int
    card_x_padding: int
    card_y_padding: int
    card_num: int
    max_card_num: Optional[int] = None
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
    current_user: Union[RunLeaderboardUser, SingleStrikeLeaderboardUser]

    class Config:
        arbitrary_types_allowed = True


class TodoItem(BaseModel):
    name: str
    current: int
    max: int


class AbyssHalf(BaseModel):
    num: int
    enemies: List[str]


class AbyssChamber(BaseModel):
    num: int
    enemy_level: int
    halfs: List[AbyssHalf]


class AbyssFloor(BaseModel):
    num: int
    chambers: List[AbyssChamber]


class InitLevels(BaseModel):
    level: Optional[int] = None
    a_level: Optional[int] = None
    e_level: Optional[int] = None
    q_level: Optional[int] = None
    ascension_phase: Optional[int] = None


class TodoAction(str, Enum):
    REMOVE = "remove"
    EDIT = "edit"


class OriginalInfo(BaseModel):
    view: discord.ui.View
    children: List[discord.ui.Item]
    embed: Optional[discord.Embed] = None
    attachments: Optional[List[discord.Attachment]] = None

    class Config:
        arbitrary_types_allowed = True


class DiaryLogsResult(BaseModel):
    primo_per_day: Dict[int, int]
    before_adding: Dict[int, int]


class FarmData(BaseModel):
    domain: ambr.Domain
    characters: List[ambr.Character] = []
    weapons: List[ambr.Weapon] = []


class ConditionalResult(BaseModel):
    cond: Dict[str, Any]
    desc: str
    effect: str


class CustomInteraction(discord.Interaction):
    client: ShenheBot
