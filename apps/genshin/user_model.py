from pydantic import BaseModel
import discord
import genshin

class ShenheUser(BaseModel):
    client: genshin.Client
    uid: int | None
    discord_user: discord.User
    user_locale: str | None
    is_cn: bool
    
    class Config:
        arbitrary_types_allowed = True