import typing

from pydantic import BaseModel, validator

from .build import Build

V = typing.TypeVar("V")


class AkashaResponse(typing.Generic[V], BaseModel):
    """Base class for all Akasha responses"""

    ttl: int
    data: typing.List[V]

    @validator("data", pre=True, always=True, allow_reuse=True)
    def _validate_data(cls, v):
        return [Build(**i) for i in v]
