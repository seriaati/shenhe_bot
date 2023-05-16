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
