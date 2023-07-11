from typing import List, Optional

from asyncpg import Pool
from pydantic import BaseModel, Field

from dev.enum import BoardCategory


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

    def __init__(self, **data):
        character = SingleStrikeCharacter(
            const=data["const"],
            refine=data["refine"],
            c_level=data["c_level"],
            c_icon=data["c_icon"],
        )
        super().__init__(**data, character=character)

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

    async def delete(self, uid: int, season: int) -> None:
        """
        Delete abyss leaderboard entry

        Args:
            uid (int): Genshin Impact UID
            season (int): Abyss season
        """
        await self.pool.execute(
            "DELETE FROM abyss_leaderboard WHERE uid = $1 AND season = $2",
            uid,
            season,
        )

    async def get_all(
        self, category: BoardCategory, season: Optional[int] = None
    ) -> List[AbyssBoardEntry]:
        """
        Get abyss leaderboard entries

        Args:
            category (Category): Abyss category
            season (int): Abyss season

        Returns:
            List[AbyssBoardEntry]: List of abyss leaderboard entries
        """
        order = (
            "single_strike DESC"
            if category == BoardCategory.SINGLE_STRIKE
            else "runs ASC"
        )
        if season is None:
            if category is BoardCategory.FULL_CLEAR:
                query = f"SELECT * FROM abyss_leaderboard WHERE stars_collected = 36 ORDER BY {order}"
            else:
                query = f"SELECT * FROM abyss_leaderboard ORDER BY {order}"
            return [AbyssBoardEntry(**i) for i in await self.pool.fetch(query)]

        if category is BoardCategory.FULL_CLEAR:
            query = f"SELECT * FROM abyss_leaderboard WHERE stars_collected = 36 AND season = $1 ORDER BY {order}"
        else:
            query = (
                f"SELECT * FROM abyss_leaderboard ORDER BY {order} WHERE season = $1 "
            )
        return [
            AbyssBoardEntry(**i)
            for i in await self.pool.fetch(
                query,
                season,
            )
        ]
