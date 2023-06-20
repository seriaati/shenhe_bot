from typing import Dict, List

from discord import Forbidden, Guild

from dev.models import BotModel
from utils.general import open_json, write_json
from yatta import YattaAPI


class DataUpdater:
    """
    Update data for Star Rail.
    """

    def __init__(self, bot: BotModel):
        self.bot = bot
        self.emoji_map: Dict[str, str] = open_json("data/star_rail/emoji_map.json")
        self.url_map: Dict[str, str] = {}
        self.guilds: List[Guild] = []

    async def start(self) -> None:
        """
        Start data update process.
        """
        self.guilds = await self.get_asset_guilds()
        await self.fetch_url_map()
        await self.upload_emojis()
        write_json("data/star_rail/emoji_map.json", self.emoji_map)

    async def fetch_url_map(self) -> None:
        """
        Fetch character icon url map from Yatta API.
        """
        yatta = YattaAPI()
        character_ids = await yatta.fetch_character_ids()
        url = "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/avatar"
        for character_id in character_ids:
            if str(character_id) not in self.emoji_map:
                self.url_map[str(character_id)] = f"{url}/{character_id}.png"

    async def get_asset_guilds(self) -> List[Guild]:
        """
        Get guilds with "shenhe asset" in their name
        and with emoji limit available.
        """
        return [
            g
            for g in self.bot.guilds
            if "shenhe asset" in g.name.lower() and g.emoji_limit - len(g.emojis) > 0
        ]

    async def upload_emojis(self) -> None:
        """
        Upload character icons as custom emojis.
        """
        guild = self.guilds[0]
        for item_id, url in self.url_map.items():
            async with self.bot.session.get(url) as resp:
                image = await resp.read()
            try:
                emoji = await guild.create_custom_emoji(name=item_id, image=image)
            except Forbidden:
                # emoji limit reached
                self.guilds.remove(guild)
                guild = self.guilds[0]
            else:
                self.emoji_map[item_id] = str(emoji)
