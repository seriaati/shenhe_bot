import datetime
from typing import List, Optional

from asyncpg import Pool
from genshin.models import Wish
from pydantic import BaseModel, Field


class WishHistory(BaseModel):
    """Wish history"""

    wish_id: int
    """Wish ID in the game"""
    user_id: int
    """Discord user ID"""
    uid: Optional[int] = None
    """Game UID"""

    name: str = Field(alias="wish_name")
    """Wish name"""
    rarity: int = Field(alias="wish_rarity")
    """Wish rarity"""
    time: datetime.datetime = Field(alias="wish_time")
    """Wish time"""
    banner: int = Field(alias="wish_banner_type")
    """Wish banner type"""

    item_id: Optional[int] = None
    """Game item ID"""
    pity: Optional[int] = Field(alias="pity_pull", default=None)
    """Pity pull count"""

    @classmethod
    def from_genshin_wish(cls, wish: Wish, user_id: int) -> "WishHistory":
        """Create a WishHistory object from the Genshin wish object"""
        return cls(
            user_id=user_id,
            wish_id=wish.id,
            uid=wish.uid,
            wish_name=wish.name,
            wish_rarity=wish.rarity,
            wish_time=wish.time.replace(tzinfo=None),
            wish_banner_type=wish.banner_type.value,
        )

    def to_dict(self) -> dict:
        """Converts the wish object to a dictionary"""
        return {
            "wish_id": self.wish_id,
            "user_id": self.user_id,
            "uid": self.uid,
            "wish_name": self.name,
            "wish_rarity": self.rarity,
            "wish_time": self.time,
            "wish_banner_type": self.banner,
            "item_id": self.item_id,
            "pity_pull": self.pity,
        }


class WishHistoryTable:
    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    async def insert(self, history: WishHistory) -> None:
        await self.pool.execute(
            """
            INSERT INTO wish_history (
                wish_id, user_id, uid, wish_name, wish_rarity, wish_time,
                wish_banner_type, item_id, pity_pull
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9
            )
            ON CONFLICT (wish_id) DO NOTHING
            """,
            history.wish_id,
            history.user_id,
            history.uid,
            history.name,
            history.rarity,
            history.time,
            history.banner,
            history.item_id,
            history.pity,
        )

    async def check_linked(self, user_id: int) -> bool:
        first_check = await self.pool.fetchval(
            "SELECT EXISTS(SELECT 1 FROM wish_history WHERE user_id = $1)", user_id
        )
        if not first_check:
            return True
        second_check = await self.pool.fetchval(
            "SELECT EXISTS(SELECT 1 FROM wish_history WHERE user_id = $1 AND uid IS NOT NULL)",
            user_id,
        )
        return second_check

    async def get_with_uid(self, uid: int) -> List[WishHistory]:
        return [
            WishHistory(**data)
            for data in await self.pool.fetch(
                "SELECT * FROM wish_history WHERE uid = $1 ORDER BY wish_id DESC", uid
            )
        ]

    async def get_with_user_id(self, user_id: int) -> List[WishHistory]:
        return [
            WishHistory(**data)
            for data in await self.pool.fetch(
                "SELECT * FROM wish_history WHERE user_id = $1 ORDER BY wish_id DESC",
                user_id,
            )
        ]

    async def delete_with_uid(self, uid: int) -> None:
        await self.pool.execute(
            """
            DELETE FROM wish_history WHERE uid = $1
            """,
            uid,
        )

    async def delete_with_user_id(self, user_id: int) -> None:
        await self.pool.execute(
            """
            DELETE FROM wish_history WHERE user_id = $1
            """,
            user_id,
        )
