from asyncpg import Pool
from pydantic import BaseModel


class RedeemedCode(BaseModel):
    uid: int
    code: str


class RedeemedCodeTable:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def insert(self, uid: int, code: str) -> None:
        await self.pool.execute(
            "INSERT INTO redeem_codes (uid, code) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            uid,
            code,
        )

    async def check(self, uid: int, code: str) -> bool:
        return await self.pool.fetchval(
            "SELECT EXISTS(SELECT 1 FROM redeem_codes WHERE uid = $1 AND code = $2)",
            uid,
            code,
        )
