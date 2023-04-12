import asyncio
import datetime
import os
from typing import Any, Dict, List, Union

import discord
import sentry_sdk
from dotenv import load_dotenv

import dev.models as model
from apps.db.utility import get_user_lang, get_user_notif
from apps.genshin.hoyolab import GenshinApp
from apps.text_map import text_map
from apps.text_map.convert_locale import to_genshin_py
from dev.enum import CheckInAPI
from dev.exceptions import CheckInAPIError
from utility.utils import get_dt_now, log

load_dotenv()


class DailyCheckin:
    def __init__(self, bot: model.BotModel) -> None:
        self.bot = bot

        self.total: Dict[CheckInAPI, int] = {}

        self.start_time: datetime.datetime
        self.end_time: datetime.datetime

        self.genshin_app = GenshinApp(self.bot)

        self.api_links = {
            CheckInAPI.VERCEL: os.getenv("VERCEL_URL"),
            CheckInAPI.DETA: os.getenv("DETA_URL"),
            CheckInAPI.RENDER: os.getenv("RENDER_URL"),
            CheckInAPI.RAILWAY: os.getenv("RAILWAY_URL"),
        }

    async def start(self) -> None:
        try:
            log.info("[DailyCheckin] Starting...")
            self.start_time = get_dt_now()

            # initialize the queue
            queue: asyncio.Queue[model.User] = asyncio.Queue()

            # add users to queue
            tasks: List[asyncio.Task] = [
                asyncio.create_task(self._add_user_to_queue(queue))
            ]

            # add checkin tasks
            apis = [
                CheckInAPI.LOCAL,
                CheckInAPI.VERCEL,
                CheckInAPI.DETA,
                CheckInAPI.RENDER,
                CheckInAPI.RAILWAY,
            ]
            for api in apis:
                tasks.append(asyncio.create_task(self._daily_checkin_task(api, queue)))

            # wait for all tasks to finish
            await asyncio.gather(*tasks)
            self.end_time = get_dt_now()

            await self._send_report()

            log.info("[DailyCheckin] Finished")
        except Exception as e: # skipcq: PYL-W0703
            sentry_sdk.capture_exception(e)
            log.error(f"[DailyCheckin] {e}")

    async def _add_user_to_queue(self, queue: asyncio.Queue[model.User]) -> None:
        log.info("[DailyCheckin] Adding users to queue...")

        rows = await self.bot.pool.fetch(
            """
            SELECT * FROM user_accounts
            WHERE daily_checkin = true
            AND ltuid IS NOT NULL
            AND ltoken IS NOT NULL
            """
        )
        for row in rows:
            user = model.User.from_row(row)
            if user.last_checkin_date != get_dt_now().day:
                await queue.put(user)

        log.info(f"[DailyCheckin] Added {queue.qsize()} users to queue")

    async def _daily_checkin_task(
        self, api: CheckInAPI, queue: asyncio.Queue[model.User]
    ) -> None:
        log.info(f"[DailyCheckin] Starting {api.name} task...")

        if api is not CheckInAPI.LOCAL:
            link = self.api_links[api]
            if link is None:
                return log.error(f"[DailyCheckin] {api.name} link is not set")

            async with self.bot.session.get(link) as resp:
                if resp.status != 200:
                    log.error(
                        f"[DailyCheckin] {api.name} returned {resp.status} status code"
                    )
                    raise CheckInAPIError(api, resp.status)

        self.total[api] = 0
        MAX_API_ERROR = 5
        api_error_count = 0

        while not queue.empty():
            user = await queue.get()
            try:
                embed = await self._do_daily_checkin(api, user)
                notif = await get_user_notif(user.user_id, self.bot.pool)
                if notif:
                    await self._notify_user(user, embed)
            except Exception as e:  # skipcq: PYL-W0703
                api_error_count += 1
                if api_error_count >= MAX_API_ERROR:
                    log.error(
                        f"[DailyCheckin] {api.name} has reached {MAX_API_ERROR} API errors"
                    )
                    return

                log.error(f"[DailyCheckin] {api.name} error: {e}")
                sentry_sdk.capture_exception(e)
                await queue.put(user)
                continue
            else:
                self.total[api] += 1
                await self.bot.pool.execute(
                    "UPDATE user_accounts SET last_checkin_date = $1 WHERE user_id = $2 AND uid = $3",
                    get_dt_now(),
                    user.user_id,
                    user.uid,
                )

    async def _do_daily_checkin(
        self, api: CheckInAPI, user: model.User
    ) -> model.ShenheEmbed:
        if api is CheckInAPI.LOCAL:
            result = await self.genshin_app.claim_daily_reward(
                user.user_id, user.user_id, discord.Locale.american_english
            )
            return result.result
        api_link = self.api_links[api]
        if api_link is None:
            raise CheckInAPIError(api, 404)

        user_lang = (await get_user_lang(user.user_id, self.bot.pool)) or "en-US"
        payload = {
            "cookie": {
                "ltuid": user.ltuid,
                "ltoken": user.ltoken,
                "cookie_token": user.cookie_token,
            },
            "lang": to_genshin_py(str(user_lang)),
        }
        async with self.bot.session.post(
            url=f"{api_link}/checkin/", json=payload
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                embed = self._create_embed(user_lang, data)
                return embed
            raise CheckInAPIError(api, resp.status)

    @staticmethod
    def _create_embed(
        user_lang: str, data: Dict[str, Any]
    ) -> Union[model.DefaultEmbed, model.ErrorEmbed]:
        if "reward" in data:
            embed = model.DefaultEmbed(
                text_map.get(42, user_lang),
                f"""
                {text_map.get(41, user_lang).format(
                    reward=f'{data["reward"]["name"]} x{data["reward"]["amount"]}'
                )}
                
                *{text_map.get(211, user_lang)}*
                """,
            )
            embed.set_thumbnail(url=data["reward"]["icon"])
        else:
            embed = model.ErrorEmbed()
            retcode = data["code"]
            message = data["msg"]
            if retcode == -5003:  # Already claimed
                embed.title = text_map.get(40, user_lang)
                embed.description = f"*{text_map.get(211, user_lang)}*"
            elif retcode == -100:  # Invalid cookie
                embed.title = text_map.get(36, user_lang)
                embed.description = f"""
                {text_map.get(767, user_lang)}
                
                *{text_map.get(211, user_lang)}*
                """
            else:
                embed.title = text_map.get(135, user_lang)
                embed.description = f"""
                ```
                {message}
                ```
                
                *{text_map.get(211, user_lang)}*
                """
        embed.set_author(name=text_map.get(370, user_lang))
        return embed

    async def _notify_user(self, user: model.User, embed: model.ShenheEmbed) -> None:
        discord_user = self.bot.get_user(user.user_id) or await self.bot.fetch_user(
            user.user_id
        )
        embed.set_user_footer(discord_user, user.uid)
        try:
            await discord_user.send(embed=embed)
        except discord.Forbidden:
            log.error(f"[DailyCheckin] Failed to send message to {user.user_id}")
        except Exception as e:  # skipcq: PYL-W0703
            sentry_sdk.capture_exception(e)

    async def _send_report(self) -> None:
        owner = self.bot.get_user(self.bot.owner_id) or await self.bot.fetch_user(
            self.bot.owner_id
        )

        each_api = "\n".join(f"{api.name}: {self.total[api]}" for api in CheckInAPI)
        embed = model.DefaultEmbed(
            "Daily Checkin Report",
            f"""
            {each_api}
            Total: {sum(self.total.values())}
            
            Start time: {self.start_time}
            End time: {self.end_time}
            Time taken: {self.end_time - self.start_time}
            """,
        )
        embed.timestamp = get_dt_now()
        await owner.send(embed=embed)
