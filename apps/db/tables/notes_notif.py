import datetime
import typing

from asyncpg import Pool, Record
from pydantic import BaseModel, Field

from dev.enum import GameType, NotifType


class NotifBase(BaseModel):
    """Notification base table"""

    uid: int
    """Genshin Impact UID"""
    user_id: int
    """Discord user ID"""
    last_notif: typing.Optional[datetime.datetime] = Field(default=None)
    """Last notification time"""

    type: NotifType
    """Notification type"""
    current: int = Field(default=0)
    """Current notification count"""
    max: int = Field(default=3)
    """Maximum notification count"""
    toggle: bool = Field(default=False)
    """Notification toggle"""
    game: GameType = Field(default=GameType.GENSHIN)
    """Game type"""


class PotNotif(NotifBase):
    """Realm currency notification"""

    type: NotifType = Field(default=NotifType.POT)
    """Notification type"""
    threshold: int = Field(default=2000)
    """Realm currency threshold"""


class PTNotif(NotifBase):
    """Parametric transformer notification"""

    type: NotifType = Field(default=NotifType.PT)
    """Notification type"""
    hour_before: float = 1.0
    """Notify x hour before PT is available"""


class ResinNotif(NotifBase):
    """Resin notification"""

    type: NotifType = Field(default=NotifType.RESIN)
    """Notification type"""
    threshold: int = Field(default=130)
    """Resin threshold"""


class ExpedNotif(NotifBase):
    """Expedition notification"""

    type: NotifType = Field(default=NotifType.EXPED)
    """Notification type"""
    hour_before: float = 1.0
    """Notify x hour before expedition ends"""


class NotifTable:
    def __init__(self, pool: Pool, notif_type: NotifType):
        self.pool = pool
        self.notif_type = notif_type

    async def alter(self) -> None:
        await self.pool.execute(
            """
            ALTER TABLE public.notif_base
            ADD COLUMN IF NOT EXISTS game text NOT NULL DEFAULT 'genshin'
            """
        )
        await self.pool.execute(
            f"""
            ALTER TABLE public.{self.notif_type.value}
            ADD COLUMN IF NOT EXISTS game text NOT NULL DEFAULT 'genshin'
            """
        )

    async def insert(self, user_id: int, uid: int, game: GameType) -> None:
        """Insert user notification data"""
        await self.pool.execute(
            f"INSERT INTO {self.notif_type.value} (user_id, uid, game) VALUES ($1, $2, $3) ON CONFLICT (user_id, uid) DO NOTHING",
            user_id,
            uid,
            game.value,
        )

    async def update(self, user_id: int, uid: int, **kwargs: typing.Any) -> None:
        """Update user notification data"""
        await self.pool.execute(
            f"UPDATE {self.notif_type.value} SET "
            + ", ".join(f"{key} = ${i}" for i, key in enumerate(kwargs, 3))
            + " WHERE user_id = $1 AND uid = $2",
            user_id,
            uid,
            *kwargs.values(),
        )

    async def get(self, user_id: int, uid: int) -> Record:
        """Get user notification data"""
        row = await self.pool.fetchrow(
            f"SELECT * FROM {self.notif_type.value} WHERE user_id = $1 AND uid = $2",
            user_id,
            uid,
        )
        return row

    async def get_all(self) -> typing.List[Record]:
        """Get users of a notification type that has the toggle on"""
        rows = await self.pool.fetch(
            f"SELECT * FROM {self.notif_type.value} WHERE toggle = true ORDER BY uid"
        )
        return rows


class ResinNotifTable(NotifTable):
    def __init__(self, pool: Pool):
        super().__init__(pool, NotifType.RESIN)

    async def get(self, user_id: int, uid: int) -> ResinNotif:
        return ResinNotif(**await super().get(user_id, uid))

    async def get_all(self) -> typing.List[ResinNotif]:
        return [ResinNotif(**i) for i in await super().get_all()]


class PotNotifTable(NotifTable):
    def __init__(self, pool: Pool):
        super().__init__(pool, NotifType.POT)

    async def get(self, user_id: int, uid: int) -> PotNotif:
        return PotNotif(**await super().get(user_id, uid))

    async def get_all(self) -> typing.List[PotNotif]:
        return [PotNotif(**i) for i in await super().get_all()]


class PTNotifTable(NotifTable):
    def __init__(self, pool: Pool):
        super().__init__(pool, NotifType.PT)

    async def alter(self) -> None:
        await super().alter()
        await self.pool.execute(
            """
            ALTER TABLE public.pt_notification
            ADD COLUMN IF NOT EXISTS hour_before REAL NOT NULL DEFAULT 1.0
            """
        )

    async def get(self, user_id: int, uid: int) -> PTNotif:
        return PTNotif(**await super().get(user_id, uid))

    async def get_all(self) -> typing.List[PTNotif]:
        return [PTNotif(**i) for i in await super().get_all()]


class ExpedNotifTable(NotifTable):
    def __init__(self, pool: Pool):
        super().__init__(pool, NotifType.EXPED)

    async def create(self) -> None:
        await self.pool.execute(
            """
            CREATE TABLE IF NOT EXISTS public.exped_notif (
                hour_before REAL NOT NULL DEFAULT 1.0,
                CONSTRAINT exped_notif_uid_user_id_key UNIQUE (uid, user_id)
            )
            INHERITS (public.notif_base)
            """
        )

    async def get(self, user_id: int, uid: int) -> ExpedNotif:
        return ExpedNotif(**await super().get(user_id, uid))

    async def get_all(self) -> typing.List[ExpedNotif]:
        return [ExpedNotif(**i) for i in await super().get_all()]
