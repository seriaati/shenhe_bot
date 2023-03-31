import typing

from pydantic import BaseModel

from ..enum import FilterType, OptionType, PageType


class Option(BaseModel):
    """Option model."""

    type: OptionType
    value: typing.Optional[typing.Any]
    option_name: str = ""


class Filter(Option):
    """Filter model."""

    type: FilterType
    value: str
    option_name: str = "filter"


class Page(Option):
    """Page model."""

    type: PageType
    value: typing.Optional[float]
    option_name: str = "p"
