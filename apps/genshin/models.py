import io
import typing

import discord
import genshin
from pydantic import BaseModel, Field

from dev.models import DrawInput, ErrorEmbed

__all__ = (
    "GenshinAppResult",
    "AbyssResult",
    "RealtimeNoteResult",
    "StatsResult",
    "AreaResult",
    "DiaryResult",
    "CharacterResult",
    "DiaryLogsResult",
)

V = typing.TypeVar("V")


class GenshinAppResult(typing.Generic[V], BaseModel):
    success: bool
    result: typing.Union[V, ErrorEmbed]

    class Config:
        arbitrary_types_allowed = True


class AbyssResult(BaseModel):
    embed_title: str = Field(alias="title")
    abyss: genshin.models.SpiralAbyss
    genshin_user: genshin.models.PartialGenshinUserStats = Field(alias="user")
    discord_user: discord.User | discord.Member | discord.ClientUser
    overview_embed: discord.Embed = Field(alias="overview")
    overview_file: io.BytesIO = Field(alias="overview_card")
    abyss_floors: typing.List[genshin.models.Floor] = Field(alias="floors")
    characters: typing.List[genshin.models.Character]
    uid: int

    class Config:
        arbitrary_types_allowed = True


class RealtimeNoteResult(BaseModel):
    embed: discord.Embed
    draw_input: DrawInput
    notes: genshin.models.Notes

    class Config:
        arbitrary_types_allowed = True


class StatsResult(BaseModel):
    embed: discord.Embed
    file: io.BytesIO

    class Config:
        arbitrary_types_allowed = True


class AreaResult(BaseModel):
    embed: discord.Embed
    file: io.BytesIO

    class Config:
        arbitrary_types_allowed = True


class DiaryResult(BaseModel):
    embed: discord.Embed
    file: io.BytesIO

    class Config:
        arbitrary_types_allowed = True


class CharacterResult(BaseModel):
    characters: typing.List[genshin.models.Character]


class DiaryLogsResult(BaseModel):
    primo_per_day: typing.Dict[int, int]
    before_adding: typing.Dict[int, int]
