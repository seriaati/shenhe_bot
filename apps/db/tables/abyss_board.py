from typing import List, Optional

from asyncpg import Pool
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
    def __init__(self, **data):
        character = SingleStrikeCharacter(
            const=data["const"],
            refine=data["refine"],
            c_level=data["c_level"],
            c_icon=data["c_icon"],
        )
        super().__init__(**data, character=character)

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


class AbyssBoard:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_all(
        self, category: Category, season: Optional[int] = None
    ) -> List[AbyssBoardEntry]:
        """Get abyss leaderboard entries"""
        order = (
            "single_strike DESC" if category == Category.SINGLE_STRIKE else "runs ASC"
        )
        if season is None:
            return [
                AbyssBoardEntry(**i)
                for i in await self.pool.fetch(
                    f"SELECT * FROM abyss_leaderboard ORDER BY {order}"
                )
            ]
        return [
            AbyssBoardEntry(**i)
            for i in await self.pool.fetch(
                f"SELECT * FROM abyss_leaderboard WHERE season = $1 ORDER BY {order}",
                season,
            )
        ]
