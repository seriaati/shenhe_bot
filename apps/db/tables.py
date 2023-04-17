import typing

from attr import define, field


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