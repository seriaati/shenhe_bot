import ast
import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import List
import aiosqlite
import sentry_sdk
from ambr.client import AmbrTopAPI
from apps.genshin.custom_model import NotificationUser, ShenheUser
from apps.genshin.genshin_app import GenshinApp
from apps.genshin.utils import get_shenhe_user
from apps.text_map.convert_locale import to_ambr_top_dict
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from discord import File, Game, Interaction, app_commands
from discord.app_commands import locale_str as _
from discord.errors import HTTPException, Forbidden
from discord.ext import commands, tasks
from discord.utils import format_dt, sleep_until, find
from utility.utils import default_embed, error_embed, get_user_timezone, log
from yelan.draw import draw_talent_reminder_card
import genshin
from cogs.admin import is_seria
import pytz


def schedule_error_handler(func):
    async def inner_function(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except Exception as e:
            bot = args[0].bot
            seria = await bot.fetch_user(410036441129943050)
            await seria.send(f"[Schedule] Error in {func.__name__}: {e}")
            log.warning(f"[Schedule] Error in {func.__name__}: {e}")
            sentry_sdk.capture_exception(e)

    return inner_function


class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.genshin_app = GenshinApp(self.bot.db, self.bot)
        self.debug = self.bot.debug
        self.claim_reward.start()
        self.resin_notification.start()
        self.talent_notification.start()
        self.change_status.start()
        self.pot_notification.start()
        self.backup_database.start()
        self.update_game_data.start()
        self.update_text_map.start()
        self.update_ambr_cache.start()

    def cog_unload(self):
        self.claim_reward.cancel()
        self.resin_notification.cancel()
        self.talent_notification.cancel()
        self.change_status.cancel()
        self.pot_notification.cancel()
        self.backup_database.cancel()
        self.update_game_data.cancel()
        self.update_text_map.cancel()
        self.update_ambr_cache.cancel()

    @tasks.loop(minutes=10)
    async def change_status(self):
        status_list = [
            "/help",
            "shenhe.bot.nu",
        ]
        await self.bot.change_presence(
            activity=Game(
                name=f"{random.choice(status_list)} | {len(self.bot.guilds)} guilds"
            )
        )

    async def get_schedule_users(self) -> List[ShenheUser]:
        """Gets a list of shenhe users that have Cookie registered (ltuid is not None)

        Returns:
            List[ShenheUser]: List of shenhe users
        """
        result = []
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute(
            "SELECT ltuid, ltoken, user_id, uid FROM user_accounts WHERE ltuid IS NOT NULL"
        )
        users = await c.fetchall()
        for _, tpl in enumerate(users):
            ltuid = tpl[0]
            ltoken = tpl[1]
            user_id = tpl[2]
            shenhe_user = await get_shenhe_user(
                user_id,
                self.bot.db,
                self.bot,
                cookie={"ltuid": ltuid, "ltoken": ltoken},
                custom_uid=tpl[3],
            )
            result.append(shenhe_user)
        return result

    async def get_notification_users(self, table_name: str) -> List[NotificationUser]:
        result = []
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute(
            f"SELECT user_id, threshold, current, max, last_notif_time, uid FROM {table_name} WHERE toggle = 1"
        )
        data = await c.fetchall()
        for _, tpl in enumerate(data):
            user_id = tpl[0]
            threshold = tpl[1]
            current = tpl[2]
            max = tpl[3]
            last_notif_time = tpl[4]
            uid = tpl[5]
            notification_user = NotificationUser(
                user_id=user_id,
                threshold=threshold,
                current=current,
                max=max,
                uid=uid,
                last_notif_time=last_notif_time,
            )
            result.append(notification_user)
        return result

    async def base_notification(self, notification_type: str):
        log.info(f"[Schedule][{notification_type}] Start")
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        now = datetime.now()
        shenhe_users = await self.get_schedule_users()
        notification_users = await self.get_notification_users(notification_type)
        count = 0
        for notif_user in notification_users:
            for shenhe_user in shenhe_users:
                if shenhe_user.uid == notif_user.uid:
                    notif_user.shenhe_user = shenhe_user
                    break
        for user in notification_users:
            if user.shenhe_user is None:
                continue
            if user.last_notif_time is None:
                pass
            else:
                last_notif_time = datetime.strptime(
                    user.last_notif_time, "%Y/%m/%d %H:%M:%S"
                )
                time_diff = now - last_notif_time
                if time_diff.total_seconds() < 7200:
                    continue
            error = False
            error_message = ""
            client = user.shenhe_user.client
            locale = user.shenhe_user.user_locale or "en-US"
            try:
                notes = await client.get_notes(user.shenhe_user.uid)
            except genshin.errors.InvalidCookies:
                error = True
                error_message = text_map.get(36, "en-US", user.user_locale)
                log.warning(
                    f"[Schedule][{notification_type}] Invalid Cookies for {user.user_id}"
                )
                continue
            except Exception as e:
                error = True
                error_message = f"```{e}```"
                log.warning(f"[Schedule][{notification_type}] Error: {e}")
                continue
            if notification_type == "pot_notification":
                item_current_amount = notes.current_realm_currency
                item_max_amount = notes.max_realm_currency
            elif notification_type == "resin_notification":
                item_current_amount = notes.current_resin
                item_max_amount = notes.max_resin
            if item_current_amount >= user.threshold:
                if user.current >= user.max:
                    continue
                if item_current_amount == item_max_amount:
                    recover_time = text_map.get(1, locale)
                else:
                    if notification_type == "pot_notification":
                        recover_time = format_dt(
                            notes.realm_currency_recovery_time, "R"
                        )
                    elif notification_type == "resin_notification":
                        recover_time = format_dt(notes.resin_recovery_time, "R")
                if notification_type == "pot_notification":
                    embed = default_embed(
                        message=f"{text_map.get(2, locale)}: {item_current_amount}/{notes.max_realm_currency}\n"
                        f"{text_map.get(15, locale)}: {recover_time}\n"
                        f"UID: {user.shenhe_user.uid}\n",
                    )
                    embed.set_author(
                        name=text_map.get(518, locale),
                        icon_url=user.shenhe_user.discord_user.display_avatar.url,
                    )
                elif notification_type == "resin_notification":
                    embed = default_embed(
                        message=f"{text_map.get(303, locale)}: {notes.current_resin}/{notes.max_resin}\n"
                        f"{text_map.get(15, locale)}: {recover_time}\n"
                        f"UID: {user.shenhe_user.uid}\n",
                    )
                    embed.set_author(
                        name=text_map.get(306, locale),
                        icon_url=user.shenhe_user.discord_user.display_avatar.url,
                    )
                embed.set_footer(text=text_map.get(305, locale))
                try:
                    await user.shenhe_user.discord_user.send(embed=embed)
                except Forbidden:
                    await c.execute(
                        f"UPDATE {notification_type} SET toggle = 0 WHERE user_id = ? AND uid = ?",
                        (user.user_id, user.shenhe_user.uid),
                    )
                else:
                    await c.execute(
                        f"UPDATE {notification_type} SET current = ?, last_notif_time = ? WHERE user_id = ? AND uid = ?",
                        (
                            user.current + 1,
                            datetime.strftime(now, "%Y/%m/%d %H:%M:%S"),
                            user.user_id,
                            user.shenhe_user.uid,
                        ),
                    )
                    count += 1
            else:
                await c.execute(
                    f"UPDATE {notification_type} SET current = 0 WHERE user_id = ? AND uid = ?",
                    (user.user_id, user.shenhe_user.uid),
                )
            if error:
                await user.discord_user.send(
                    embed=error_embed(message=error_message)
                    .set_author(
                        name=text_map.get(
                            505 if notification_type == "resin_notification" else 506,
                            "en-US",
                            user.user_locale,
                        ),
                        icon_url=user.discord_user.display_avatar.url,
                    )
                    .set_footer(text=text_map.get(16, "en-US", user.user_locale))
                )
            await asyncio.sleep(5)
        await self.bot.db.commit()
        log.info(
            f"[Schedule][{notification_type}] Ended (Notified {count}/{len(notification_users)} users)"
        )

    @tasks.loop(hours=24)
    @schedule_error_handler
    async def backup_database(self):
        await self.backup_database_task()

    async def backup_database_task(self):
        log.info("[Schedule][Backup] Start")
        db: aiosqlite.Connection = self.bot.db
        await db.commit()
        await db.backup(self.bot.backup_db)
        log.info("[Schedule][Backup] Ended")

    @tasks.loop(hours=24)
    @schedule_error_handler
    async def claim_reward(self):
        await self.claim_reward_task()

    async def claim_reward_task(self):
        log.info("[Schedule] Claim Reward Start")
        users = await self.get_schedule_users()
        count = 0
        for user in users:
            error = False
            error_message = ""
            client = user.client
            try:
                await client.claim_daily_reward()
            except genshin.errors.AlreadyClaimed:
                pass
            except genshin.errors.InvalidCookies:
                error = True
                error_message = text_map.get(36, "en-US", user.user_locale)
                log.warning(f"[Schedule][Claim Reward] Invalid Cookies: {user}")
            except genshin.errors.GenshinException as e:
                if e.retcode in [-10002]:
                    pass
                else:
                    claimed = False
                    log.warning(f"[Schedule][Claim Reward] We have been rate limited")
                    for index in range(1, 6):
                        await asyncio.sleep(20 * index)
                        log.info(f"[Schedule][Claim Reward] Retry {index}")
                        try:
                            await client.claim_daily_reward()
                        except genshin.errors.AlreadyClaimed:
                            claimed = True
                            break
                        except Exception as e:
                            error_message = f"```{e}```"
                            log.warning(f"[Schedule][Claim Reward] Error: {e}")
                            sentry_sdk.capture_exception(e)
                    if not claimed:
                        error = True
            except Exception as e:
                error = True
                error_message = f"```{e}```"
                log.warning(f"[Schedule][Claim Reward] Error: {e}")
                sentry_sdk.capture_exception(e)
            else:
                count += 1
            if error:
                await user.discord_user.send(
                    embed=error_embed(message=error_message)
                    .set_author(
                        name=text_map.get(500, "en-US", user.user_locale),
                        icon_url=user.discord_user.display_avatar.url,
                    )
                    .set_footer(text=text_map.get(611, "en-US", user.user_locale))
                )
            await asyncio.sleep(5)
        log.info(f"[Schedule][Claim Reward] Ended ({count}/{len(users)} users)")

    @tasks.loop(hours=1)
    @schedule_error_handler
    async def pot_notification(self):
        await self.base_notification("pot_notification")

    @tasks.loop(hours=1)
    @schedule_error_handler
    async def resin_notification(self):
        await self.base_notification("resin_notification")

    @tasks.loop(minutes=30)
    @schedule_error_handler
    async def talent_notification(self):
        await self.talent_notification_task()

    async def talent_notification_task(self):
        log.info("[Schedule][Talent Notification] Start")
        client = AmbrTopAPI(self.bot.session, "cht")
        domains = await client.get_domain()
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute(
            "SELECT user_id, character_list, last_notif FROM talent_notification WHERE toggle = 1"
        )
        users = await c.fetchall()
        count = 0
        for _, tpl in enumerate(users):
            user_id = tpl[0]
            character_list = tpl[1]
            last_notif = tpl[2]
            timezone = await get_user_timezone(user_id, self.bot.db)
            now = datetime.now(pytz.timezone(timezone))
            user = (self.bot.get_user(user_id)) or await self.bot.fetch_user(user_id)
            if last_notif is not None:
                last_notif = datetime.strptime(last_notif, "%Y/%m/%d %H:%M:%S")
                if last_notif.day == now.day:
                    continue
            user_locale = await get_user_locale(user_id, self.bot.db)
            character_list = ast.literal_eval(character_list)
            notified = {}
            for character_id in character_list:
                for domain in domains:
                    if domain.weekday == now.weekday():
                        for item in domain.rewards:
                            [upgrade] = await client.get_character_upgrade(character_id)
                            if item in upgrade.items:
                                if character_id not in notified:
                                    notified[character_id] = []
                                if item.id not in notified[character_id]:
                                    notified[character_id].append(item.id)
            for character_id, materials in notified.items():
                [character] = await client.get_character(character_id)
                fp = await draw_talent_reminder_card(materials, user_locale or "en-US")
                fp.seek(0)
                file = File(fp, "reminder_card.jpeg")
                embed = default_embed(message=text_map.get(314, "en-US", user_locale))
                embed.set_author(
                    name=f"{text_map.get(312, 'en-US', user_locale)}",
                    icon_url=character.icon,
                )
                embed.set_image(url="attachment://reminder_card.jpeg")
                try:
                    await user.send(embed=embed, files=[file])
                except Forbidden:
                    await c.execute(
                        "UPDATE talent_notification SET toggle = 0 WHERE user_id = ?",
                        (user_id,),
                    )
                else:
                    await c.execute(
                        "UPDATE talent_notification SET last_notif = ? WHERE user_id = ?",
                        (now.strftime("%Y/%m/%d %H:%M:%S"), user_id),
                    )
                    count += 1
        log.info(
            f"[Schedule][Talent Notifiaction] Ended (Notified {count}/{len(users)} users)"
        )

    @tasks.loop(hours=24)
    @schedule_error_handler
    async def update_game_data(self):
        await self.update_game_data_task()

    async def update_game_data_task(self):
        log.info("[Schedule][Update Game Data] Start")
        await genshin.utility.update_characters_ambr()
        emoji_server_id = 991560432470999062
        emoji_server = self.bot.get_guild(
            emoji_server_id
        ) or await self.bot.fetch_guild(emoji_server_id)
        client = AmbrTopAPI(self.bot.session, "cht")
        eng_client = AmbrTopAPI(self.bot.session, "en")
        things_to_update = ["character", "weapon", "artifact"]
        with open(f"data/game/character_map.json", "r", encoding="utf-8") as f:
            character_map = json.load(f)
        character_map["10000005"] = {
            "name": "旅行者",
            "element": "Anemo",
            "rarity": 5,
            "icon": "https://api.ambr.top/assets/UI/UI_AvatarIcon_PlayerBoy.png",
            "eng": "Traveler",
            "emoji": str(find(lambda e: e.name == "10000005", self.bot.emojis)),
        }
        character_map["10000007"] = character_map["10000005"]
        character_map["10000007"]["emoji"] = str(
            find(lambda e: e.name == "10000007", self.bot.emojis)
        )
        with open(f"data/game/character_map.json", "w+", encoding="utf-8") as f:
            json.dump(character_map, f, ensure_ascii=False, indent=4)

        for thing in things_to_update:
            if thing == "character":
                objects = await client.get_character()
            elif thing == "weapon":
                objects = await client.get_weapon()
            elif thing == "artifact":
                objects = await client.get_artifact()
            try:
                with open(f"data/game/{thing}_map.json", "r", encoding="utf-8") as f:
                    object_map = json.load(f)
            except FileNotFoundError:
                object_map = {}
            for object in objects:
                if thing == "character":
                    object_map[str(object.id)] = {
                        "name": object.name,
                        "element": object.element,
                        "rarity": object.rairty,
                        "icon": object.icon,
                    }
                    english_name = (await eng_client.get_character(object.id))[0].name
                elif thing == "weapon":
                    object_map[str(object.id)] = {
                        "name": object.name,
                        "rarity": object.rarity,
                        "icon": object.icon,
                    }
                    english_name = (await eng_client.get_weapon(str(object.id)))[0].name
                elif thing == "artifact":
                    object_map[str(object.id)] = {
                        "name": object.name,
                        "rarity": object.rarity_list,
                        "icon": object.icon,
                    }
                    english_name = (await eng_client.get_artifact(str(object.id)))[
                        0
                    ].name
                object_map[str(object.id)]["eng"] = english_name
                object_id = str(object.id)
                if "-" in object_id:
                    object_id = (object_id.split("-"))[0]
                emoji = find(lambda e: e.name == object_id, self.bot.emojis)
                if emoji is None:
                    try:
                        async with self.bot.session.get(object.icon) as r:
                            bytes_obj = await r.read()
                        emoji = await emoji_server.create_custom_emoji(
                            name=object_id,
                            image=bytes_obj,
                        )
                    except (Forbidden, HTTPException) as e:
                        log.warning(
                            f"[Schedule] Emoji creation failed [Object]{object}"
                        )
                        sentry_sdk.capture_exception(e)
                    else:
                        object_map[str(object.id)]["emoji"] = str(emoji)
                else:
                    object_map[str(object.id)]["emoji"] = str(emoji)
            with open(f"data/game/{thing}_map.json", "w+", encoding="utf-8") as f:
                json.dump(object_map, f, ensure_ascii=False, indent=4)
        log.info("[Schedule][Update Game Data] Ended")

    @tasks.loop(hours=24)
    @schedule_error_handler
    async def update_text_map(self):
        await self.update_text_map_task()

    async def update_text_map_task(self):
        log.info("[Schedule][Update Text Map] Start")
        # character, weapon, material, artifact text map
        things_to_update = ["avatar", "weapon", "material", "reliquary"]
        for thing in things_to_update:
            dict = {}
            for lang in list(to_ambr_top_dict.values()):
                async with self.bot.session.get(
                    f"https://api.ambr.top/v2/{lang}/{thing}"
                ) as r:
                    data = await r.json()
                for character_id, character_info in data["data"]["items"].items():
                    if character_id not in dict:
                        dict[character_id] = {}
                    dict[character_id][lang] = character_info["name"]
            if thing == "avatar":
                dict["10000007"] = {
                    "chs": "旅行者",
                    "cht": "旅行者",
                    "de": "Reisende",
                    "en": "Traveler",
                    "es": "Viajera",
                    "fr": "Voyageuse",
                    "jp": "旅人",
                    "kr": "여행자",
                    "th": "นักเดินทาง",
                    "pt": "Viajante",
                    "ru": "Путешественница",
                    "vi": "Nhà Lữ Hành",
                }
                dict["10000005"] = dict["10000007"]
            with open(f"text_maps/{thing}.json", "w+", encoding="utf-8") as f:
                json.dump(dict, f, indent=4, ensure_ascii=False)
        # daily dungeon text map
        dict = {}
        for lang in list(to_ambr_top_dict.values()):
            async with self.bot.session.get(
                f"https://api.ambr.top/v2/{lang}/dailyDungeon"
            ) as r:
                data = await r.json()
            for _, domains in data["data"].items():
                for _, domain_info in domains.items():
                    if str(domain_info["id"]) not in dict:
                        dict[str(domain_info["id"])] = {}
                    dict[str(domain_info["id"])][lang] = domain_info["name"]
        with open(f"text_maps/dailyDungeon.json", "w+", encoding="utf-8") as f:
            json.dump(dict, f, indent=4, ensure_ascii=False)
        log.info("[Schedule][Update Text Map] Ended")

    @tasks.loop(hours=24)
    @schedule_error_handler
    async def update_ambr_cache(self):
        await self.update_ambr_cache_task()

    async def update_ambr_cache_task(self):
        log.info("[Schedule][Update Ambr Cache] Start")
        client = AmbrTopAPI(self.bot.session)
        await client._update_cache(all_lang=True)
        await client._update_cache(static=True)
        log.info("[Schedule][Update Ambr Cache] Ended")

    @claim_reward.before_loop
    async def before_claiming_reward(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        next_run = now.replace(hour=1, minute=0, second=0)  # 等待到早上1點
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)

    @resin_notification.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @pot_notification.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @talent_notification.before_loop
    async def before_notif(self):
        await self.bot.wait_until_ready()

    @change_status.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @update_text_map.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        next_run = now.replace(hour=2, minute=0, second=0)  # 等待到早上2點
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)

    @backup_database.before_loop
    async def before_backup(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        next_run = now.replace(hour=0, minute=30, second=0)  # 等待到早上0點30分
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)

    @update_game_data.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        next_run = now.replace(hour=2, minute=30, second=0)  # 等待到早上2點30分
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)

    @update_ambr_cache.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        next_run = now.replace(hour=2, minute=30, second=0)  # 等待到早上2點30分
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)

    @is_seria()
    @app_commands.command(
        name="instantclaim", description=_("Owner usage only", hash=496)
    )
    async def instantclaim(self, i: Interaction):
        await i.response.send_message("started, check console", ephemeral=True)
        await self.claim_reward_task()

    @is_seria()
    @app_commands.command(name="backup", description=_("Owner usage only", hash=496))
    async def backup(self, i: Interaction):
        await i.response.send_message("started", ephemeral=True)
        await self.backup_database_task()
        await i.edit_original_response(content="backup completed")

    @is_seria()
    @app_commands.command(
        name="updategamedata", description=_("Owner usage only", hash=496)
    )
    async def updategamedata(self, i: Interaction):
        await i.response.send_message("started", ephemeral=True)
        await self.update_ambr_cache_task()
        await i.edit_original_response(content="updated amber cache (1/3)")
        await self.update_text_map_task()
        await i.edit_original_response(content="updated text map (2/3)")
        await self.update_game_data_task()
        await i.edit_original_response(content="updated game data (3/3)")

    @is_seria()
    @app_commands.command(
        name="instantnotify", description=_("Owner usage only", hash=496)
    )
    async def instant_notify(self, i: Interaction):
        await i.response.send_message(content="started", ephemeral=True)
        await self.talent_notification_task()
        await i.edit_original_response(content="talent notification sent")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Schedule(bot))
