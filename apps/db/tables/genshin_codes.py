from typing import List

from asyncpg import Pool


class GenshinCodes:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def update_codes(self, codes: List[str]) -> None:
        await self.pool.execute("DELETE FROM genshin_codes")
        for code in codes:
            await self.pool.execute("INSERT INTO genshin_codes VALUES ($1)", code)

    async def get_all(self) -> List[str]:
        codes = await self.pool.fetch("SELECT * FROM genshin_codes")
        return [code["code"] for code in codes]
