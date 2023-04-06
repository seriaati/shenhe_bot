import typing
from datetime import datetime

import asyncpg
import genshin
from pydantic import BaseModel


class WishHistory(BaseModel):
    id: int
    user_id: int
    uid: typing.Optional[int] = None

    name: str
    rarity: int
    time: datetime
    type: str
    banner: int

    item_id: typing.Optional[int] = None
    pity: typing.Optional[int] = None

    @staticmethod
    def from_row(row: asyncpg.Record) -> "WishHistory":
        return WishHistory(
            id=row["wish_id"],
            user_id=row["user_id"],
            uid=row["uid"],
            name=row["wish_name"],
            rarity=row["wish_rarity"],
            time=row["wish_time"],
            type=row["wish_type"],
            banner=row["wish_banner_type"],
            item_id=row["item_id"],
            pity=row["pity_pull"],
        )

    @staticmethod
    def from_genshin_wish(wish: genshin.models.Wish, user_id: int) -> "WishHistory":
        return WishHistory(
            id=wish.id,
            user_id=user_id,
            uid=wish.uid,
            name=wish.name,
            rarity=wish.rarity,
            time=wish.time,
            type=wish.type,
            banner=wish.banner_type.value,
        )

    def to_dict(self) -> dict:
        return {
            "wish_id": self.id,
            "user_id": self.user_id,
            "uid": self.uid,
            "wish_name": self.name,
            "wish_rarity": self.rarity,
            "wish_time": self.time,
            "wish_type": self.type,
            "wish_banner_type": self.banner,
            "item_id": self.item_id,
            "pity_pull": self.pity,
        }


class RecentWish(BaseModel):
    name: str
    pull_num: int
    icon: typing.Optional[str] = None


class WishItem(BaseModel):
    name: str
    banner: int
    rarity: int
    time: datetime


class WishData(BaseModel):
    title: str
    total_wishes: int
    pity: int
    four_star: int
    five_star: int
    recents: typing.List[RecentWish]


class WishInfo(BaseModel):
    total: int
    newest_wish: WishHistory
    oldest_wish: WishHistory
    character_banner_num: int
    permanent_banner_num: int
    weapon_banner_num: int
    novice_banner_num: int
