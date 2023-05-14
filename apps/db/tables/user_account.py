import datetime
import typing

import asyncpg
import discord
import genshin
from pydantic import BaseModel, Field

from apps.text_map.convert_locale import to_genshin_py
from dev.enum import GameType
from dev.exceptions import AccountNotFound, UIDNotFound


def convert_game_type(game_type: GameType) -> genshin.Game:
    if game_type is GameType.HSR:
        return genshin.Game.STARRAIL
    elif game_type is GameType.HONKAI:
        return genshin.Game.HONKAI
    else:
        return genshin.Game.GENSHIN


class UserAccount(BaseModel):
    """User account"""

    uid: int
    """Genshin Impact UID"""
    hsr_uid: typing.Optional[int]
    """Honkai Star Rail UID"""
    user_id: int
    """Discord user ID"""

    ltuid: typing.Optional[str]
    """User account ltuid"""
    ltoken: typing.Optional[str]
    """User account ltoken"""
    cookie_token: typing.Optional[str]
    """User account cookie token"""
    client: genshin.Client
    """Genshin client object"""

    nickname: typing.Optional[str]
    """User account nickname"""
    current: bool = Field(default=True)
    """Whether this is the current account"""
    china: bool = Field(default=False)
    """Whether this is a China account"""

    last_checkin_date: typing.Optional[datetime.date] = Field(default=None)
    """Last daily check-in date"""

    lang: typing.Optional[str] = Field(default=None)
    """User language"""
    discord_user: typing.Optional[discord.User] = Field(default=None)
    """Discord user object"""

    daily_checkin: bool
    """Genshin daily check-in toggle"""
    honkai_daily: bool
    """Honkai Impact 3rd daily check-in toggle"""
    hsr_daily: bool
    """Honkai Star Rail daily check-in toggle"""
    checkin_game: GameType = Field(default=GameType.GENSHIN)
    """Internal attribute for daily check-in"""

    def __init__(self, **data: typing.Any):
        client = genshin.Client(
            uid=data["uid"],
            region=genshin.Region.CHINESE if data["china"] else genshin.Region.OVERSEAS,
        )
        if data["uid"]:
            client.uid = data["uid"]
        if data["ltuid"] and data["ltoken"] and data["cookie_token"]:
            cookies = {
                "ltuid": data["ltuid"],
                "ltoken": data["ltoken"],
                "cookie_token": data["cookie_token"],
                "account_id": data["ltuid"],
            }
            client.set_cookies(cookies)

        super().__init__(client=client, **data)

    async def fetch_lang(self, pool: asyncpg.Pool) -> typing.Optional[str]:
        lang = await pool.fetchval(
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

    class Config:
        arbitrary_types_allowed = True


class UserAccountTable:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_uid(self, user_id: int) -> int:
        uid = await self.pool.fetchval(
            "SELECT uid FROM user_accounts WHERE user_id = $1 AND current = True",
            user_id,
        )
        if uid is None:
            raise UIDNotFound
        return uid

    async def update(
        self, user_id: int, uid: typing.Optional[int] = None, **kwargs
    ) -> None:
        await self.pool.execute(
            "UPDATE user_accounts SET "
            + ", ".join(f"{key} = ${i}" for i, key in enumerate(kwargs, 3))
            + f" WHERE user_id = $1 AND uid = $2",
            user_id,
            uid or await self.get_uid(user_id),
            *kwargs.values(),
        )

    async def delete(self, user_id: int, uid: typing.Optional[int] = None) -> None:
        await self.pool.execute(
            "DELETE FROM user_accounts WHERE user_id = $1 AND uid = $2",
            user_id,
            uid or await self.get_uid(user_id),
        )

    async def get(
        self, user_id: int, uid: typing.Optional[int] = None, **kwargs
    ) -> UserAccount:
        kwargs["user_id"] = user_id
        kwargs["uid"] = uid or await self.get_uid(user_id)

        data = await self.pool.fetchrow(
            "SELECT * FROM user_accounts WHERE "
            + " AND ".join(f"{key} = ${i}" for i, key in enumerate(kwargs, 1)),
            *kwargs.values(),
        )
        if data is None:
            raise AccountNotFound
        return UserAccount(**dict(data))

    async def get_all(self, **kwargs) -> typing.List[UserAccount]:
        data = await self.pool.fetch(
            "SELECT * FROM user_accounts WHERE "
            + " AND ".join(f"{key} = ${i}" for i, key in enumerate(kwargs, 1)),
            *kwargs.values(),
        )
        return [UserAccount(**dict(d)) for d in data]
