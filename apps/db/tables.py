import datetime
import typing

import asyncpg
import discord
import genshin
from attr import define, field

from apps.text_map.convert_locale import to_genshin_py
from dev.enum import NotificationType


@define
class AbyssCharacterLeaderboard:
    """Abyss character usage leaderboard"""

    user_id: int
    """Discord user ID"""

    uid: int
    """Genshin Impact UID"""
    season: int
    """Abyss season"""
    characters: typing.Optional[typing.List[int]] = field(default=None)
    """Character ID list"""


@define
class AbyssLeaderboard:
    """Single strike damage leaderboard"""

    user_id: int
    """Discord user ID"""

    uid: int
    """Genshin Impact UID"""
    season: int
    """Abyss season"""
    user_name: str
    """Genshin Impact user name"""
    level: int
    """Genshin Impact adventure rank"""
    icon_url: str
    """Genshin Impact user avatar URL"""

    floor: str
    """Abyss floor reached"""
    stars_collected: int
    """Total stars collected"""
    single_strike: int
    """Highest single strike damage"""
    runs: int
    """Total abyss runs"""
    wins: int
    """Total abyss wins"""

    character_level: int = field(alias="c_level")
    """Character level"""
    character_icon: str = field(alias="c_icon")
    """Character icon URL"""
    constellation: int = field(alias="const")
    """Character constellation level"""
    refinemenet: int = field(alias="refine")
    """Weapon refinement level"""


@define
class NotifBase:
    """Notification base table"""

    uid: int
    """Genshin Impact UID"""
    user_id: int
    """Discord user ID"""
    last_notif: typing.Optional[datetime.datetime]
    """Last notification time"""

    type: NotificationType
    """Notification type"""
    current: int = field(default=0)
    """Current notification count"""
    max: int = field(default=3)
    """Maximum notification count"""
    toggle: bool = field(default=False)
    """Notification toggle"""


@define
class PotNotification(NotifBase):
    """Realm currency notification"""

    type: NotificationType = field(default=NotificationType.POT)
    """Notification type"""
    threshold: int = field(default=2000)
    """Realm currency threshold"""


@define
class PtNotification(NotifBase):
    """Parametric transformer notification"""
    
    type: NotificationType = field(default=NotificationType.PT)
    """Notification type"""


@define
class ResinNotification(NotifBase):
    """Resin notification"""

    type: NotificationType = field(default=NotificationType.RESIN)
    """Notification type"""
    threshold: int = field(default=130)
    """Resin threshold"""


@define
class UserAccount:
    """User account"""

    uid: int
    """Genshin Impact UID"""
    user_id: int
    """Discord user ID"""

    ltuid: typing.Optional[str]
    """User account ltuid"""
    ltoken: typing.Optional[str]
    """User account ltoken"""
    cookie_token: typing.Optional[str]
    """User account cookie token"""
    client: genshin.Client = field(init=False)

    nickname: typing.Optional[str]
    """User account nickname"""
    current: bool = field(default=True)
    """Whether this is the current account"""
    china: bool = field(default=False)
    """Whether this is a China account"""

    daily_checkin: bool = field(default=True)
    """Daily check-in toggle"""
    last_checkin_date: typing.Optional[datetime.date] = field(default=None)
    """Last daily check-in date"""

    lang: typing.Optional[str] = field(default=None)
    """User language"""
    discord_user: typing.Optional[discord.User] = field(default=None)

    def __attrs_post_init__(self) -> None:
        client = genshin.Client(
            uid=self.uid,
            game=genshin.Game.GENSHIN,
            region=genshin.Region.CHINESE if self.china else genshin.Region.OVERSEAS,
        )
        if (
            self.ltuid is not None
            and self.ltoken is not None
            and self.cookie_token is not None
        ):
            cookies = {
                "ltuid": self.ltuid,
                "ltoken": self.ltoken,
                "cookie_token": self.cookie_token,
            }
            client.set_cookies(cookies)
        self.client = client

    async def fetch_lang(self, pool: asyncpg.Pool) -> typing.Optional[str]:
        lang: typing.Optional[str] = await pool.fetchval(
            "SELECT lang FROM user_settings WHERE user_id = $1", self.user_id
        )
        if lang is None or not isinstance(lang, str):
            return
        self.lang = lang
        self.client.lang = to_genshin_py(lang)
        return lang

    async def fetch_discord_user(self, bot: discord.Client) -> discord.User:
        user = bot.get_user(self.user_id)
        if user is None:
            user = await bot.fetch_user(self.user_id)
        self.discord_user = user
        return user