import io
from typing import Optional
from pydantic import BaseModel, validator
import discord
import genshin

class ShenheUser(BaseModel):
    client: genshin.Client
    uid: int | None
    discord_user: discord.User | discord.Member | discord.ClientUser
    user_locale: str | None
    china: bool
    daily_checkin: bool
    
    class Config:
        arbitrary_types_allowed = True

class DamageResult(BaseModel):
    result_embed: discord.Embed
    cond_embed: discord.Embed | None
    log_file: io.StringIO | None
    
    class Config:
        arbitrary_types_allowed = True

class NotificationUser(BaseModel):
    user_id: int
    threshold: int
    current: int
    max: int
    uid: Optional[int]
    last_notif_time: Optional[str]
    shenhe_user: Optional[ShenheUser] = None