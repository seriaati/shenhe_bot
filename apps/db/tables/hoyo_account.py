import datetime
from typing import Optional

from asyncpg import Pool
from genshin import Client, Game, Region
from pydantic import BaseModel

from apps.text_map.convert_locale import to_genshin_py
from dev.enum import GameType
from dev.exceptions import AccountNotFound

from .cookies import Cookie, CookieTable
from .user_settings import UserSettings, UserSettingsTable


def convert_game_type(game_type: GameType) -> Game:
    if game_type is GameType.HSR:
        return Game.STARRAIL
    if game_type is GameType.HONKAI:
        return Game.HONKAI
    return Game.GENSHIN


def convert_game(game: Game) -> GameType:
    if game is Game.STARRAIL:
        return GameType.HSR
    if game is Game.HONKAI:
        return GameType.HONKAI
    return GameType.GENSHIN


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

    daily_checkin: bool
    """Daily check-in toggle"""
    last_checkin: Optional[datetime.datetime] = None
    """Last daily check-in date"""

    china: bool
    """Whether the account's region is in China"""

    settings_db: UserSettingsTable
    """User settings database"""
    cookie_db: CookieTable
    """Cookie database"""

    internal_cookie: Optional[Cookie]
    """Hoyoverse cookie"""
    internal_client: Optional[Client]
    """Genshin.py client"""
    internal_settings: Optional[UserSettings]
    """User settings"""

    def __init__(self, **kwargs) -> None:
        china = str(kwargs["uid"])[0] in (1, 2, 5)
        super().__init__(china=china, **kwargs)

    @property
    async def cookie(self) -> Cookie:
        if not self.internal_cookie:
            cookie = await self.cookie_db.get(self.ltuid)
            self.internal_cookie = cookie
        return self.internal_cookie

    @property
    async def client(self) -> Client:
        """Get the genshin.py client"""
        if not self.internal_client:
            cookie = await self.cookie
            self.internal_client = self._create_client(cookie)
        return self.internal_client

    @property
    async def settings(self) -> UserSettings:
        """Get the user settings"""
        if not self.internal_settings:
            self.internal_settings = await self.settings_db.get_all(self.user_id)
        if self.internal_client:
            self.internal_client.lang = to_genshin_py(str(self.internal_settings.lang))
        return self.internal_settings

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

    class Config:
        arbitrary_types_allowed = True
        allow_private = True


class HoyoAccountTable:
    """Hoyoverse Account Table"""

    def __init__(
        self, pool: Pool, cookie_db: CookieTable, settings_db: UserSettingsTable
    ) -> None:
        self.pool = pool
        self.cookie_db = cookie_db
        self.settings_db = settings_db

    async def alter(self) -> None:
        await self.pool.execute(
            "ALTER TABLE hoyo_account ADD COLUMN IF NOT EXISTS daily_checkin BOOLEAN DEFAULT FALSE"
        )
        try:
            users = await self.pool.fetch(
                "SELECT user_id FROM hoyo_account WHERE genshin_daily = TRUE or honkai_daily = TRUE or hsr_daily = TRUE"
            )
        except Exception:  # skipcq: PYL-W0703
            return
        for user in users:
            await self.pool.execute(
                "UPDATE hoyo_account SET daily_checkin = TRUE WHERE user_id = $1",
                user["user_id"],
            )
        await self.pool.execute(
            "ALTER TABLE hoyo_account DROP COLUMN IF EXISTS genshin_daily, DROP COLUMN IF EXISTS honkai_daily, DROP COLUMN IF EXISTS hsr_daily"
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
            ON CONFLICT DO NOTHING
            """,
            user_id,
            int(uid),
            int(ltuid),
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

    async def check_exist(self, ltuid: int) -> bool:
        """Check if an account exists"""
        return await self.pool.fetchval(
            """
            SELECT EXISTS(SELECT 1 FROM hoyo_account WHERE ltuid = $1)
            """,
            ltuid,
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

    async def get(self, user_id: int, uid: Optional[int] = None) -> HoyoAccount:
        """Get a user's Hoyo account"""
        if uid:
            account = await self.pool.fetchrow(
                """
                SELECT * FROM hoyo_account WHERE user_id = $1 AND uid = $2
                """,
                user_id,
                uid,
            )
        else:
            account = await self.pool.fetchrow(
                """
                SELECT * FROM hoyo_account WHERE user_id = $1 AND current = TRUE
                """,
                user_id,
            )
        if not account:
            raise AccountNotFound
        return HoyoAccount(
            cookie_db=self.cookie_db,
            settings_db=self.settings_db,
            **account,
        )

    async def get_all_of_user(self, user_id: int, game: Optional[GameType] = None) -> list[HoyoAccount]:
        """Get all of a user's accounts"""
        if game:
            accounts = await self.pool.fetch(
                """
                SELECT * FROM hoyo_account WHERE user_id = $1 AND game = $2
                ORDER BY uid ASC
                """,
                user_id,
                game.value,
            )
        else:
            accounts = await self.pool.fetch(
                """
                SELECT * FROM hoyo_account WHERE user_id = $1
                ORDER BY uid ASC
                """,
                user_id,
            )
        return [
            HoyoAccount(
                cookie_db=self.cookie_db,
                settings_db=self.settings_db,
                **account,
            )
            for account in accounts
        ]

    async def get_all(self) -> list[HoyoAccount]:
        """Get all accounts"""
        accounts = await self.pool.fetch(
            """
            SELECT * FROM hoyo_account
            ORDER BY user_id ASC, uid ASC
            """
        )
        return [
            HoyoAccount(
                cookie_db=self.cookie_db,
                settings_db=self.settings_db,
                **account,
            )
            for account in accounts
        ]
    

    async def get_total(self) -> int:
        """Get the total number of accounts"""
        return await self.pool.fetchval(
            """
            SELECT COUNT(*) FROM hoyo_account
            """
        )

    async def set_current(self, user_id: int, uid: int) -> None:
        """Set the current account"""
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
