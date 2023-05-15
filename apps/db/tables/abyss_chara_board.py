import typing

import asyncpg
from pydantic import BaseModel, Field


class AbyssCharaBoardEntry(BaseModel):
    """Abyss character usage leaderboard entry"""

    uid: int
    """Genshin Impact UID"""
    season: int
    """Abyss season"""

    character_ids: typing.List[int] = Field(alias="characters")
    """Abyss character ID list"""
    user_id: int
    """Discord user ID"""


class AbyssCharacterLeaderboard:
    """Abyss character usage leaderboard"""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def insert(
        self, *, uid: int, season: int, character_ids: typing.List[int], user_id: int
    ) -> None:
        """Insert abyss character usage leaderboard entry"""
        await self.pool.execute(
            "INSERT INTO abyss_character_leaderboard (uid, season, characters, user_id) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
            uid,
            season,
            character_ids,
            user_id,
        )

    async def get_all(
        self, season: typing.Optional[int] = None
    ) -> typing.List[AbyssCharaBoardEntry]:
        """Get abyss character usage leaderboard entries"""
        if season is None:
            return [
                AbyssCharaBoardEntry(**i)
                for i in await self.pool.fetch(
                    "SELECT * FROM abyss_character_leaderboard"
                )
            ]
        return [
            AbyssCharaBoardEntry(**i)
            for i in await self.pool.fetch(
                "SELECT * FROM abyss_character_leaderboard WHERE season = $1", season
            )
        ]
