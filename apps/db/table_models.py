import datetime
import typing

from attr import define, field

from dev.enum import NotificationType


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
