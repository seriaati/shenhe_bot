import ast
import asyncio
import json
import random
from datetime import timedelta
import traceback
from typing import List, Literal, Optional
from apps.draw import main_funcs
import aiosqlite
from data.game.pot import get_pot_accumulation_rate
import genshin
import sentry_sdk
from discord import File, Game, Interaction, app_commands
from discord.errors import Forbidden, HTTPException
from discord.ext import commands, tasks
from discord.utils import find, format_dt

import asset
from ambr.client import AmbrTopAPI
from ambr.models import Artifact, Character, Domain, Material, Weapon
from apps.genshin.custom_model import DrawInput, NotificationUser, ShenheBot, ShenheUser
from apps.genshin.utils import get_shenhe_user, get_uid, get_uid_tz
from apps.text_map.convert_locale import to_ambr_top, to_ambr_top_dict
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from cogs.admin import is_seria
from utility.utils import (
    default_embed,
    error_embed,
    get_dt_now,
    get_user_appearance_mode,
    log,
)


def schedule_error_handler(func):
    async def inner_function(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except Exception as e:
            bot = args[0].bot
            seria = bot.get_user(410036441129943050) or await bot.fetch_user(
                410036441129943050
            )
            await seria.send(
                embed=error_embed(
                    f"[Schedule] Error in {func.__name__}", f"```\n{e}\n```"
                )
            )
            log.warning(f"[Schedule] Error in {func.__name__}: {e}")
            traceback.print_exc()
            sentry_sdk.capture_exception(e)

    return inner_function


class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot: ShenheBot = bot
        self.debug = self.bot.debug
        if not self.debug:
            self.run_tasks.start()
        self.change_status.start()

    def cog_unload(self):
        if not self.debug:
            self.run_tasks.cancel()
        self.change_status.cancel()

    loop_interval = 1

    @tasks.loop(minutes=loop_interval)
    async def run_tasks(self):
        """Run the tasks every loop_interval minutes"""
        now = get_dt_now()
        tasks = ["resin_notification", "pot_notification", "pt_notification"]
        for task in tasks:
            await asyncio.create_task(self.check_notification(task))

        if now.hour == 0 and now.minute < self.loop_interval:  # midnight
            await asyncio.create_task(self.claim_reward())

        if now.hour == 1 and now.minute < self.loop_interval:  # 1am
            await asyncio.create_task(self.update_ambr_cache())
            await asyncio.create_task(self.update_text_map())
            await asyncio.create_task(self.update_game_data())
            await asyncio.create_task(self.backup_database())

        if now.hour in [4, 15, 21] and now.minute < self.loop_interval:  # 4am, 3pm, 9pm
            hour_dict = {
                4: 0,  # Asia
                15: -13,  # North America
                21: -7,  # Europe
            }
            await asyncio.create_task(
                self.weapon_talent_base_notifiction(
                    "talent_notification", hour_dict[now.hour]
                )
            )
            await asyncio.create_task(
                self.weapon_talent_base_notifiction(
                    "weapon_notification", hour_dict[now.hour]
                )
            )

    @tasks.loop(minutes=20)
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

    async def check_notification(self, notification_type: str):
        n_users = await self.get_notification_users(notification_type)
        now = get_dt_now()
        sent_num = 0
        c = await self.bot.db.cursor()
        for n_user in n_users:
            if n_user.last_check is not None and now < n_user.last_check:
                continue
            if n_user.last_notif is not None and now - n_user.last_notif < timedelta(
                hours=2
            ):  # notify every 2 hours
                continue

            s_user = await get_shenhe_user(n_user.user_id, self.bot.db, self.bot)
            locale = s_user.user_locale or "en-US"

            error = False
            error_message = ""
            try:
                notes = await s_user.client.get_notes(s_user.uid)
            except genshin.errors.InvalidCookies:
                error = True
                error_message = text_map.get(36, locale)
                log.warning(
                    f"[Schedule][{notification_type}] Invalid Cookies for {n_user.user_id}"
                )
                await self.disable_notification(
                    n_user.user_id, n_user.uid, notification_type
                )
            except (genshin.errors.InternalDatabaseError, OSError):
                pass
            except Exception as e:
                error = True
                error_message = f"```{e}```"
                log.warning(f"[Schedule][{notification_type}] Error: {e}")
                await self.disable_notification(
                    n_user.user_id, n_user.uid, notification_type
                )
            else:
                # calulate the time to reach the threshold
                reach_time = now
                if notification_type == "resin_notification":
                    diff = timedelta(minutes=8) - (
                        (now + timedelta(minutes=8 * (160 - notes.current_resin)))
                        - notes.resin_recovery_time.replace(tzinfo=None)
                    )
                    reach_time = (
                        now
                        + diff
                        + timedelta(
                            minutes=8 * (n_user.threshold - notes.current_resin - 1)
                        )
                    )
                    if notes.current_resin < n_user.threshold:
                        await self.reset_current(
                            n_user.user_id, n_user.uid, "resin_notification"
                        )

                elif notification_type == "pot_notification":
                    stats = await s_user.client.get_partial_genshin_user(s_user.uid)
                    if stats.teapot is None:
                        continue
                    rate = get_pot_accumulation_rate(stats.teapot.comfort)
                    ac_rate = 1 / rate
                    theoretical = now + timedelta(
                        hours=ac_rate
                        * (notes.max_realm_currency - notes.current_realm_currency)
                    )
                    real = notes.realm_currency_recovery_time.replace(tzinfo=None)
                    diff = theoretical - real
                    reach_time = (
                        now
                        + diff
                        + timedelta(
                            hours=ac_rate
                            * (n_user.threshold - notes.current_realm_currency - rate)
                        )
                    )
                    if notes.current_realm_currency < n_user.threshold:
                        await self.reset_current(
                            n_user.user_id, n_user.uid, "pot_notification"
                        )

                elif notification_type == "pt_notification":
                    if notes.remaining_transformer_recovery_time is not None:
                        reach_time = now + timedelta(
                            seconds=notes.remaining_transformer_recovery_time.total_seconds()
                        )
                        if (
                            notes.remaining_transformer_recovery_time.total_seconds()
                            > 0
                        ):
                            await self.reset_current(
                                n_user.user_id, n_user.uid, "pt_notification"
                            )

                # update last check time
                await c.execute(
                    f"UPDATE {notification_type} SET last_check = ? WHERE user_id = ? AND uid = ?",
                    (reach_time, n_user.user_id, s_user.uid),
                )

                # send error message
                if error:
                    discord_user = self.bot.get_user(
                        n_user.user_id
                    ) or await self.bot.fetch_user(n_user.user_id)
                    if notification_type == "pot_notification":
                        map_hash = 584
                    elif notification_type == "pt_notification":
                        map_hash = 704
                    else:  # resin_notification
                        map_hash = 582
                    embed = error_embed(
                        message=f"{error_message}\n\n{text_map.get(631, locale).format(feature=text_map.get(map_hash, locale))}"
                    )
                    embed.set_author(
                        name=text_map.get(505, locale),
                        icon_url=discord_user.display_avatar.url,
                    )
                    embed.set_footer(text=text_map.get(16, locale))
                    try:
                        await discord_user.send(embed=embed)
                    except Forbidden:
                        pass

                # send notification
                if reach_time <= now and not error:
                    success = False
                    if notification_type == "resin_notification":
                        success = await self.notify_resin(n_user, notes, locale)
                    elif notification_type == "pot_notification":
                        success = await self.notify_pot(n_user, notes, locale)
                    elif notification_type == "pt_notification":
                        success = await self.notify_pt(n_user, locale)
                    if success:
                        sent_num += 1
                        # update notification count
                        await c.execute(
                            f"UPDATE {notification_type} SET current = current + 1 WHERE user_id = ? AND uid = ?",
                            (n_user.user_id, s_user.uid),
                        )
                        # update last notification time
                        await c.execute(
                            f"UPDATE {notification_type} SET {'last_notif' if notification_type == 'pt_notification' else 'last_notif_time'} = ? WHERE user_id = ? AND uid = ?",
                            (now, n_user.user_id, s_user.uid),
                        )
            await asyncio.sleep(2.5)

        await self.bot.db.commit()

    async def notify_resin(
        self, user: NotificationUser, notes: genshin.models.Notes, locale: str
    ) -> bool:
        discord_user = self.bot.get_user(user.user_id) or await self.bot.fetch_user(
            user.user_id
        )
        embed = default_embed(
            message=f"{text_map.get(303, locale)}: {notes.current_resin}/{notes.max_resin}\n"
            f"{text_map.get(15, locale)}: {text_map.get(1, locale) if notes.current_resin == notes.max_resin else format_dt(notes.resin_recovery_time, 'R')}\n"
            f"UID: {user.uid}\n",
        )
        embed.set_author(
            name=text_map.get(306, locale),
            icon_url=discord_user.display_avatar.url,
        )
        embed.set_footer(text=text_map.get(305, locale))
        try:
            await discord_user.send(embed=embed)
        except Forbidden:
            await self.disable_notification(
                user.user_id, user.uid, "resin_notification"
            )
            return False
        else:
            return True

    async def notify_pot(
        self, user: NotificationUser, notes: genshin.models.Notes, locale: str
    ) -> bool:
        discord_user = self.bot.get_user(user.user_id) or await self.bot.fetch_user(
            user.user_id
        )
        embed = default_embed(
            message=f"{text_map.get(102, locale)}: {notes.current_realm_currency}/{notes.max_realm_currency}\n"
            f"{text_map.get(15, locale)}: {text_map.get(1, locale) if notes.current_realm_currency == notes.max_realm_currency else format_dt(notes.realm_currency_recovery_time, 'R')}\n"
            f"UID: {user.uid}\n",
        )
        embed.set_author(
            name=text_map.get(518, locale),
            icon_url=discord_user.display_avatar.url,
        )
        embed.set_footer(text=text_map.get(305, locale))
        try:
            await discord_user.send(embed=embed)
        except Forbidden:
            await self.disable_notification(user.user_id, user.uid, "pot_notification")
            return False
        else:
            return True

    async def notify_pt(self, user: NotificationUser, locale: str):
        discord_user = self.bot.get_user(user.user_id) or await self.bot.fetch_user(
            user.user_id
        )
        embed = default_embed(message=f"UID: {user.uid}")
        embed.set_author(
            name=text_map.get(366, locale),
            icon_url=discord_user.display_avatar.url,
        )
        embed.set_thumbnail(url=asset.pt_icon)
        embed.set_footer(text=text_map.get(305, locale))
        try:
            await discord_user.send(embed=embed)
        except Forbidden:
            await self.disable_notification(user.user_id, user.uid, "pt_notification")
            return False
        else:
            return True

    async def disable_notification(
        self, user_id: int, uid: int, notification_type: str
    ):
        await self.bot.db.execute(
            f"UPDATE {notification_type} SET toggle = 0 WHERE user_id = ? AND uid = ?",
            (user_id, uid),
        )
        await self.bot.db.commit()

    async def reset_current(self, user_id: int, uid: int, notification_type: str):
        await self.bot.db.execute(
            f"UPDATE {notification_type} SET current = 0 WHERE user_id = ? AND uid = ?",
            (user_id, uid),
        )
        await self.bot.db.commit()

    async def get_schedule_users(
        self, user_ids: Optional[List[int]] = None
    ) -> List[ShenheUser]:
        """Gets a list of shenhe users that have Cookie registered (ltuid is not None)

        Returns:
            List[ShenheUser]: List of shenhe users
        """
        result = []
        c = await self.bot.db.cursor()

        if user_ids is not None:
            seq = ",".join(["?"] * len(user_ids))
            await c.execute(
                f"SELECT ltuid, ltoken, user_id, uid, daily_checkin FROM user_accounts WHERE ltuid IS NOT NULL AND user_id IN ({seq})",
                (tuple(user_ids)),
            )
        else:
            await c.execute(
                "SELECT ltuid, ltoken, user_id, uid, daily_checkin FROM user_accounts WHERE ltuid IS NOT NULL",
            )

        users = await c.fetchall()
        for _, tpl in enumerate(users):
            ltuid = tpl[0]
            ltoken = tpl[1]
            user_id = tpl[2]
            uid = tpl[3]
            daily_checkin = tpl[4]
            shenhe_user = await get_shenhe_user(
                user_id,
                self.bot.db,
                self.bot,
                cookie={"ltuid": ltuid, "ltoken": ltoken},
                custom_uid=uid,
                daily_checkin=True if daily_checkin == 1 else False,
            )
            result.append(shenhe_user)

        await c.close()
        return result

    async def get_notification_users(self, table_name: str) -> List[NotificationUser]:
        """Gets a list of notification users that has the reminder feature enabled

        Args:
            table_name (str): the table name in the database

        Returns:
            List[NotificationUser]: a list of notification users
        """
        result = []
        if table_name == "pt_notification":
            async with self.bot.db.execute(
                f"SELECT user_id, uid, max, last_notif, last_check FROM {table_name} WHERE toggle = 1"
            ) as c:
                async for row in c:
                    result.append(
                        NotificationUser(
                            user_id=row[0],
                            uid=row[1],
                            max=row[2],
                            last_notif=row[3],
                            last_check=row[4],
                        )
                    )
        else:  # resin_notification, pot_notification
            async with self.bot.db.execute(
                f"SELECT user_id, threshold, current, max, last_notif_time, uid, last_check FROM {table_name} WHERE toggle = 1"
            ) as c:
                async for row in c:
                    result.append(
                        NotificationUser(
                            user_id=row[0],
                            threshold=row[1],
                            current=row[2],
                            max=row[3],
                            last_notif=row[4],
                            uid=row[5],
                            last_check=row[6],
                        )
                    )
        return result

    @schedule_error_handler
    async def backup_database(self):
        """Backs up the shenhe database, the new database is named backup.db"""
        log.info("[Schedule][Backup] Start")
        db: aiosqlite.Connection = self.bot.db
        await db.commit()
        await db.backup(self.bot.backup_db)
        log.info("[Schedule][Backup] Ended")

    @schedule_error_handler
    async def claim_reward(self):
        """Claims daily check-in rewards for all Shenhe users that have Cookie registered"""
        log.info("[Schedule][Claim Reward] Start")
        users = await self.get_schedule_users()
        count = 0
        user_count = 0

        for user in users:
            if not user.daily_checkin:
                continue
            user_count += 1
            error = True
            error_message = ""
            client = user.client
            try:
                reward = await client.claim_daily_reward()
            except genshin.errors.AlreadyClaimed:
                error = False
                count += 1
            except genshin.errors.InvalidCookies:
                error_message = text_map.get(36, "en-US", user.user_locale)
                log.warning(f"[Schedule][Claim Reward] Invalid Cookies: {user}")
                count += 1
            except genshin.errors.GenshinException as e:
                error_message = f"```{e}```"
                log.warning(f"[Schedule][Claim Reward] Genshin Exception: {e}")
                sentry_sdk.capture_exception(e)
            except Exception as e:
                error_message = f"```{e}```"
                log.warning(f"[Schedule][Claim Reward] Error: {e}")
                sentry_sdk.capture_exception(e)
            else:
                embed = default_embed(message=f"{reward.name} x{reward.amount}")
                embed.set_author(
                    name=text_map.get(87, "en-US", user.user_locale),
                    icon_url=user.discord_user.display_avatar.url,
                )
                embed.set_thumbnail(url=reward.icon)
                try:
                    await user.discord_user.send(embed=embed)
                except Forbidden:
                    pass
                error = False
                count += 1

            if error:
                await self.bot.db.execute(
                    "UPDATE user_accounts SET daily_checkin = 0 WHERE user_id = ? AND uid = ?",
                    (user.discord_user.id, user.uid),
                )
                embed = embed = error_embed(
                    message=f"{error_message}\n\n{text_map.get(630, 'en-US', user.user_locale)}"
                )
                embed.set_author(
                    name=text_map.get(500, "en-US", user.user_locale),
                    icon_url=user.discord_user.display_avatar.url,
                )
                embed.set_footer(text=text_map.get(611, "en-US", user.user_locale))
                try:
                    await user.discord_user.send(embed=embed)
                except Forbidden:
                    pass

            if user_count % 100 == 0:  # Sleep for 30 seconds every 100 users
                await asyncio.sleep(30)
            await asyncio.sleep(2.5)
        await self.bot.db.commit()

        log.info(f"[Schedule][Claim Reward] Ended ({count}/{user_count} users)")

        # send a notification to Seria
        seria = self.bot.get_user(410036441129943050) or await self.bot.fetch_user(
            410036441129943050
        )
        await seria.send(
            embed=default_embed(
                "Automatic daily check-in report", f"Claimed {count}/{user_count}"
            )
        )

    @schedule_error_handler
    async def weapon_talent_base_notifiction(
        self, notification_type: str, time_offset: Literal[0, -13, -7]
    ):
        log.info(f"[Schedule][{notification_type}][offset: {time_offset}] Start")
        list_name = (
            "weapon_list"
            if notification_type == "weapon_notification"
            else "character_list"
        )
        async with self.bot.db.execute(
            f"SELECT user_id, {list_name}, last_notif FROM {notification_type} WHERE toggle = 1"
        ) as c:
            count = 0
            async for row in c:
                user_id = row[0]
                item_list = row[1]
                now = get_dt_now() + timedelta(hours=time_offset)
                locale = await get_user_locale(user_id, self.bot.db) or "en-US"
                client = AmbrTopAPI(self.bot.session, to_ambr_top(locale))
                domains = await client.get_domain()
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                uid = await get_uid(user_id, self.bot.db)
                uid_tz = get_uid_tz(uid)
                if uid_tz != time_offset:
                    continue
                item_list = ast.literal_eval(item_list)
                notified = {}
                today_domains = [d for d in domains if d.weekday == now.weekday()]
                for item_id in item_list:
                    for domain in today_domains:
                        for reward in domain.rewards:
                            if notification_type == "talent_notification":
                                upgrade = await client.get_character_upgrade(
                                    str(item_id)
                                )
                            else:
                                upgrade = await client.get_weapon_upgrade(int(item_id))

                            if upgrade is None or isinstance(upgrade, List):
                                continue

                            if reward in upgrade.items:
                                if item_id not in notified:
                                    notified[item_id] = {
                                        "materials": [],
                                        "domain": domain,
                                    }
                                if reward.id not in notified[item_id]["materials"]:
                                    notified[item_id]["materials"].append(reward.id)

                for item_id, item_info in notified.items():
                    item = None
                    if notification_type == "talent_notification":
                        item = await client.get_character(item_id)
                    elif notification_type == "weapon_notification":
                        item = await client.get_weapon(int(item_id))
                    if not isinstance(item, (Character, Weapon)):
                        continue

                    materials = []
                    for material_id in item_info["materials"]:
                        material = await client.get_material(material_id)
                        if not isinstance(material, Material):
                            continue
                        materials.append((material, ""))

                    dark_mode = await get_user_appearance_mode(user_id, self.bot.db)
                    fp = await main_funcs.draw_material_card(
                        DrawInput(
                            loop=self.bot.loop,
                            session=self.bot.session,
                            locale=locale,
                            dark_mode=dark_mode,
                        ),
                        materials,
                        "",
                        draw_title=False,
                    )
                    fp.seek(0)
                    file = File(fp, "reminder_card.jpeg")
                    domain: Domain = item_info["domain"]
                    embed = default_embed()
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
                        await user.send(embed=embed, files=[file])
                    except Forbidden:
                        await c.execute(
                            f"UPDATE {notification_type} SET toggle = 0 WHERE user_id = ?",
                            (user_id,),
                        )
                    else:
                        await c.execute(
                            f"UPDATE {notification_type} SET last_notif = ? WHERE user_id = ?",
                            (now.strftime("%Y/%m/%d %H:%M:%S"), user_id),
                        )
                        count += 1
                await asyncio.sleep(2.5)
        await self.bot.db.commit()
        log.info(f"[Schedule][{notification_type}] Ended (Notified {count} users)")

    @schedule_error_handler
    async def update_game_data(self):
        """Updates genshin game data and adds emojis"""
        log.info("[Schedule][Update Game Data] Start")
        await genshin.utility.update_characters_ambr()
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

            for object in objects:
                english_name = ""
                if isinstance(object, Character):
                    object_map[str(object.id)] = {
                        "name": object.name,
                        "element": object.element,
                        "rarity": object.rairty,
                        "icon": object.icon,
                    }
                    eng_object = await eng_client.get_character(object.id)
                    if isinstance(eng_object, Character) and eng_object is not None:
                        english_name = eng_object.name
                elif isinstance(object, Weapon):
                    object_map[str(object.id)] = {
                        "name": object.name,
                        "rarity": object.rarity,
                        "icon": object.icon,
                    }
                    eng_object = await eng_client.get_weapon(object.id)
                    if isinstance(eng_object, Weapon) and eng_object is not None:
                        english_name = eng_object.name
                elif isinstance(object, Artifact):
                    object_map[str(object.id)] = {
                        "name": object.name,
                        "rarity": object.rarity_list,
                        "icon": object.icon,
                    }
                    eng_object = await eng_client.get_artifact(object.id)
                    if isinstance(eng_object, Artifact) and eng_object is not None:
                        english_name = eng_object.name

                object_map[str(object.id)]["eng"] = english_name
                object_id = str(object.id)
                if "-" in object_id:
                    object_id = (object_id.split("-"))[0]
                emoji = find(lambda e: e.name == object_id, self.bot.emojis)
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

    @schedule_error_handler
    async def update_text_map(self):
        """Updates genshin text map"""
        log.info("[Schedule][Update Text Map] Start")
        # character, weapon, material, artifact text map
        things_to_update = [
            "avatar",
            "weapon",
            "material",
            "reliquary",
            "food",
            "book",
            "furniture",
            "monster",
            "namecard",
        ]
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

        # item name text map
        huge_text_map = {}
        for thing in things_to_update:
            with open(f"text_maps/{thing}.json", "r", encoding="utf-8") as f:
                text_map = json.load(f)
            for item_id, item_info in text_map.items():
                for lang, name in item_info.items():
                    if "10000005" in item_id:
                        huge_text_map[name] = "10000005"
                    elif "10000007" in item_id:
                        huge_text_map[name] = "10000007"
                    else:
                        huge_text_map[name] = item_id
        with open(f"text_maps/item_name.json", "w+", encoding="utf-8") as f:
            json.dump(huge_text_map, f, indent=4, ensure_ascii=False)
        log.info("[Schedule][Update Text Map] Ended")

    @schedule_error_handler
    async def update_ambr_cache(self):
        """Updates data from ambr.top"""
        log.info("[Schedule][Update Ambr Cache] Start")
        client = AmbrTopAPI(self.bot.session)
        await client.update_cache(all_lang=True)
        await client.update_cache(static=True)
        log.info("[Schedule][Update Ambr Cache] Ended")

    @run_tasks.before_loop
    async def before_run_tasks(self):
        await self.bot.wait_until_ready()

    @change_status.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @is_seria()
    @app_commands.command(
        name="update-data", description="Update game data and text map"
    )
    async def update_data(self, i: Interaction):
        await i.response.defer(ephemeral=True)
        await asyncio.create_task(self.update_ambr_cache())
        await asyncio.create_task(self.update_text_map())
        await asyncio.create_task(self.update_game_data())
        await i.followup.send("Tasks created", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Schedule(bot))
