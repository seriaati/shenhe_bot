import typing
from enum import Enum

from asyncpg import Pool
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
    def __init__(self, pool: Pool):
        self.pool = pool

    async def insert(self, user_id: int) -> None:
        """Insert user settings"""
        await self.pool.execute(
            "INSERT INTO user_settings (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
            user_id,
        )

    async def update(self, user_id: int, settings: Settings, value: typing.Any) -> None:
        """Update user settings"""
        await self.pool.execute(
            f"UPDATE user_settings SET {settings.value} = $1 WHERE user_id = $2",
            value,
            user_id,
        )

    async def get(self, user_id: int, settings: Settings) -> typing.Any:
        """Get user settings"""
        val = await self.pool.fetchval(
            f"SELECT {settings.value} FROM user_settings WHERE user_id = $1", user_id
        )
        if val is None and settings is not Settings.LANG:
            await self.insert(user_id)
            val = await self.get(user_id, settings)

        if settings is Settings.DEFAULT_GAME:
            return GameType(val)
        return val
