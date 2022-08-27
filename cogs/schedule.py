import ast
import asyncio
import random
from datetime import datetime, timedelta

import aiosqlite
import sentry_sdk
from ambr.client import AmbrTopAPI
from apps.draw import draw_talent_reminder_card
from apps.genshin.genshin_app import GenshinApp
from discord import File
from apps.text_map.convert_locale import to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from discord import Forbidden, Game, Interaction, app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands, tasks
from discord.utils import format_dt, sleep_until
from utility.utils import default_embed, log

import genshin


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

    def cog_unload(self):
        self.claim_reward.cancel()
        self.resin_notification.cancel()
        self.talent_notification.cancel()
        self.change_status.cancel()
        self.pot_notification.cancel()

    @tasks.loop(minutes=10)
    async def change_status(self):
        status_list = [
            "/help",
            "discord.gg/ryfamUykRw",
            f"in {len(self.bot.guilds)} guilds",
            "shenhe.bot.nu",
        ]
        await self.bot.change_presence(activity=Game(name=random.choice(status_list)))

    @tasks.loop(hours=24)
    async def claim_reward(self):
        log.info("[Schedule] Claim Reward Start")
        try:
            count = 0
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute("SELECT user_id FROM genshin_accounts")
            users = await c.fetchall()
            for index, tuple in enumerate(users):
                user_id = tuple[0]
                client, uid, user, user_locale = await self.genshin_app.get_user_data(
                    user_id
                )
                client.lang = to_genshin_py(user_locale) or "ja-jp"
                try:
                    await client.claim_daily_reward()
                except genshin.errors.AlreadyClaimed:
                    count += 1
                except genshin.errors.InvalidCookies:
                    await c.execute(
                        "DELETE FROM genshin_accounts WHERE user_id = ?", (user_id,)
                    )
                except:
                    continue
                else:
                    count += 1
                await asyncio.sleep(3.0)
            await self.bot.db.commit()
        except Exception as e:
            sentry_sdk.capture_exception(e)
        else:
            log.info("[Schedule]Claim Reward Ended")

    @tasks.loop(hours=1)
    async def pot_notification(self):
        try:
            log.info("[Schedule] Pot Notification Start")
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute(
                "SELECT user_id, pot_threshold, pot_current_notif, pot_max_notif, last_pot_notif_time FROM genshin_accounts WHERE pot_notif_toggle = 1"
            )
            users = await c.fetchall()
            now = datetime.now()
            for index, tuple in enumerate(users):
                user_id = tuple[0]
                threshold = tuple[1]
                current_notif = tuple[2]
                max_notif = tuple[3]
                last_notif_time = tuple[4]
                last_notif_time = datetime.strptime(
                    last_notif_time, "%Y/%m/%d %H:%M:%S"
                )
                time_diff = now - last_notif_time
                if time_diff.total_seconds() < 7200:
                    continue

                client, uid, user, user_locale = await self.genshin_app.get_user_data(
                    user_id
                )
                try:
                    notes = await client.get_notes(uid)
                except genshin.errors.InvalidCookies:
                    await c.execute(
                        "DELETE FROM genshin_accounts WHERE user_id = ?", (user_id,)
                    )
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    await c.execute(
                        "UPDATE genshin_accounts SET pot_notif_toggle = 0 WHERE user_id = ?",
                        (user_id,),
                    )
                else:
                    coin = notes.current_realm_currency
                    locale = user_locale or "zh-TW"
                    if coin > threshold and current_notif < max_notif:
                        if notes.current_realm_currency == notes.max_realm_currency:
                            realm_recover_time = text_map.get(1, locale, user_locale)
                        else:
                            realm_recover_time = format_dt(
                                notes.realm_currency_recovery_time, "R"
                            )
                        embed = default_embed(
                            message=f"{text_map.get(14, locale)}: {coin}/{notes.max_realm_currency}\n"
                            f"{text_map.get(15, locale)}: {realm_recover_time}\n"
                            f"{text_map.get(302, locale)}: {threshold}\n"
                            f"{text_map.get(304, locale)}: {max_notif}"
                        )
                        embed.set_author(
                            name=text_map.get(518, locale), icon_url=user.avatar
                        )
                        embed.set_footer(text=text_map.get(305, locale))
                        try:
                            await user.send(embed=embed)
                        except Forbidden:
                            await c.execute(
                                "UPDATE genshin_accounts SET pot_notif_toggle = 0 WHERE user_id = ?",
                                (user_id,),
                            )
                        else:
                            await c.execute(
                                "UPDATE genshin_accounts SET pot_current_notif = ?, last_pot_notif_time = ? WHERE user_id = ?",
                                (
                                    current_notif + 1,
                                    datetime.strftime(now, "%Y/%m/%d %H:%M:%S"),
                                    user_id,
                                ),
                            )
                    if coin < threshold:
                        await c.execute(
                            "UPDATE genshin_accounts SET pot_current_notif = 0 WHERE user_id = ?",
                            (user_id,),
                        )

                await asyncio.sleep(3.0)
            await self.bot.db.commit()
            log.info("[Schedule] Pot Notification Ended")
        except Exception as e:
            sentry_sdk.capture_exception(e)

    @tasks.loop(hours=1)
    async def resin_notification(self):
        try:
            log.info("[Schedule] Resin Notification Start")
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute(
                "SELECT user_id, resin_threshold, current_notif, max_notif, last_resin_notif_time FROM genshin_accounts WHERE resin_notification_toggle = 1"
            )
            users = await c.fetchall()
            now = datetime.now()
            for index, tuple in enumerate(users):
                user_id = tuple[0]
                threshold = tuple[1]
                current_notif = tuple[2]
                max_notif = tuple[3]
                last_notif_time = tuple[4]
                last_notif_time = datetime.strptime(
                    last_notif_time, "%Y/%m/%d %H:%M:%S"
                )
                time_diff = now - last_notif_time
                if time_diff.total_seconds() < 7200:
                    continue

                client, uid, user, user_locale = await self.genshin_app.get_user_data(
                    user_id
                )
                try:
                    notes = await client.get_notes(uid)
                except genshin.errors.InvalidCookies:
                    await c.execute(
                        "DELETE FROM genshin_accounts WHERE user_id = ?", (user_id,)
                    )
                except:
                    await c.execute(
                        "UPDATE genshin_accounts SET resin_notification_toggle = 0 WHERE user_id = ?",
                        (user_id,),
                    )
                else:
                    locale = user_locale or "zh-TW"
                    resin = notes.current_resin
                    if resin >= threshold and current_notif < max_notif:
                        if resin == notes.max_resin:
                            resin_recover_time = text_map.get(1, locale, user_locale)
                        else:
                            resin_recover_time = format_dt(
                                notes.resin_recovery_time, "R"
                            )
                        embed = default_embed(
                            message=f"{text_map.get(303, locale)}: {notes.current_resin}/{notes.max_resin}\n"
                            f"{text_map.get(15, locale)}: {resin_recover_time}\n"
                            f"{text_map.get(302, locale)}: {threshold}\n"
                            f"{text_map.get(304, locale)}: {max_notif}"
                        )
                        embed.set_footer(text=text_map.get(305, locale))
                        embed.set_author(
                            name=text_map.get(306, locale), icon_url=user.avatar
                        )
                        try:
                            await user.send(embed=embed)
                        except Forbidden:
                            await c.execute(
                                "UPDATE genshin_accounts SET resin_notification_toggle = 0 WHERE user_id = ?",
                                (user_id,),
                            )
                        else:
                            await c.execute(
                                "UPDATE genshin_accounts SET current_notif = ?, last_resin_notif_time = ? WHERE user_id = ?",
                                (
                                    current_notif + 1,
                                    datetime.strftime(now, "%Y/%m/%d %H:%M:%S"),
                                    user_id,
                                ),
                            )
                    if resin < threshold:
                        await c.execute(
                            "UPDATE genshin_accounts SET current_notif = 0 WHERE user_id = ?",
                            (user_id,),
                        )
                await asyncio.sleep(3.0)
            await self.bot.db.commit()
            log.info("[Schedule] Resin Notifiaction Ended")
        except Exception as e:
            sentry_sdk.capture_exception(e)

    @tasks.loop(hours=24)
    async def talent_notification(self):
        try:
            log.info("[Schedule] Talent Notification Start")
            today_weekday = datetime.today().weekday()
            client = AmbrTopAPI(self.bot.session, "cht")
            domains = await client.get_domain()
            character_upgrades = await client.get_character_upgrade()
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute(
                "SELECT user_id, talent_notif_chara_list FROM genshin_accounts WHERE talent_notif_toggle = 1"
            )
            users = await c.fetchall()
            for index, tuple in enumerate(users):
                user_id = tuple[0]
                user = self.bot.get_user(user_id)
                user_locale = await get_user_locale(user_id, self.bot.db)
                user_notification_list = ast.literal_eval(tuple[1])
                notified = {}
                for character_id in user_notification_list:
                    for domain in domains:
                        if domain.weekday == today_weekday:
                            for item in domain.rewards:
                                for upgrade in character_upgrades:
                                    if upgrade.character_id != character_id:
                                        continue
                                    if item in upgrade.items:
                                        if character_id not in notified:
                                            notified[character_id] = []
                                        if item.id not in notified[character_id]:
                                            notified[character_id].append(item.id)

                for character_id, materials in notified.items():
                    [character] = await client.get_character(character_id)

                    fp = await draw_talent_reminder_card(materials, user_locale or 'zh-TW')
                    fp.seek(0)
                    file = File(fp, "reminder_card.jpeg")
                    embed = default_embed(
                        message=text_map.get(314, "zh-TW", user_locale)
                    )
                    embed.set_author(
                        name=text_map.get(313, "zh-TW", user_locale),
                        icon_url=character.icon,
                    )
                    embed.set_image(url="attachment://reminder_card.jpeg")

                    await user.send(embed=embed, files=[file])

            log.info("[Schedule] Talent Notifiaction Ended")
        except Exception as e:
            sentry_sdk.capture_exception(e)

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

    @app_commands.command(
        name="instantclaim", description=_("Admin usage only", hash=496)
    )
    async def instantclaim(self, i: Interaction):
        await i.response.defer(ephemeral=True)
        await self.claim_reward()
        await i.followup.send(
            embed=default_embed().set_author(name="claimed", icon_url=i.user.avatar),
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Schedule(bot))
