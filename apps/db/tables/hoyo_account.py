import datetime
from typing import Optional

from asyncpg import Pool
from discord import User
from genshin import Client, Game, Region
from pydantic import BaseModel, Field

from apps.text_map.convert_locale import to_genshin_py
from dev.enum import GameType
from dev.exceptions import AccountNotFound
from utils.general import get_dc_user

from .cookies import Cookie, CookieTable
from .user_settings import UserSettings, UserSettingsTable


def convert_game_type(game_type: GameType) -> Game:
    if game_type is GameType.HSR:
        return Game.STARRAIL
    if game_type is GameType.HONKAI:
        return Game.HONKAI
    return Game.GENSHIN


class HoyoAccount(BaseModel):
    """Hoyoverse Account"""

    user_id: int
    """Discord User ID"""
    uid: int
    """Game UID"""
    current: bool
    """Is this the current account?"""
    game: GameType
    """Game type"""
    ltuid: int
    """Hoyoverse account ID"""
    nickname: Optional[str]
    """Account nickname"""

    genshin_daily: bool
    """Genshin Impact daily check-in toggle"""
    hsr_daily: bool
    """Honkai Star Rail daily check-in toggle"""
    honkai_daily: bool
    """Honkai Impact 3rd daily check-in toggle"""
    last_checkin: Optional[datetime.datetime] = None
    """Last daily check-in date"""
    checkin_game: GameType = Field(GameType.GENSHIN)
    """Last daily check-in game"""

    china: bool
    """Whether the account's region is in China"""

    _settings_db: UserSettingsTable
    """User settings database"""
    _cookie_db: CookieTable
    """Cookie database"""

    _cookie: Optional[Cookie] = None
    """Hoyoverse cookie"""
    _client: Optional[Client] = None
    """Genshin.py client"""
    _settings: Optional[UserSettings] = None
    """User settings"""

    def __init__(self, **kwargs) -> None:
        china = str(kwargs["uid"])[0] in (1, 2, 5)
        super().__init__(china=china, **kwargs)

    @property
    async def cookie(self) -> Cookie:
        if not self._cookie:
            cookie = await self._cookie_db.get(self.ltuid)
            self._cookie = cookie
        return self._cookie

    @property
    async def client(self) -> Client:
        """Get the genshin.py client"""
        if not self._client:
            cookie = await self.cookie
            self._client = self._create_client(cookie)
        return self._client

    @property
    async def settings(self) -> UserSettings:
        """Get the user settings"""
        if not self._settings:
            self._settings = await self._settings_db.get_all(self.user_id)
        if self._client:
            self._client.lang = to_genshin_py(str(self._settings.lang))
        return self._settings

    def _create_client(self, cookie: Cookie) -> Client:
        """Create a genshin.py client"""
        client = Client()
        client.set_cookies(
            {
                "ltuid": cookie.ltuid,
                "ltoken": cookie.ltoken,
                "cookie_token": cookie.cookie_token,
                "account_id": self.ltuid,
            }
        )
        client.game = convert_game_type(self.game)
        client.region = Region.CHINESE if self.china else Region.OVERSEAS
        return client


class HoyoAccountTable:
    """Hoyoverse Account Table"""

    def __init__(
        self, pool: Pool, cookie_db: CookieTable, settings_db: UserSettingsTable
    ) -> None:
        self.pool = pool
        self.cookie_db = cookie_db
        self.settings_db = settings_db

    async def create(self) -> None:
        """Create the table"""
        await self.pool.execute(
            """
        CREATE TABLE IF NOT EXISTS hoyo_account (
            user_id BIGINT NOT NULL,
            uid INT NOT NULL,
            ltuid INT NOT NULL,
            current BOOLEAN NOT NULL,
            game TEXT NOT NULL,
            nickname TEXT,
            genshin_daily BOOLEAN NOT NULL DEFAULT FALSE,
            hsr_daily BOOLEAN NOT NULL DEFAULT FALSE,
            honkai_daily BOOLEAN NOT NULL DEFAULT FALSE,
            UNIQUE (user_id, uid),
        )
        """
        )

    async def insert(
        self,
        *,
        user_id: int,
        uid: int,
        ltuid: int,
        game: GameType,
        nickname: Optional[str] = None,
    ) -> None:
        """Insert a new account"""
        await self.pool.execute(
            """
            INSERT INTO hoyo_account (user_id, uid, ltuid, current, game, nickname)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            user_id,
            uid,
            ltuid,
            True,
            game.value,
            nickname,
        )

    async def delete(self, user_id: int, uid: int) -> None:
        """Delete an account"""
        await self.pool.execute(
            """
            DELETE FROM hoyo_account WHERE user_id = $1 AND uid = $2
            """,
            user_id,
            uid,
        )

    async def get_uid(self, user_id: int) -> int:
        """Get a user's UID"""
        uid = await self.pool.fetchval(
            """
            SELECT uid FROM hoyo_account WHERE user_id = $1 AND current = TRUE
            """,
            user_id,
        )
        if not uid:
            raise AccountNotFound
        return uid

    async def get(self, user_id: int) -> HoyoAccount:
        """Get a user's Hoyo account"""
        account = await self.pool.fetchrow(
            """
            SELECT * FROM hoyo_account WHERE user_id = $1 AND current = TRUE
            """,
            user_id,
        )
        if not account:
            raise AccountNotFound
        return HoyoAccount(
            _cookie_db=self.cookie_db,
            _settings_db=self.settings_db,
            **account,
        )

    async def get_all_of_user(self, user_id: int) -> list[HoyoAccount]:
        """Get all of a user's accounts"""
        accounts = await self.pool.fetch(
            """
            SELECT * FROM hoyo_account WHERE user_id = $1
            """,
            user_id,
        )
        return [
            HoyoAccount(
                _cookie_db=self.cookie_db,
                _settings_db=self.settings_db,
                **account,
            )
            for account in accounts
        ]

    async def get_all(self) -> list[HoyoAccount]:
        """Get all accounts"""
        accounts = await self.pool.fetch(
            """
            SELECT * FROM hoyo_account
            """
        )
        return [
            HoyoAccount(
                _cookie_db=self.cookie_db,
                _settings_db=self.settings_db,
                **account,
            )
            for account in accounts
        ]

    async def update_current(self, user_id: int, uid: int) -> None:
        """Update the current account"""
        await self.pool.execute(
            """
            UPDATE hoyo_account SET current = FALSE WHERE user_id = $1
            """,
            user_id,
        )
        await self.pool.execute(
            """
            UPDATE hoyo_account SET current = TRUE WHERE user_id = $1 AND uid = $2
            """,
            user_id,
            uid,
        )

    async def update(self, user_id: int, uid: Optional[int] = None, **kwargs) -> None:
        await self.pool.execute(
            "UPDATE hoyo_account SET "
            + ", ".join(f"{key} = ${i}" for i, key in enumerate(kwargs, 3))
            + " WHERE user_id = $1 AND uid = $2",
            user_id,
            uid or await self.get_uid(user_id),
            *kwargs.values(),
        )
