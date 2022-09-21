import ast
import asyncio
import json
import random
from datetime import datetime, timedelta
import aiosqlite
import sentry_sdk
from ambr.client import AmbrTopAPI
from apps.genshin.genshin_app import GenshinApp
from apps.text_map.convert_locale import to_ambr_top_dict, to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from discord import File, Forbidden, Game, Interaction, app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands, tasks
from discord.utils import format_dt, sleep_until
from cogs.admin import is_seria
from utility.utils import default_embed, log
from yelan.draw import draw_talent_reminder_card

import genshin


def schedule_error_handler(func):
    async def inner_function(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except Exception as e:
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
        if not self.bot.debug:
            self.update_text_map.start()

    def cog_unload(self):
        self.claim_reward.cancel()
        self.resin_notification.cancel()
        self.talent_notification.cancel()
        self.change_status.cancel()
        self.pot_notification.cancel()
        if not self.bot.debug:
            self.update_text_map.cancel()

    @tasks.loop(minutes=10)
    async def change_status(self):
        status_list = [
            "/help",
            "shenhe.bot.nu",
        ]
        await self.bot.change_presence(activity=Game(name=f"{random.choice(status_list)} | {len(self.bot.guilds)} guilds"))

    @tasks.loop(hours=24)
    @schedule_error_handler
    async def claim_reward(self):
        log.info("[Schedule] Claim Reward Start")
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute("SELECT user_id FROM user_accounts WHERE ltuid IS NOT NULL")
        users = await c.fetchall()
        log.info(users)
        count = 0
        for _, tpl in enumerate(users):
            user_id = tpl[0]
            shenhe_user = await self.genshin_app.get_user_cookie(user_id)
            client = shenhe_user.client
            client.lang = to_genshin_py(shenhe_user.user_locale) or "en-us"
            try:
                await client.claim_daily_reward()
            except genshin.errors.AlreadyClaimed:
                break
            except genshin.errors.InvalidCookies:
                log.warning(f"[Schedule] Invalid Cookies: {user_id}")
                break
            except genshin.errors.GenshinException as e:
                if e.retcode == -10002:
                    break
                elif e.retcode == -1004:
                    log.warning(f"[Schedule][Claim Reward] We have been rate limited")
                    await asyncio.sleep(20)
                    for index in range(5):
                        log.info(f"[Schedule][Claim Reward] Retry {index + 1}")
                        try:
                            await client.claim_daily_reward()
                        except genshin.errors.AlreadyClaimed:
                            break
                        await asyncio.sleep(20*index)
                else:
                    log.warning(f"[Schedule] Claim Reward Error: {e}")
                    sentry_sdk.capture_exception(e)
                    break
            except Exception as e:
                log.warning(f"[Schedule] Claim Reward Error: {e}")
                sentry_sdk.capture_exception(e)
                break
            else:
                count += 1
            await asyncio.sleep(5)
        await self.bot.db.commit()
        log.info(f"[Schedule] Claim Reward Ended ({count}/{len(users)} users)")

    @tasks.loop(hours=1)
    @schedule_error_handler
    async def pot_notification(self):
        log.info("[Schedule] Pot Notification Start")
        now = datetime.now()
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute(
            "SELECT user_id, uid FROM user_accounts WHERE ltuid IS NOT NULL"
        )
        users = await c.fetchall()
        count = 0
        for _, tpl in enumerate(users):
            user_id = tpl[0]
            uid = tpl[1]
            await c.execute(
                "SELECT user_id, threshold, current, max, last_notif_time FROM pot_notification WHERE toggle = 1 AND user_id = ? AND uid = ?",
                (user_id, uid),
            )
            data = await c.fetchone()
            if data is None:
                continue
            user_id, threshold, current, max, last_notif_time = data
            last_notif_time = now - timedelta(1) if not last_notif_time else datetime.strptime(last_notif_time, "%Y/%m/%d %H:%M:%S")
            time_diff = now - last_notif_time
            if time_diff.total_seconds() < 7200:
                continue

            shenhe_user = await self.genshin_app.get_user_cookie(user_id)
            try:
                notes = await shenhe_user.client.get_notes(shenhe_user.uid)
            except genshin.errors.InvalidCookies:
                log.warning(f"[Schedule] Invalid Cookies for {user_id}")
                continue
            except Exception as e:
                log.warning(f"[Schedule] Pot Notification Error: {e}")
                continue
            coin = notes.current_realm_currency
            locale = shenhe_user.user_locale or "en-US"
            if coin >= threshold and current < max:
                if notes.current_realm_currency == notes.max_realm_currency:
                    realm_recover_time = text_map.get(
                        1, locale, shenhe_user.user_locale
                    )
                else:
                    realm_recover_time = format_dt(
                        notes.realm_currency_recovery_time, "R"
                    )
                embed = default_embed(
                    message=f"{text_map.get(14, locale)}: {coin}/{notes.max_realm_currency}\n"
                    f"{text_map.get(15, locale)}: {realm_recover_time}\n"
                )
                embed.set_author(
                    name=text_map.get(518, locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                )
                embed.set_footer(text=text_map.get(305, locale))
                try:
                    await shenhe_user.discord_user.send(embed=embed)
                except Forbidden:
                    await c.execute(
                        "UPDATE pot_notification SET toggle = 0 WHERE user_id = ? AND uid = ?",
                        (user_id, uid),
                    )
                else:
                    await c.execute(
                        "UPDATE pot_notification SET current = ?, last_notif_time = ? WHERE user_id = ? AND uid = ?",
                        (
                            current + 1,
                            datetime.strftime(now, "%Y/%m/%d %H:%M:%S"),
                            user_id,
                            uid,
                        ),
                    )
                    count += 1
            if coin < threshold:
                await c.execute(
                    "UPDATE pot_notification SET current = 0 WHERE user_id = ? AND uid = ?",
                    (user_id, uid),
                )
            await asyncio.sleep(3)
        await self.bot.db.commit()
        log.info(f"[Schedule] Pot Notification Ended (Notified {count}/{len(users)} users)")

    @tasks.loop(hours=1)
    @schedule_error_handler
    async def resin_notification(self):
        log.info("[Schedule] Resin Notification Start")
        now = datetime.now()
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute(
            "SELECT user_id, uid FROM user_accounts WHERE ltuid IS NOT NULL"
        )
        users = await c.fetchall()
        count = 0
        for _, tpl in enumerate(users):
            user_id = tpl[0]
            uid = tpl[1]
            await c.execute(
                "SELECT user_id, threshold, current, max, last_notif_time FROM resin_notification WHERE toggle = 1 AND user_id = ? AND uid = ?",
                (user_id, uid),
            )
            data = await c.fetchone()
            if data is None:
                continue
            user_id, threshold, current, max, last_notif_time = data
            last_notif_time = now - timedelta(1) if not last_notif_time else datetime.strptime(last_notif_time, "%Y/%m/%d %H:%M:%S")
            time_diff = now - last_notif_time
            if time_diff.total_seconds() < 7200:
                continue

            shenhe_user = await self.genshin_app.get_user_cookie(user_id)
            try:
                notes = await shenhe_user.client.get_notes(shenhe_user.uid)
            except genshin.errors.InvalidCookies:
                log.warning(f"[Schedule] Invalid Cookies for {user_id}")
                continue
            except Exception as e:
                log.warning(f"[Schedule] Resin Notification Error: {e}")
                continue
            locale = shenhe_user.user_locale or "en-US"
            resin = notes.current_resin
            if resin >= threshold and current < max:
                if resin == notes.max_resin:
                    resin_recover_time = text_map.get(
                        1, locale, shenhe_user.user_locale
                    )
                else:
                    resin_recover_time = format_dt(notes.resin_recovery_time, "R")
                embed = default_embed(
                    message=f"{text_map.get(303, locale)}: {notes.current_resin}/{notes.max_resin}\n"
                    f"{text_map.get(15, locale)}: {resin_recover_time}"
                )
                embed.set_footer(text=text_map.get(305, locale))
                embed.set_author(
                    name=text_map.get(306, locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                )
                try:
                    await shenhe_user.discord_user.send(embed=embed)
                except Forbidden:
                    await c.execute(
                        "UPDATE resin_notification SET toggle = 0 WHERE user_id = ? AND uid = ?",
                        (user_id, uid),
                    )
                else:
                    await c.execute(
                        "UPDATE resin_notification SET current = ?, last_notif_time = ? WHERE user_id = ? AND uid = ?",
                        (
                            current + 1,
                            datetime.strftime(now, "%Y/%m/%d %H:%M:%S"),
                            user_id,
                            uid,
                        ),
                    )
                    count += 1
            if resin < threshold:
                await c.execute(
                    "UPDATE resin_notification SET current = 0 WHERE user_id = ? AND uid = ?",
                    (user_id, uid),
                )
            await asyncio.sleep(3.0)
        await self.bot.db.commit()
        log.info(f"[Schedule] Resin Notifiaction Ended (Notified {count}/{len(users)} users)")

    @tasks.loop(hours=24)
    @schedule_error_handler
    async def talent_notification(self):
        log.info("[Schedule] Talent Notification Start")
        today_weekday = datetime.today().weekday()
        client = AmbrTopAPI(self.bot.session, "cht")
        domains = await client.get_domain()
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute(
            "SELECT user_id, character_list FROM talent_notification WHERE toggle = 1"
        )
        users = await c.fetchall()
        count = 0
        for _, tpl in enumerate(users):
            user_id = tpl[0]
            user = (self.bot.get_user(user_id)) or await self.bot.fetch_user(user_id)
            user_locale = await get_user_locale(user_id, self.bot.db)
            user_notification_list = ast.literal_eval(tpl[1])
            notified = {}
            for character_id in user_notification_list:
                for domain in domains:
                    if domain.weekday == today_weekday:
                        for item in domain.rewards:
                            [upgrade] = await client.get_character_upgrade(character_id)
                            if item in upgrade.items:
                                if character_id not in notified:
                                    notified[character_id] = []
                                if item.id not in notified[character_id]:
                                    notified[character_id].append(item.id)

            for character_id, materials in notified.items():
                [character] = await client.get_character(character_id)

                fp = await draw_talent_reminder_card(materials, user_locale or "zh-TW")
                fp.seek(0)
                file = File(fp, "reminder_card.jpeg")
                embed = default_embed(message=text_map.get(314, "zh-TW", user_locale))
                embed.set_author(
                    name=text_map.get(313, "zh-TW", user_locale),
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
                    count += 1

        log.info(f"[Schedule] Talent Notifiaction Ended (Notified {count}/{len(users)} users)")

    @tasks.loop(hours=24)
    @schedule_error_handler
    async def update_text_map(self):
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
                dict["10000005"] = {
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

    @claim_reward.before_loop
    async def before_claiming_reward(self):
        await self.bot.wait_until_ready()
        now = datetime.now().astimezone()
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
        await asyncio.sleep(120)

    @talent_notification.before_loop
    async def before_notif(self):
        await self.bot.wait_until_ready()
        now = datetime.now().astimezone()
        next_run = now.replace(hour=1, minute=20, second=0)  # 等待到早上1點20
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)

    @change_status.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @update_text_map.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()
        now = datetime.now().astimezone()
        next_run = now.replace(hour=2, minute=0, second=0)  # 等待到早上2點
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)

    @is_seria()
    @app_commands.command(
        name="instantclaim", description=_("Admin usage only", hash=496)
    )
    async def instantclaim(self, i: Interaction):
        await i.response.send_message('started, check console', ephemeral=True)
        await self.claim_reward()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Schedule(bot))
