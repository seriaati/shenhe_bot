from asyncpg import Pool
from pydantic import BaseModel


class Cookie(BaseModel):
    """Cookie"""

    ltuid: int
    ltoken: str
    cookie_token: str


class CookieTable:
    """Cookie Table"""

    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    async def create(self) -> None:
        """Create the table"""
        await self.pool.execute(
            """
            CREATE TABLE IF NOT EXISTS cookies (
                ltuid BIGINT NOT NULL PRIMARY KEY,
                ltoken TEXT NOT NULL,
                cookie_token TEXT NOT NULL
            )
            """
        )

    async def insert(self, cookie: Cookie) -> None:
        """Insert a new cookie or update if exists"""
        await self.pool.execute(
            """
            INSERT INTO cookies (ltuid, ltoken, cookie_token)
            VALUES ($1, $2, $3)
            ON CONFLICT (ltuid)
            DO UPDATE SET ltoken = $2, cookie_token = $3
            """,
            cookie.ltuid,
            cookie.ltoken,
            cookie.cookie_token,
        )

    async def get(self, ltuid: int) -> Cookie:
        """Get a cookie"""
        row = await self.pool.fetchrow(
            """
            SELECT * FROM cookies WHERE ltuid = $1
            """,
            ltuid,
        )
        return Cookie(**row)

    async def update(self, cookie: Cookie) -> None:
        """Update a cookie"""
        await self.pool.execute(
            """
            UPDATE cookies SET ltoken = $2, cookie_token = $3 WHERE ltuid = $1
            """,
            cookie.ltuid,
            cookie.ltoken,
            cookie.cookie_token,
        )

    async def delete(self, ltuid: int) -> None:
        """Delete a cookie"""
        await self.pool.execute(
            """
            DELETE FROM cookies WHERE ltuid = $1
            """,
            ltuid,
        )
