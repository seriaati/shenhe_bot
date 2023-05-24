import asyncio
import json
from typing import Any, Dict, List

import aiofiles
import discord
import genshin
from discord import utils
from discord.ext import commands, tasks
from dotenv import load_dotenv

import ambr
import apps.genshin as genshin_app
import dev.models as models
from apps.genshin import auto_task
from dev.base_ui import capture_exception
from utils import convert_dict_to_zipped_json, fetch_cards, get_dt_now, log
from utils.general import get_dc_user

load_dotenv()


def schedule_error_handler(func):
    async def inner_function(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except Exception as e:  # skipcq: PYL-W0703
            bot = args[0].bot
            seria_id = 410036441129943050
            seria = bot.get_user(seria_id) or await bot.fetch_user(seria_id)
            await seria.send(f"[Schedule] Error in {func.__name__}: {type(e)}\n{e}")
            capture_exception(e)

    return inner_function


class Schedule(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: models.BotModel = bot
        self.debug = self.bot.debug
        if not self.debug:
            self.run_tasks.start()

    async def cog_unload(self) -> None:
        if not self.debug:
            self.run_tasks.cancel()

    loop_interval = 1

    @tasks.loop(minutes=loop_interval)
    async def run_tasks(self) -> None:
        """Run the tasks every loop_interval minutes"""
        now = get_dt_now()

        if now.minute < self.loop_interval:  # every hour
            asyncio.create_task(auto_task.RealtimeNotes(self.bot).start())
            asyncio.create_task(self.save_codes())

        if now.hour == 0 and now.minute < self.loop_interval:  # midnight
            asyncio.create_task(auto_task.DailyCheckin(self.bot).start())

        if now.hour == 1 and now.minute < self.loop_interval:  # 1am
            asyncio.create_task(self.update_shenhe_cache_and_data())
            if now.day in (3, 10, 18, 25):
                asyncio.create_task(self.generate_abyss_json())

        if now.hour in (4, 15, 21) and now.minute < self.loop_interval:  # 4am, 3pm, 9pm
            hour_dict = {
                4: 0,  # Asia
                15: -13,  # North America
                21: -7,  # Europe
            }
            asyncio.create_task(
                auto_task.WTNotifs(self.bot, hour_dict[now.hour]).exec()
            )

        if now.hour == 10 and now.minute < self.loop_interval:  # 10am
            asyncio.create_task(auto_task.AutoRedeem(self.bot).exec())

    @schedule_error_handler
    async def update_shenhe_cache_and_data(self) -> None:
        await self.update_ambr_cache()
        await self.update_text_map()
        await self.update_game_data()
        await self.update_card_data()

    @schedule_error_handler
    async def save_codes(self) -> None:
        codes = await genshin_app.find_codes(self.bot.session)
        await self.bot.db.codes.update_codes(codes)

    @schedule_error_handler
    async def generate_abyss_json(self) -> None:
        log.info("[Schedule] Generating abyss.json...")

        result: Dict[str, Any] = {}
        result["schedule_id"] = genshin_app.get_current_abyss_season()
        result["size"] = 0
        result["data"] = []

        accounts = await self.bot.db.users.get_all()

        for account in accounts:
            if str(account.uid)[0] in (1, 2, 5):
                continue

            client = await account.client
            client.lang = "en-us"

            try:
                abyss = await client.get_genshin_spiral_abyss(account.uid)
                characters = await client.get_genshin_characters(account.uid)
            except Exception:  # skipcq: PYL-W0703
                pass
            else:
                if abyss.total_stars != 36:
                    continue

                genshin_app.add_abyss_entry(result, account, abyss, list(characters))
        log.info("[Schedule] Generated abyss.json")

        user = await get_dc_user(self.bot, 630235350526328844)
        fp = convert_dict_to_zipped_json(result)
        await user.send(file=discord.File(fp, "abyss_json.zip"))
        log.info("[Schedule] Saved abyss.json")

    @schedule_error_handler
    async def update_game_data(self):
        """Updates genshin game data and adds emojis"""
        log.info("[Schedule][Update Game Data] Start")
        await genshin.utility.update_characters_ambr()
        client = ambr.AmbrTopAPI(self.bot.session, "cht")
        eng_client = ambr.AmbrTopAPI(self.bot.session, "en")
        things_to_update = ["character", "weapon", "artifact"]
        with open("data/game/character_map.json", "r", encoding="utf-8") as f:
            character_map = json.load(f)
        character_map["10000005"] = {
            "name": "旅行者",
            "element": "Anemo",
            "rarity": 5,
            "icon": "https://api.ambr.top/assets/UI/UI_AvatarIcon_PlayerBoy.png",
            "eng": "Traveler",
            "emoji": str(utils.find(lambda e: e.name == "10000005", self.bot.emojis)),
        }
        character_map["10000007"] = character_map["10000005"]
        character_map["10000007"]["emoji"] = str(
            utils.find(lambda e: e.name == "10000007", self.bot.emojis)
        )
        with open("data/game/character_map.json", "w+", encoding="utf-8") as f:
            json.dump(character_map, f, ensure_ascii=False, indent=4)

        for thing in things_to_update:
            objects = None
            if thing == "character":
                objects = await client.get_character()
            elif thing == "weapon":
                objects = await client.get_weapon()
            elif thing == "artifact":
                objects = await client.get_artifact()

            if not isinstance(objects, List) or objects is None:
                continue
            try:
                with open(f"data/game/{thing}_map.json", "r", encoding="utf-8") as f:
                    object_map = json.load(f)
            except FileNotFoundError:
                object_map = {}

            for obj in objects:
                english_name = ""
                if isinstance(obj, ambr.Character):
                    object_map[str(obj.id)] = {
                        "name": obj.name,
                        "element": obj.element,
                        "rarity": obj.rairty,
                        "icon": obj.icon,
                    }
                    eng_object = await eng_client.get_character(obj.id)
                    if (
                        isinstance(eng_object, ambr.Character)
                        and eng_object is not None
                    ):
                        english_name = eng_object.name
                elif isinstance(obj, ambr.Weapon):
                    object_map[str(obj.id)] = {
                        "name": obj.name,
                        "rarity": obj.rarity,
                        "icon": obj.icon,
                    }
                    eng_object = await eng_client.get_weapon(obj.id)
                    if isinstance(eng_object, ambr.Weapon) and eng_object is not None:
                        english_name = eng_object.name
                elif isinstance(obj, ambr.Artifact):
                    object_map[str(obj.id)] = {
                        "name": obj.name,
                        "rarity": obj.rarity_list,
                        "icon": obj.icon,
                    }
                    eng_object = await eng_client.get_artifact(obj.id)
                    if isinstance(eng_object, ambr.Artifact) and eng_object is not None:
                        english_name = eng_object.name

                object_map[str(obj.id)]["eng"] = english_name
                object_id = str(obj.id)
                if "-" in object_id:
                    object_id = (object_id.split("-"))[0]
                emoji = utils.get(self.bot.emojis, name=object_id)
                if emoji is None:
                    emoji_server = None
                    for guild in self.bot.guilds:
                        if (
                            "shenhe asset" in guild.name
                            and guild.me.guild_permissions.manage_emojis
                            and len(guild.emojis) < guild.emoji_limit
                        ):
                            emoji_server = guild
                            break
                    if emoji_server is not None:
                        try:
                            async with self.bot.session.get(obj.icon) as r:
                                bytes_obj = await r.read()
                            emoji = await emoji_server.create_custom_emoji(
                                name=object_id,
                                image=bytes_obj,
                            )
                        except discord.HTTPException as e:
                            log.warning(
                                f"[Schedule] Emoji creation failed [Object]{obj}"
                            )
                            capture_exception(e)
                        else:
                            object_map[str(obj.id)]["emoji"] = str(emoji)
                else:
                    object_map[str(obj.id)]["emoji"] = str(emoji)
            with open(f"data/game/{thing}_map.json", "w+", encoding="utf-8") as f:
                json.dump(object_map, f, ensure_ascii=False, indent=4)
        log.info("[Schedule][Update Game Data] Ended")

    @schedule_error_handler
    async def update_text_map(self):
        """Updates genshin text map"""
        log.info("[Schedule][Update Text Map] Start")

        things_to_update = (
            "avatar",
            "weapon",
            "material",
            "reliquary",
            "food",
            "book",
            "furniture",
            "monster",
            "namecard",
        )
        for thing in things_to_update:
            await genshin_app.update_thing_text_map(thing, self.bot.session)

        # daily dungeon text map
        await genshin_app.update_dungeon_text_map(self.bot.session)

        # item name text map
        await genshin_app.update_item_text_map(things_to_update)

        log.info("[Schedule][Update Text Map] Ended")

    @schedule_error_handler
    async def update_card_data(self):
        log.info("[Schedule][Update Card Data] Start")

        cards = await fetch_cards(self.bot.session)
        for lang, card_data in cards.items():
            async with aiofiles.open(
                f"data/cards/card_data_{lang}.json", "w+", encoding="utf-8"
            ) as f:
                await f.write(json.dumps(card_data, indent=4, ensure_ascii=False))

        log.info("[Schedule][Update Card Data] Ended")

    @schedule_error_handler
    async def update_ambr_cache(self):
        """Updates data from ambr.top"""
        log.info("[Schedule][Update Ambr Cache] Start")
        client = ambr.AmbrTopAPI(self.bot.session)
        await client.update_cache(all_lang=True)
        await client.update_cache(static=True)
        log.info("[Schedule][Update Ambr Cache] Ended")

    @run_tasks.before_loop
    async def before_run_tasks(self):
        await self.bot.wait_until_ready()

    @commands.is_owner()
    @commands.command(name="update-data")
    async def update_data(self, ctx: commands.Context):
        message = await ctx.send("Updating data...")
        await asyncio.create_task(self.update_ambr_cache())
        await asyncio.create_task(self.update_text_map())
        await asyncio.create_task(self.update_game_data())
        await asyncio.create_task(self.update_card_data())
        await message.edit(content="Data updated")

    @commands.is_owner()
    @commands.command(name="run-func")
    async def run_func(self, ctx: commands.Context, func_name: str, *args):
        func = getattr(self, func_name)
        if not func:
            return await ctx.send("Function not found")
        message = await ctx.send(f"Function {func_name} ran")
        await asyncio.create_task(func(*args))
        await message.edit(content=f"Function {func_name} ended")


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(Schedule(bot))
