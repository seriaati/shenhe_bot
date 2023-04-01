import asyncio
import io
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import aiofiles
import discord
import genshin
from discord import utils
from discord.ext import commands, tasks

import ambr
import apps.genshin as genshin_app
import asset
import models
from apps.db import get_user_lang, get_user_theme
from apps.draw import main_funcs
from apps.text_map import text_map, to_ambr_top
from base_ui import capture_exception
from utility import dm_embed, log
from utility.fetch_card import fetch_cards
from utility.utils import get_dt_now


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
    def __init__(self, bot):
        self.bot: models.ShenheBot = bot
        self.debug = self.bot.debug
        if not self.debug:
            self.run_tasks.start()

    async def cog_unload(self):
        if not self.debug:
            self.run_tasks.cancel()

    loop_interval = 1

    @tasks.loop(minutes=loop_interval)
    async def run_tasks(self):
        """Run the tasks every loop_interval minutes"""
        now = get_dt_now()

        if now.minute < self.loop_interval:  # every hour
            check_tasks = ("resin_notification", "pot_notification", "pt_notification")
            for task in check_tasks:
                asyncio.create_task(self.check_notification(task))
            asyncio.create_task(self.save_codes())

        if now.hour == 0 and now.minute < self.loop_interval:  # midnight
            asyncio.create_task(self.claim_reward())

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
                self.weapon_talent_base_notification(
                    "talent_notification", hour_dict[now.hour]
                )
            )
            asyncio.create_task(
                self.weapon_talent_base_notification(
                    "weapon_notification", hour_dict[now.hour]
                )
            )

        if now.hour == 10 and now.minute < self.loop_interval:  # 10am
            asyncio.create_task(self.redeem_codes())

    @schedule_error_handler
    async def update_shenhe_cache_and_data(self):
        await self.update_ambr_cache()
        await self.update_text_map()
        await self.update_game_data()
        await self.update_card_data()

    @schedule_error_handler
    async def save_codes(self):
        log.info("[Schedule] Saving codes...")
        await self.bot.pool.execute(
            "CREATE TABLE IF NOT EXISTS genshin_codes (code text)"
        )
        await self.bot.pool.execute("DELETE FROM genshin_codes")
        codes = await genshin_app.find_codes(self.bot.session)
        for code in codes:
            await self.bot.pool.execute("INSERT INTO genshin_codes VALUES ($1)", code)
        log.info(f"[Schedule] Codes saved: {codes}.")

    @schedule_error_handler
    async def generate_abyss_json(self):
        log.info("[Schedule] Generating abyss.json...")

        result: Dict[str, Any] = {}
        result["schedule_id"] = genshin_app.get_current_abyss_season()
        result["size"] = 0
        result["data"] = []

        accounts = await self.get_schedule_users()

        for account in accounts:
            if str(account.uid)[0] in (1, 2, 5):
                continue

            client = account.client
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

        lvlurarti_id = 630235350526328844
        lvlurarti = self.bot.get_user(lvlurarti_id) or await self.bot.fetch_user(
            lvlurarti_id
        )
        fp = io.BytesIO()
        fp.write(json.dumps(result, indent=4).encode())
        fp.seek(0)
        await lvlurarti.send(file=discord.File(fp, "abyss.json"))

        log.info("[Schedule] Sent abyss.json")

    @schedule_error_handler
    async def check_notification(self, notification_type: str):
        log.info(f"[Schedule][{notification_type}] Checking...")

        n_users = await self.get_notification_users(notification_type)
        now = get_dt_now()
        sent_num = 0
        for n_user in n_users:
            if n_user.last_notif and now - n_user.last_notif < timedelta(hours=2):
                continue

            try:
                s_user = await genshin_app.get_shenhe_account(
                    n_user.user_id, self.bot, custom_uid=n_user.uid
                )
            except Exception:  # skipcq: PYL-W0703
                continue

            locale = s_user.user_locale or "en-US"

            error = False
            error_message = ""
            try:
                notes = await s_user.client.get_notes(s_user.uid)
            except genshin.errors.InvalidCookies:
                error = True
                error_message = text_map.get(36, locale)
                log.warning(
                    f"[Schedule][{notification_type}][{n_user.user_id}] Invalid Cookies for {n_user.user_id}"
                )
                await self.disable_notification(
                    n_user.user_id, n_user.uid, notification_type
                )
            except (genshin.errors.InternalDatabaseError, OSError):
                pass
            except genshin.errors.GenshinException as e:
                if e.retcode != 1009:
                    error = True
                    error_message = f"```{e}```"
                    if e.msg:
                        error_message += f"\n```{e.msg}```"
                    log.warning(
                        f"[Schedule][{notification_type}][{n_user.user_id}] Error: {e}"
                    )
                    await self.disable_notification(
                        n_user.user_id, n_user.uid, notification_type
                    )
            except Exception as e:  # skipcq: PYL-W0703
                error = True
                error_message = f"```{e}```"
                log.warning(
                    f"[Schedule][{notification_type}][{n_user.user_id}] Error: {e}"
                )
                await self.disable_notification(
                    n_user.user_id, n_user.uid, notification_type
                )
            else:
                # reset current
                await self.reset_notif_current(notification_type, n_user, notes)

                if error:
                    await self.handle_notif_error(
                        notification_type, n_user, locale, error_message
                    )
                else:
                    if n_user.current >= n_user.max:
                        continue

                    # send notification
                    success = False
                    if (
                        notification_type == "resin_notification"
                        and notes.current_resin >= n_user.threshold
                    ):
                        success = await self.notify_resin(n_user, notes, locale)
                    elif (
                        notification_type == "pot_notification"
                        and notes.current_realm_currency >= n_user.threshold
                    ):
                        success = await self.notify_pot(n_user, notes, locale)
                    elif (
                        notification_type == "pt_notification"
                        and notes.remaining_transformer_recovery_time is not None
                        and notes.remaining_transformer_recovery_time.total_seconds()
                        == 0
                    ):
                        if (
                            n_user.last_notif is not None
                            and n_user.last_notif.day == now.day
                        ):
                            continue
                        success = await self.notify_pt(n_user, locale)

                    if success:
                        log.info(
                            f"[Schedule][{notification_type}][{n_user.user_id}] Notification sent"
                        )
                        sent_num += 1
                        await self.update_current(
                            notification_type, now, n_user, s_user
                        )

            await asyncio.sleep(2.5)

        log.info(
            f"[Schedule][{notification_type}] Sent {sent_num} notifications, total {len(n_users)} users"
        )

    async def reset_notif_current(
        self,
        notification_type: str,
        n_user: models.NotificationUser,
        notes: genshin.models.Notes,
    ):
        if (
            notification_type == "resin_notification"
            and notes.current_resin < n_user.threshold
        ):
            await self.reset_current(n_user.user_id, n_user.uid, "resin_notification")
        elif (
            notification_type == "pot_notification"
            and notes.current_realm_currency < n_user.threshold
        ):
            await self.reset_current(n_user.user_id, n_user.uid, "pot_notification")

    async def update_current(
        self,
        notification_type: str,
        now: datetime,
        n_user: models.NotificationUser,
        s_user: models.ShenheAccount,
    ):
        await self.bot.pool.execute(
            f"UPDATE {notification_type} SET current = current + 1, last_notif = $1 WHERE user_id = $2 AND uid = $3",
            now,
            n_user.user_id,
            s_user.uid,
        )

    async def handle_notif_error(
        self,
        notification_type: str,
        n_user: models.NotificationUser,
        locale: str,
        error_message: str,
    ):
        discord_user = self.bot.get_user(n_user.user_id) or await self.bot.fetch_user(
            n_user.user_id
        )
        if notification_type == "pot_notification":
            map_hash = 584
        elif notification_type == "pt_notification":
            map_hash = 704
        else:  # resin_notification
            map_hash = 582

        embed = models.ErrorEmbed(
            description=f"{error_message}\n\n{text_map.get(631, locale).format(feature=text_map.get(map_hash, locale))}"
        )
        embed.set_author(
            name=text_map.get(505, locale),
            icon_url=discord_user.display_avatar.url,
        )
        embed.set_footer(text=text_map.get(16, locale))
        await dm_embed(discord_user, embed)

    async def notify_resin(
        self,
        user: models.NotificationUser,
        notes: genshin.models.Notes,
        locale: str,
    ) -> bool:
        discord_user = self.bot.get_user(user.user_id) or await self.bot.fetch_user(
            user.user_id
        )
        embed = models.DefaultEmbed(
            description=f"{text_map.get(303, locale)}: {notes.current_resin}/{notes.max_resin}\n"
            f"{text_map.get(15, locale)}: {text_map.get(1, locale) if notes.current_resin == notes.max_resin else utils.format_dt(notes.resin_recovery_time, 'R')}\n"
            f"UID: {user.uid}\n",
        ).set_title(306, locale, discord_user)
        embed.set_thumbnail(url=asset.resin_icon)
        embed.set_footer(text=text_map.get(305, locale))

        success = await dm_embed(discord_user, embed)
        if not success:
            await self.disable_notification(
                user.user_id, user.uid, "resin_notification"
            )
        return success

    async def notify_pot(
        self,
        user: models.NotificationUser,
        notes: genshin.models.Notes,
        locale: str,
    ) -> bool:
        discord_user = self.bot.get_user(user.user_id) or await self.bot.fetch_user(
            user.user_id
        )
        embed = models.DefaultEmbed(
            description=f"{text_map.get(102, locale)}: {notes.current_realm_currency}/{notes.max_realm_currency}\n"
            f"{text_map.get(15, locale)}: {text_map.get(1, locale) if notes.current_realm_currency == notes.max_realm_currency else utils.format_dt(notes.realm_currency_recovery_time, 'R')}\n"
            f"UID: {user.uid}\n",
        )
        embed.set_author(
            name=text_map.get(518, locale),
            icon_url=discord_user.display_avatar.url,
        )
        embed.set_thumbnail(url=asset.realm_currency_icon)
        embed.set_footer(text=text_map.get(305, locale))

        success = await dm_embed(discord_user, embed)
        if not success:
            await self.disable_notification(user.user_id, user.uid, "pot_notification")
        return success

    async def notify_pt(self, user: models.NotificationUser, locale: str):
        discord_user = self.bot.get_user(user.user_id) or await self.bot.fetch_user(
            user.user_id
        )
        embed = models.DefaultEmbed(description=f"UID: {user.uid}")
        embed.set_author(
            name=text_map.get(366, locale),
            icon_url=discord_user.display_avatar.url,
        )
        embed.set_thumbnail(url=asset.pt_icon)
        embed.set_footer(text=text_map.get(305, locale))

        success = await dm_embed(discord_user, embed)
        if not success:
            await self.disable_notification(user.user_id, user.uid, "pt_notification")
        return success

    async def disable_notification(
        self, user_id: int, uid: int, notification_type: str
    ):
        await self.bot.pool.execute(
            f"UPDATE {notification_type} SET toggle = false WHERE user_id = $1 AND uid = $2",
            user_id,
            uid,
        )

    async def reset_current(self, user_id: int, uid: int, notification_type: str):
        await self.bot.pool.execute(
            f"UPDATE {notification_type} SET current = 0 WHERE user_id = $1 AND uid = $2",
            user_id,
            uid,
        )

    async def get_schedule_users(self) -> List[models.ShenheAccount]:
        """Gets a list of shenhe users that have Cookie registered (ltuid is not None)

        Returns:
            List[models.ShenheAccount]: List of shenhe users
        """
        accounts: List[models.ShenheAccount] = []
        rows = await self.bot.pool.fetch(
            "SELECT user_id, ltuid, ltoken, cookie_token, uid FROM user_accounts WHERE ltuid IS NOT NULL"
        )
        for row in rows:
            custom_cookie = {
                "ltuid": row["ltuid"],
                "ltoken": row["ltoken"],
                "cookie_token": row["cookie_token"],
            }
            try:
                account = await genshin_app.get_shenhe_account(
                    row["user_id"],
                    self.bot,
                    custom_cookie=custom_cookie,
                    custom_uid=row["uid"],
                )
            except Exception:  # skipcq: PYL-W0703
                continue
            accounts.append(account)

        return accounts

    async def get_notification_users(
        self, table_name: str
    ) -> List[models.NotificationUser]:
        """Gets a list of notification users that has the reminder feature enabled

        Args:
            table_name (str): the table name in the database

        Returns:
            List[models.NotificationUser]: a list of notification users
        """
        select_query = "SELECT user_id, uid, max, last_notif, current"
        if table_name in ("resin_notification", "pot_notification"):
            select_query += ", threshold"
        rows = await self.bot.pool.fetch(
            f"{select_query} FROM {table_name} WHERE toggle = true"
        )

        return [models.NotificationUser(**row) for row in rows]

    @schedule_error_handler
    async def redeem_codes(self):
        """Auto-redeems codes for all Shenhe users that have Cookie registered"""
        log.info("[Schedule][Redeem Codes] Start")

        codes = await genshin_app.find_codes(self.bot.session)
        log.info(f"[Schedule][Redeem Codes] Found codes {codes}")

        users = await self.get_redeem_code_users()
        for index, user in enumerate(users):
            locale = user.user_locale or "en-US"
            embed = models.DefaultEmbed(text_map.get(126, locale))

            for code in codes:
                c = await self.bot.pool.fetchval(
                    "SELECT code FROM redeem_codes WHERE code = $1 AND uid = $2",
                    code,
                    user.uid,
                )
                if c:
                    continue
                value, success = await self.redeem_code(user, locale, code)

                embed.add_field(
                    name=f"{'✅' if success else '⛔'} {code}",
                    value=value,
                )
                await self.bot.pool.execute(
                    "INSERT INTO redeem_codes (code, uid) VALUES ($1, $2)",
                    code,
                    user.uid,
                )
                await asyncio.sleep(5)

            if embed.fields:
                await dm_embed(user.discord_user, embed)
            await asyncio.sleep(10)
            if index % 100 == 0:
                await asyncio.sleep(30)

        log.info("[Schedule][Redeem Codes] Done")

    async def get_redeem_code_users(self):
        users: List[models.ShenheAccount] = []
        rows = await self.bot.pool.fetch(
            "SELECT user_id FROM user_settings WHERE auto_redeem = true"
        )
        for row in rows:
            try:
                acc = await genshin_app.get_shenhe_account(row["user_id"], self.bot)
            except Exception:  # skipcq: PYL-W0703
                pass
            else:
                users.append(acc)
        return users

    @staticmethod
    async def redeem_code(user, locale, code):
        success = False
        value = "default_value"
        try:
            await user.client.redeem_code(code, user.uid)
        except genshin.errors.InvalidCookies:
            value = text_map.get(36, locale)
        except genshin.errors.RedemptionClaimed:
            value = text_map.get(106, locale)
        except genshin.errors.RedemptionCooldown:
            await asyncio.sleep(10)
            try:
                await user.client.redeem_code(code, user.uid)
            except Exception:  # skipcq: PYL-W0703
                value = text_map.get(127, locale)
        except genshin.errors.RedemptionException as e:
            value = e.msg
        except Exception as e:  # skipcq: PYL-W0703
            value = f"{type(e)} {e}"
        else:
            log.info(
                f"[Schedule][Redeem Codes] Redeemed {code} for ({user.discord_user.id}, {user.uid})"
            )
            success = True
            value = text_map.get(109, locale)
        return value, success

    @schedule_error_handler
    async def claim_reward(self):
        """Claims daily check-in rewards for all Shenhe users that have Cookie registered"""
        log.info("[Schedule][Claim Reward] Start")
        users = await self.get_schedule_users()

        success_count = 0
        user_count = 0

        for user in users:
            if not user.daily_checkin:
                continue

            user_count += 1
            (
                success_count,
                error,
                error_message,
            ) = await genshin_app.claim_daily_checkin_reward(
                success_count, user, user.client, self.bot.pool
            )

            if error:
                await genshin_app.handle_daily_reward_error(
                    user, error_message, self.bot.pool
                )

            if user_count % 100 == 0:  # Sleep for 40 seconds every 100 users
                await asyncio.sleep(40)

            await asyncio.sleep(3.5)

        log.info(f"[Schedule][Claim Reward] Ended ({success_count}/{user_count} users)")

        # send a notification to Seria
        seria = self.bot.get_user(410036441129943050) or await self.bot.fetch_user(
            410036441129943050
        )
        await seria.send(
            embed=models.DefaultEmbed(
                "Automatic daily check-in report",
                f"Claimed {success_count}/{user_count}",
            )
        )

    @schedule_error_handler
    async def weapon_talent_base_notification(
        self, notification_type: str, time_offset: int
    ):
        time_offset = int(time_offset)
        log.info(f"[Schedule][{notification_type}][offset: {time_offset}] Start")
        upgrade_cache: Dict[str, ambr.CharacterUpgrade | ambr.WeaponUpgrade] = {}
        item_cache: Dict[str, ambr.Weapon | ambr.Character] = {}

        rows = await self.bot.pool.fetch(
            f"SELECT user_id, item_list FROM {notification_type} WHERE toggle = true"
        )
        count = 0
        for row in rows:
            user_id: int = row["user_id"]
            item_list: List[str] = row["item_list"]

            uid = await genshin_app.get_uid(user_id, self.bot.pool)
            uid_tz = genshin_app.get_uid_tz(uid)
            if uid_tz != time_offset:
                continue

            log.info(
                f"[Schedule][{notification_type}][offset: {time_offset}] {user_id} ({count})"
            )

            now = get_dt_now() + timedelta(hours=time_offset)
            locale = await get_user_lang(user_id, self.bot.pool) or "en-US"

            client = ambr.AmbrTopAPI(self.bot.session, to_ambr_top(locale))
            domains = await client.get_domains()
            today_domains = [d for d in domains if d.weekday == now.weekday()]

            user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
            notified: Dict[str, Dict[str, Any]] = {}

            for item_id in item_list:
                for domain in today_domains:
                    for reward in domain.rewards:
                        upgrade = upgrade_cache.get(str(item_id))

                        if upgrade is None:
                            if notification_type == "talent_notification":
                                upgrade = await client.get_character_upgrade(
                                    str(item_id)
                                )
                            else:
                                upgrade = await client.get_weapon_upgrade(int(item_id))
                            if not isinstance(
                                upgrade, (ambr.CharacterUpgrade, ambr.WeaponUpgrade)
                            ):
                                raise AssertionError
                            upgrade_cache[str(item_id)] = upgrade

                        if reward in upgrade.items:
                            if item_id not in notified:
                                notified[item_id] = {
                                    "materials": [],
                                    "domain": domain,
                                }
                            if reward.id not in notified[item_id]["materials"]:
                                notified[item_id]["materials"].append(reward.id)

            for item_id, item_info in notified.items():
                item = item_cache.get(str(item_id))

                if item is None:
                    if notification_type == "talent_notification":
                        item = await client.get_character(str(item_id))
                    else:
                        item = await client.get_weapon(int(item_id))
                    if not isinstance(item, (ambr.Character, ambr.Weapon)):
                        continue
                    item_cache[str(item_id)] = item

                materials: List[Tuple[ambr.Material, str]] = []
                for material_id in item_info["materials"]:
                    material = await client.get_material(material_id)
                    if not isinstance(material, ambr.Material):
                        continue
                    materials.append((material, ""))

                dark_mode = await get_user_theme(user_id, self.bot.pool)
                fp = await main_funcs.draw_material_card(
                    models.DrawInput(
                        loop=self.bot.loop,
                        session=self.bot.session,
                        locale=locale,
                        dark_mode=dark_mode,
                    ),
                    materials,  # type: ignore
                    "",
                    draw_title=False,
                )
                fp.seek(0)
                _file = discord.File(fp, "reminder_card.jpeg")

                domain: ambr.Domain = item_info["domain"]

                embed = models.DefaultEmbed()
                embed.add_field(
                    name=text_map.get(609, locale),
                    value=f"{domain.name} ({domain.city.name})",
                )
                embed.set_author(
                    name=text_map.get(312, locale).format(name=item.name),
                    icon_url=item.icon,
                )
                embed.set_footer(text=text_map.get(134, locale))
                embed.set_image(url="attachment://reminder_card.jpeg")

                try:
                    await user.send(embed=embed, files=[_file])
                except discord.Forbidden:
                    await self.bot.pool.execute(
                        f"UPDATE {notification_type} SET toggle = false WHERE user_id = $1",
                        user_id,
                    )
                else:
                    count += 1
            await asyncio.sleep(2.5)
        log.info(f"[Schedule][{notification_type}] Ended (Notified {count} users)")

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
