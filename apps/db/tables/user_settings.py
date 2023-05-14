import typing
from enum import Enum

import asyncpg
from pydantic import BaseModel, Field

from dev.enum import GameType


class Settings(Enum):
    LANG = "lang"
    DARK_MODE = "dark_mode"
    NOTIFICATION = "notification"
    AUTO_REDEEM = "auto_redeem"
    PROFILE_VERSION = "profile_version"
    DEFAULT_GAME = "default_game"


class UserSettings(BaseModel):
    """User settings"""

    user_id: int
    """Discord user ID"""
    lang: typing.Optional[str] = Field(default=None)
    """Custom language"""
    dark_mode: bool = Field(default=False)
    """Dark mode toggle"""
    notification: bool = Field(default=True)
    """Notification toggle"""
    auto_redeem: bool = Field(default=False)
    """Auto redeem toggle"""
    profile_version: int = Field(default=2, alias="profile_ver")
    """Profile card version"""
    default_game: GameType = Field(default="genshin")
    """Default game"""


class UserSettingsTable:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def insert(self, user_id: int) -> None:
        """Insert user settings"""
        await self.pool.execute(
            "INSERT INTO user_settings (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
            user_id,
        )

    async def get(self, user_id: int, settings: Settings) -> typing.Any:
        """Get user settings"""
        val = await self.pool.fetchval(
            f"SELECT {settings.value} FROM user_settings WHERE user_id = $1", user_id
        )
        if val is None:
            await self.insert(user_id)
        
        if settings is Settings.DEFAULT_GAME:
            return GameType(val)
        return val

    async def get_all(self, user_id: int) -> UserSettings:
        """Get all user settings"""
        row = await self.pool.fetchrow(
            "SELECT * FROM user_settings WHERE user_id = $1", user_id
        )
        if row is None:
            await self.insert(user_id)
        return UserSettings(**row)
