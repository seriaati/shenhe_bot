import datetime
import typing

from attr import define, field

from dev.enum import NotificationType


@define
class AbyssCharacterLeaderboard:
    """Abyss character usage leaderboard"""

    user_id: int
    """Discord user ID"""

    uid: int
    """Genshin Impact UID"""
    season: int
    """Abyss season"""
    characters: typing.Optional[typing.List[int]] = field(default=None)
    """Character ID list"""


@define
class AbyssLeaderboard:
    """Single strike damage leaderboard"""

    user_id: int
    """Discord user ID"""

    uid: int
    """Genshin Impact UID"""
    season: int
    """Abyss season"""
    user_name: str
    """Genshin Impact user name"""
    level: int
    """Genshin Impact adventure rank"""
    icon_url: str
    """Genshin Impact user avatar URL"""

    floor: str
    """Abyss floor reached"""
    stars_collected: int
    """Total stars collected"""
    single_strike: int
    """Highest single strike damage"""
    runs: int
    """Total abyss runs"""
    wins: int
    """Total abyss wins"""

    character_level: int = field(alias="c_level")
    """Character level"""
    character_icon: str = field(alias="c_icon")
    """Character icon URL"""
    constellation: int = field(alias="const")
    """Character constellation level"""
    refinemenet: int = field(alias="refine")
    """Weapon refinement level"""


@define
class NotifBase:
    """Notification base table"""

    uid: int
    """Genshin Impact UID"""
    user_id: int
    """Discord user ID"""
    last_notif: typing.Optional[datetime.datetime]
    """Last notification time"""

    type: NotificationType
    """Notification type"""
    current: int = field(default=0)
    """Current notification count"""
    max: int = field(default=3)
    """Maximum notification count"""
    toggle: bool = field(default=False)
    """Notification toggle"""


@define
class PotNotification(NotifBase):
    """Realm currency notification"""

    type: NotificationType = field(default=NotificationType.POT)
    """Notification type"""
    threshold: int = field(default=2000)
    """Realm currency threshold"""


@define
class PtNotification(NotifBase):
    """Parametric transformer notification"""

    type: NotificationType = field(default=NotificationType.PT)
    """Notification type"""


@define
class ResinNotification(NotifBase):
    """Resin notification"""

    type: NotificationType = field(default=NotificationType.RESIN)
    """Notification type"""
    threshold: int = field(default=130)
    """Resin threshold"""
