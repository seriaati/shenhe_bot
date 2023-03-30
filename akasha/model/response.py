import typing

from pydantic import BaseModel, Field

V = typing.TypeVar("V")


class AkashaResponse(typing.Generic[V], BaseModel):
    """Base class for all Akasha responses"""

    ttl: int
    data: typing.List[V]
    total_row_hash: str = Field(..., alias="totalRowHash")
