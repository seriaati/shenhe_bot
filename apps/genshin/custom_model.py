import io
from pydantic import BaseModel
import discord
import genshin

class ShenheUser(BaseModel):
    client: genshin.Client
    uid: int | None
    discord_user: discord.User | discord.Member
    user_locale: str | None
    china: bool
    
    class Config:
        arbitrary_types_allowed = True

class DamageResult(BaseModel):
    result_embed: discord.Embed
    cond_embed: discord.Embed | None
    log_file: io.StringIO | None