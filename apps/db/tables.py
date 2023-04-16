import datetime
import typing

from sqlalchemy.orm import declared_attr
from sqlmodel import Field
from sqlmodel import SQLModel as _SQLModel

from utils import snake_case


class SQLModel(_SQLModel):
    """SQLModel base class"""

    @declared_attr
    def __tablename__(cls) -> str:
        return snake_case(cls.__name__)


class AbyssCharacterLeaderboard(SQLModel, table=True):
    """Abyss character usage leaderboard"""

    id: typing.Optional[int] = Field(default=None, primary_key=True)
    """Database ID"""
    user_id: int
    """Discord user ID"""

    uid: int = Field(unique=True)
    """Genshin Impact UID"""
    season: int = Field(unique=True)
    """Abyss season"""
    characters: typing.Optional[typing.List[int]] = Field(default_factory=list)
    """Character ID list"""


class AbyssLeaderboard(SQLModel, table=True):
    """Single strike damage leaderboard"""

    id: typing.Optional[int] = Field(default=None, primary_key=True)
    """Database ID"""
    user_id: int
    """Discord user ID"""

    uid: int = Field(unique=True)
    """Genshin Impact UID"""
    season: int = Field(unique=True)
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

    level: int = Field(alias="c_level")
    """Character level"""
    icon: str = Field(alias="c_icon")
    """Character icon URL"""
    constellation: int = Field(alias="const")
    """Character constellation level"""
    refinemenet: int = Field(alias="refine")
    """Weapon refinement level"""


class CustomImage(SQLModel, table=True):
    """Custom image for /profile command"""

    id: typing.Optional[int] = Field(default=None, primary_key=True)
    """Database ID"""
    user_id: int
    """Discord user ID"""

    character_id: int
    """Genshin Impact Character ID"""
    image_url: str
    """Image URL"""
    nickname: str
    """Image nickname"""
    current: bool = Field(default=True)
    """Current image"""
    from_shenhe: typing.Optional[bool] = Field(default=False)
    """Whether this image is provided by Shenhe"""


class EnkaCache(SQLModel, table=True):
    """Enka cache"""

    uid: int = Field(primary_key=True)
    """Genshin Impact UID"""
    data: typing.Optional[bytes]
    """Enka data"""
    en_data: typing.Optional[bytes]
    """English Enka data"""


class GenshinCodes(SQLModel, table=True):
    """Genshin Impact redeem codes"""

    id: typing.Optional[int] = Field(default=None, primary_key=True)
    """Database ID"""
    code: str
    """Redeem code"""


class Json(SQLModel, table=True):
    """JSON cache"""

    id: typing.Optional[int] = Field(default=None, primary_key=True)
    """Database ID"""
    file_name: str = Field(primary_key=True)
    """JSON file name"""
    file: str
    """JSON file"""


class NotifBase(SQLModel, table=True):
    """Notification base table"""

    id: typing.Optional[int] = Field(default=None, primary_key=True)
    """Database ID"""
    uid: int = Field(unique=True)
    """Genshin Impact UID"""
    user_id: int = Field(unique=True)
    """Discord user ID"""
    last_notif: typing.Optional[datetime.datetime]
    """Last notification time"""

    current: int = Field(default=0)
    max: int = Field(default=3)
    toggle: bool = Field(default=False)


class PotNotification(NotifBase):
    """Realm currency notification"""

    threshold: int = Field(default=2000)


class PtNotification(NotifBase):
    """Parametric transformer notification"""


class ResinNotification(NotifBase):
    """Resin notification"""

    threshold: int = Field(default=130)


class RedeemCodes(SQLModel, table=True):
    """Auto redeem code feature"""

    id: typing.Optional[int] = Field(default=None, primary_key=True)
    """Database ID"""
    uid: int = Field(primary_key=True)
    """Genshin Impact UID"""
    code: str
    """Redeem code"""


class WeaponTalentBase(SQLModel, table=True):
    """Weapon talent base table"""

    user_id: int = Field(primary_key=True)
    """Discord user ID"""
    toggle: bool = Field(default=False)
    """Reminder toggle"""


class TalentNotification(WeaponTalentBase):
    """Weapon notification"""

    characters: typing.Optional[typing.List[str]] = Field(
        default_factory=list, alias="item_list"
    )
    """Character list"""


class WeaponNotification(WeaponTalentBase):
    """Weapon notification"""

    weapons: typing.Optional[typing.List[str]] = Field(
        default_factory=list, alias="item_list"
    )
    """Weapon list"""


class Todo(SQLModel, table=True):
    """Todo list"""

    id: typing.Optional[int] = Field(default=None, primary_key=True)
    """Database ID"""
    user_id: int
    """Discord user ID"""
    item: str
    """Todo item ID (or name)"""
    current: int = Field(default=0, alias="count")
    """Todo item current count"""
    max: int
    """Todo item max count"""


class UserAccounts(SQLModel, table=True):
    """User accounts"""

    id: typing.Optional[int] = Field(default=None, primary_key=True)
    """Database ID"""
    uid: int = Field(unique=True)
    """Genshin Impact UID"""
    user_id: int = Field(unique=True)
    """Discord user ID"""

    ltuid: typing.Optional[str]
    """User account ltuid"""
    ltoken: typing.Optional[str]
    """User account ltoken"""
    cookie_token: typing.Optional[str]
    """User account cookie token"""

    nickname: typing.Optional[str]
    """User account nickname"""
    current: bool = Field(default=True)
    """Whether this is the current account"""
    china: bool = Field(default=False)
    """Whether this is a China account"""

    daily_checkin: bool = Field(default=True)
    """Daily check-in toggle"""
    last_checkin_date: typing.Optional[datetime.date]
    """Last daily check-in date"""


class UserSettings(SQLModel, table=True):
    """User settings"""

    user_id: int = Field(primary_key=True)
    """Discord user ID"""
    lang: typing.Optional[str] = Field(default=None)
    """Custom language"""
    dark_mode: bool = Field(default=False)
    """Dark mode toggle"""
    notification: bool = Field(default=True)
    """Notification toggle"""
    auto_redeem: bool = Field(default=False)
    """Auto redeem toggle"""
    profile_version: int = Field(default=2, alias="profile_ver")
    """Profile card version"""


class WishHistory(SQLModel, table=True):
    """Wish history"""

    id: int = Field(primary_key=True, alias="wish_id")
    """Wish ID"""
    user_id: int
    """Discord user ID"""
    uid: typing.Optional[int]
    """Genshin Impact UID"""

    name: str = Field(alias="wish_name")
    """Wish name"""
    rarity: int = Field(alias="wish_rarity")
    """Wish rarity"""
    time: datetime.datetime = Field(alias="wish_time")
    """Wish time"""
    banner: int = Field(alias="wish_banner_type")
    """Wish banner type"""

    item_id: typing.Optional[int]
    """ID of the wish item"""
    pity_pull: typing.Optional[int]
    """Pity pull count"""
