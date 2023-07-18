from typing import Dict, List

from ambr_top import AmbrAPI
from ambr_top import Language as AmbrLanguage
from discord import Forbidden, Guild
from yatta import Language as YattaLanguage
from yatta import Message, YattaAPI

from dev.enum import GenshinWikiCategory, HSRWikiCategory
from dev.models import BotModel
from utils.general import open_json, write_json


class DataUpdater:
    def __init__(self, bot: BotModel):
        self.bot = bot
        self.hsr_emoji_map: Dict[str, str] = open_json("data/star_rail/emoji_map.json")
        self.url_map: Dict[str, str] = {}
        self.guilds: List[Guild] = []

    async def start(self) -> None:
        # await self.update_hsr_emojis()
        # await self.update_genshin_text_maps()
        await self.update_hsr_text_maps()

    async def update_hsr_emojis(self) -> None:
        self.guilds = await self.get_asset_guilds()
        await self.fetch_hsr_url_map()
        await self.upload_emojis()
        write_json("data/star_rail/emoji_map.json", self.hsr_emoji_map)

    async def fetch_hsr_url_map(self) -> None:
        yatta = YattaAPI()
        character_ids = [c.id for c in await yatta.fetch_characters()]
        url = "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/avatar"
        for character_id in character_ids:
            if str(character_id) not in self.hsr_emoji_map:
                self.url_map[str(character_id)] = f"{url}/{character_id}.png"

    async def get_asset_guilds(self) -> List[Guild]:
        return [
            g
            for g in self.bot.guilds
            if "shenhe asset" in g.name.lower() and g.emoji_limit - len(g.emojis) > 0
        ]

    async def upload_emojis(self) -> None:
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
                self.hsr_emoji_map[item_id] = str(emoji)

    async def update_genshin_text_maps(self) -> None:
        ambr = AmbrAPI()
        for category in GenshinWikiCategory:
            text_map: Dict[str, Dict[str, str]] = {}
            for lang in AmbrLanguage:
                text_map[lang.value] = {}
                ambr.lang = lang
                if category is GenshinWikiCategory.ARTIFACT:
                    data = await ambr.fetch_artiact_sets()
                elif category is GenshinWikiCategory.BOOK:
                    data = await ambr.fetch_books()
                elif category is GenshinWikiCategory.CHARACTER:
                    data = await ambr.fetch_characters()
                elif category is GenshinWikiCategory.FOOD:
                    data = await ambr.fetch_foods()
                elif category is GenshinWikiCategory.FURNITURE:
                    data = await ambr.fetch_furnitures()
                elif category is GenshinWikiCategory.MATERIAL:
                    data = await ambr.fetch_materials()
                elif category is GenshinWikiCategory.MONSTER:
                    data = await ambr.fetch_monsters()
                elif category is GenshinWikiCategory.WEAPON:
                    data = await ambr.fetch_weapons()
                elif category is GenshinWikiCategory.NAME_CARD:
                    data = await ambr.fetch_name_cards()
                elif category is GenshinWikiCategory.TCG:
                    data = await ambr.fetch_tcg_cards()
                else:
                    raise ValueError(f"Invalid category: {category}")

                for item in data:
                    text_map[lang.value][item.name] = str(item.id)

            write_json(f"data/genshin/text_maps/{category.value}.json", text_map)

    async def update_hsr_text_maps(self) -> None:
        yatta = YattaAPI()
        for category in HSRWikiCategory:
            text_map: Dict[str, Dict[str, int]] = {}
            for lang in YattaLanguage:
                text_map[lang.value] = {}
                yatta.lang = lang
                if category is HSRWikiCategory.CHARACTER:
                    data = await yatta.fetch_characters()
                elif category is HSRWikiCategory.LIGHT_CONE:
                    data = await yatta.fetch_light_cones()
                elif category is HSRWikiCategory.ITEM:
                    data = await yatta.fetch_items()
                elif category is HSRWikiCategory.MESSAGE:
                    data = await yatta.fetch_messages()
                elif category is HSRWikiCategory.RELIC:
                    data = await yatta.fetch_relics()
                elif category is HSRWikiCategory.BOOK:
                    data = await yatta.fetch_books()
                else:
                    raise ValueError(f"Invalid category: {category}")

                for item in data:
                    if isinstance(item, Message):
                        text_map[lang.value][item.contact.name] = item.id
                    else:
                        text_map[lang.value][item.name] = item.id
            write_json(f"data/star_rail/text_maps/{category.value}.json", text_map)
