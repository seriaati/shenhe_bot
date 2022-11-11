import aiohttp
import aiosqlite
from typing import Dict, List, Optional
from pydantic import BaseModel, validator
import discord
import genshin
from discord.ext import commands
from enkanetwork.model import EnkaNetworkResponse

class ShenheUser(BaseModel):
    client: genshin.Client
    uid: int | None
    discord_user: discord.User | discord.Member | discord.ClientUser
    user_locale: str | None
    china: bool
    daily_checkin: bool = True
    
    class Config:
        arbitrary_types_allowed = True

class DamageResult(BaseModel):
    result_embed: discord.Embed
    cond_embed: Optional[discord.Embed] = None
    
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

class WishData(BaseModel):
    title: str
    total_wishes: int
    pity: int
    four_star: int
    five_star: int
    recents: List[Dict[str, str|int]]

    
class Wish(BaseModel):
    time: str
    rarity: int
    name: str

class WishInfo(BaseModel):
    total: int
    newest_wish: Wish
    oldest_wish: Wish
    character_banner_num: int
    permanent_banner_num: int
    weapon_banner_num: int
    novice_banner_num: int

class ShenheBot(commands.Bot):
    genshin_client: genshin.Client
    session: aiohttp.ClientSession
    db: aiosqlite.Connection
    backup_db: aiosqlite.Connection
    debug: bool
    maintenance: bool = False
    maintenance_time: Optional[str] = ""

class TodoList:
    def __init__(self):
        self.dict: Dict[int, int] = {}
    
    def add_item(self, item: Dict[int, int]):
        key = list(item.keys())[0]
        value = list(item.values())[0]
        if key in self.dict:
            self.dict[key] += value
        else:
            self.dict[key] = value
    
    def remove_item(self, item: Dict[int, int]):
        key = list(item.keys())[0]
        value = list(item.values())[0]
        if key in self.dict:
            self.dict[key] -= value
            if self.dict[key] <= 0:
                self.dict.pop(key)
    
    def return_list(self) -> Dict[int, int]:
        return self.dict
    
class EnkaView(BaseModel):
    overview_embed: discord.Embed
    character_options: List[discord.SelectOption]
    character_id: str
    data: EnkaNetworkResponse
    eng_data: EnkaNetworkResponse
    member: discord.User | discord.Member
    locale: discord.Locale | str
    custom_image_url: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        
class UserCustomImage(BaseModel):
    url: str
    nickname: str
    character_id: str
    user_id: int
    current: bool
    
    @validator("current", pre=True, allow_reuse=True)
    def parse_current(cls, v):
        return True if v == 1 else False