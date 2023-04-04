import typing

from pydantic import BaseModel, Field, validator


class EnkaPlayerInfo(BaseModel):
    nickname: str
    level: int
    signature: typing.Optional[str] = None
    world_level: int = Field(alias="worldLevel")
    name_card_id: int = Field(alias="nameCardId")
    achievement_num: int = Field(alias="finishAchievementNum")
    abyss_floor: int = Field(alias="towerFloorIndex")
    abyss_chamber: int = Field(alias="towerLevelIndex")


class EnkaInfoResponse(BaseModel):
    player_info: EnkaPlayerInfo = Field(alias="playerInfo")
    uid: int
    ttl: int

    @validator("player_info", pre=True, always=True, allow_reuse=True)
    def parse_player_info(cls, v):
        return EnkaPlayerInfo(**v)

    @validator("uid", pre=True, always=True, allow_reuse=True)
    def parse_uid(cls, v):
        return int(v)
