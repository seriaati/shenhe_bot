import typing
from datetime import datetime

from pydantic import BaseModel

from apps.db.tables.wish_history import WishHistory


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
