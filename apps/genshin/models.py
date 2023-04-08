import io
import typing

import discord
import genshin
from attr import define, field

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


@define
class GenshinAppResult(typing.Generic[V]):
    success: bool
    result: typing.Union[V, ErrorEmbed]

    class Config:
        arbitrary_types_allowed = True


@define
class AbyssResult:
    embed_title: str = field(alias="title")
    abyss: genshin.models.SpiralAbyss
    genshin_user: genshin.models.PartialGenshinUserStats = field(alias="user")
    discord_user: discord.User | discord.Member | discord.ClientUser
    overview_embed: discord.Embed = field(alias="overview")
    overview_file: io.BytesIO = field(alias="overview_card")
    abyss_floors: typing.List[genshin.models.Floor] = field(alias="floors")
    characters: typing.List[genshin.models.Character]
    uid: int

    class Config:
        arbitrary_types_allowed = True


@define
class RealtimeNoteResult:
    embed: discord.Embed
    draw_input: DrawInput
    notes: genshin.models.Notes

    class Config:
        arbitrary_types_allowed = True


@define
class StatsResult:
    embed: discord.Embed
    file: io.BytesIO

    class Config:
        arbitrary_types_allowed = True


@define
class AreaResult:
    embed: discord.Embed
    file: io.BytesIO

    class Config:
        arbitrary_types_allowed = True


@define
class DiaryResult:
    embed: discord.Embed
    file: io.BytesIO

    class Config:
        arbitrary_types_allowed = True


@define
class CharacterResult:
    characters: typing.List[genshin.models.Character]


@define
class DiaryLogsResult:
    primo_per_day: typing.Dict[int, int]
    before_adding: typing.Dict[int, int]
