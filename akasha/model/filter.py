from pydantic import BaseModel

from ..enum import FilterType


class Filter(BaseModel):
    """Filter model."""

    type: FilterType
    value: str
