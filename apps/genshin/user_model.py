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