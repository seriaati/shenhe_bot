from typing import List, Optional

import asyncpg
from pydantic import BaseModel, Field

from dev.enum import Category


class SingleStrikeCharacter(BaseModel):
    constellation: int = Field(alias="const")
    """Character constellation"""
    refinement: int = Field(alias="refine")
    """Weapon refinement"""
    level: int = Field(alias="c_level")
    """Character level"""
    icon: str = Field(alias="c_icon")
    """Character icon URL"""


class AbyssBoardEntry(BaseModel):
    """Abyss leaderboard entry"""

    uid: int
    """Genshin Impact UID"""
    user_id: int
    """Discord user ID"""

    season: int
    """Abyss season"""
    name: str = Field(alias="user_name")
    """Genshin Impact user name"""
    ar: int = Field(alias="level")
    """Adventure rank"""
    icon: str = Field(alias="icon_url")
    """User icon URL"""

    stars: int = Field(alias="stars_collected")
    """Number of abyss stars collected"""
    wins: int
    """Number of abyss wins"""
    runs: int
    """Number of abyss runs"""
    single_strike: int
    """Single strike damage"""
    floor: str
    """Deepest abyss floor reached"""
    character: SingleStrikeCharacter
    """Character used for single strike"""


class AbyssLeaderboard:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def insert(
        self,
        *,
        uid: int,
        user_id: int,
        season: int,
        name: str,
        ar: int,
        icon: str,
        stars: int,
        wins: int,
        runs: int,
        single_strike: int,
        floor: str,
        character: SingleStrikeCharacter
    ) -> None:
        """Insert abyss leaderboard entry"""
        await self.pool.execute(
            "INSERT INTO abyss_leaderboard (uid, user_id, season, user_name, level, icon_url, stars_collected, wins, runs, single_strike, floor, const, refine, c_level, c_icon) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::int, $13::int, $14::int, $15) ON CONFLICT DO NOTHING",
            uid,
            user_id,
            season,
            name,
            ar,
            icon,
            stars,
            wins,
            runs,
            single_strike,
            floor,
            character.constellation,
            character.refinement,
            character.level,
            character.icon,
        )

    async def get_all(
        self, category: Category, season: Optional[int] = None
    ) -> List[AbyssBoardEntry]:
        """Get abyss leaderboard entries"""
        order = "single_strike DESC" if category == Category.SINGLE_STRIKE else "runs ASC"
        if season is None:
            return [
                AbyssBoardEntry(**i)
                for i in await self.pool.fetch(f"SELECT * FROM abyss_leaderboard ORDER BY {order}")
            ]
        return [
            AbyssBoardEntry(**i)
            for i in await self.pool.fetch(
                f"SELECT * FROM abyss_leaderboard WHERE season = $1 ORDER BY {order}", season
            )
        ]
