import typing
from typing import List

from asyncpg import Pool, Record
from pydantic import BaseModel, Field

from dev.enum import NotifType


class WTNotifBase(BaseModel):
    user_id: int
    """Discord user ID"""
    toggle: bool = Field(default=False)
    """Notification toggle"""
    item_list: List[str] = Field(default=[])
    """List of item IDs"""
    type: NotifType
    """Notification type"""


class WeaponNotif(WTNotifBase):
    type: NotifType = Field(default=NotifType.WEAPON)


class TalentNotif(WTNotifBase):
    type: NotifType = Field(default=NotifType.TALENT)


class WTNotifTable:
    def __init__(self, pool: Pool, notif_type: NotifType):
        self.pool = pool
        self.notif_type = notif_type

    async def alter(self) -> None:
        await self.pool.execute(
            f"""
            ALTER TABLE public.{self.notif_type.value}
            ADD COLUMN IF NOT EXISTS game text NOT NULL DEFAULT 'genshin'
            """
        )

    async def insert(self, user_id: int) -> None:
        await self.pool.execute(
            f"""
            INSERT INTO {self.notif_type.value} (user_id, item_list)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id,
            [],
        )

    async def update(self, user_id: int, **kwargs) -> None:
        await self.pool.execute(
            f"UPDATE {self.notif_type.value} SET "
            + ", ".join(f"{key} = ${i}" for i, key in enumerate(kwargs, 2))
            + " WHERE user_id = $1",
            user_id,
            *kwargs.values(),
        )

    async def get(self, user_id: int) -> Record:
        """Get user notification data"""
        row = await self.pool.fetchrow(
            f"SELECT * FROM {self.notif_type.value} WHERE user_id = $1",
            user_id,
        )
        return row

    async def get_all(self) -> typing.List[Record]:
        """Get all notification users with toggle on"""
        rows = await self.pool.fetch(
            f"SELECT * FROM {self.notif_type.value} WHERE toggle = true"
        )
        return rows


class WeaponNotifTable(WTNotifTable):
    def __init__(self, pool: Pool):
        super().__init__(pool, NotifType.WEAPON)

    async def get(self, user_id: int) -> WeaponNotif:
        return WeaponNotif(**await super().get(user_id))

    async def get_all(self) -> typing.List[WeaponNotif]:
        return [WeaponNotif(**i) for i in await super().get_all()]


class TalentNotifTable(WTNotifTable):
    def __init__(self, pool: Pool):
        super().__init__(pool, NotifType.TALENT)

    async def get(self, user_id: int) -> TalentNotif:
        return TalentNotif(**await super().get(user_id))

    async def get_all(self) -> typing.List[TalentNotif]:
        return [TalentNotif(**i) for i in await super().get_all()]
