from pydantic import BaseModel, validator

from ..enum import CharacterStat, TalentType


class PropMap(BaseModel):
    """Prop map model."""

    ascension: int
    level: int

    @validator("ascension", "level", pre=True, always=True, allow_reuse=True)
    def _validate(cls, v):
        return int(v["val"])


class TalentExtraLevel(BaseModel):
    talent_id: str
    extra_level: int


class Stat(BaseModel):
    """Stat model."""

    type: CharacterStat
    value: int


class Talent(BaseModel):
    """Talent model."""

    type: TalentType
    icon: str
    level: int
    id: int
    boosted: bool
