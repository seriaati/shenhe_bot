import typing

from pydantic import BaseModel, Field, validator

from .artifact import AritfactObject, AritfactSet
from .character import PropMap, Stat, Talent, TalentExtraLevel
from .player import Player
from .weapon import Weapon


class Build(BaseModel):
    """Build model."""

    id: str = Field(..., alias="_id")
    owner: Player
    uid: str
    profile_picture: str = Field(..., alias="profilePictureLink")
    name_card: str = Field(..., alias="nameCardLink")

    name: str
    icon: str
    character_id: int = Field(..., alias="characterId")
    artifact_objects: typing.List[AritfactObject] = Field(..., alias="artifactObjects")
    artifact_sets: typing.List[AritfactSet] = Field(..., alias="artifactSets")
    constellation: int
    prop_map: PropMap
    talent_extra_level: typing.List[TalentExtraLevel] = Field(
        ..., alias="proudSkillExtraLevelMap"
    )
    stats: typing.List[Stat]
    talents: typing.List[Talent]
    weapon: Weapon
    costume_id: str = Field(..., alias="costumeId")
    crit_value: int = Field(..., alias="critValue")

    index: int
    md5: str
    type: str

    @validator("owner", pre=True, always=True, allow_reuse=True)
    def _validate_owner(cls, v):
        return Player(**v)

    @validator("artifact_objects", pre=True, always=True, allow_reuse=True)
    def _validate_artifact_objects(cls, v):
        return [AritfactObject(type=key, **i) for key, i in v.items()]

    @validator("artifact_sets", pre=True, always=True, allow_reuse=True)
    def _validate_artifact_sets(cls, v):
        return [AritfactSet(name=key, **i) for key, i in v.items()]

    @validator("prop_map", pre=True, always=True, allow_reuse=True)
    def _validate_prop_map(cls, v):
        return PropMap(ascension=v["ascension"], level=v["level"])

    @validator("talent_extra_level", pre=True, always=True, allow_reuse=True)
    def _validate_talent_extra_level(cls, v):
        return [TalentExtraLevel(talent_id=key, extra_level=i) for key, i in v.items()]

    @validator("stats", pre=True, always=True, allow_reuse=True)
    def _validate_stats(cls, v):
        return [Stat(type=key, **i) for key, i in v.items()]

    @validator("talents", pre=True, always=True, allow_reuse=True)
    def _validate_talents(cls, v):
        return [Talent(type=key, **i) for key, i in v.items()]

    @validator("weapon", pre=True, always=True, allow_reuse=True)
    def _validate_weapon(cls, v):
        return Weapon(**v)
