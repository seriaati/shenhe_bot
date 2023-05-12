import asyncio
import datetime
import io
import os
from typing import Any, Dict, List, Union

import discord
import sentry_sdk
from dotenv import load_dotenv

import dev.asset as asset
import dev.models as model
from apps.db.tables.user_account import UserAccount
from apps.genshin.hoyolab import GenshinApp
from apps.text_map import text_map
from apps.text_map.convert_locale import to_genshin_py
from dev.enum import CheckInAPI, GameType
from dev.exceptions import CheckInAPIError
from utils import get_dt_now, get_user_notif, log

load_dotenv()


class DailyCheckin:
    def __init__(self, bot: model.BotModel) -> None:
        self.bot = bot

        self._success: Dict[CheckInAPI, int] = {}
        self._total: Dict[CheckInAPI, int] = {}
        self._errors: Dict[str, int] = {}

        self._genshin_count: int = 0
        self._honkai_count: int = 0
        self._hsr_count: int = 0

        self._start_time: datetime.datetime
        self._end_time: datetime.datetime

        self._genshin_app = GenshinApp(self.bot)

        self._api_links = {
            CheckInAPI.VERCEL: os.getenv("VERCEL_URL"),
            CheckInAPI.DETA: os.getenv("DETA_URL"),
            CheckInAPI.RENDER: os.getenv("RENDER_URL"),
            CheckInAPI.RAILWAY: os.getenv("RAILWAY_URL"),
        }

    async def start(self) -> None:
        try:
            log.info("[DailyCheckin] Starting...")
            self._start_time = get_dt_now()

            # initialize the queue
            queue: asyncio.Queue[UserAccount] = asyncio.Queue()

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
            self._end_time = get_dt_now()

            await self._send_report()

            log.info("[DailyCheckin] Finished")
        except Exception as e:  # skipcq: PYL-W0703
            sentry_sdk.capture_exception(e)
            log.warning(f"[DailyCheckin] {e}")

    async def _add_user_to_queue(self, queue: asyncio.Queue[UserAccount]) -> None:
        log.info("[DailyCheckin] Adding users to queue...")

        rows = await self.bot.pool.fetch(
            """
            SELECT * FROM user_accounts
            WHERE (daily_checkin = true OR hsr_daily = true OR honkai_daily = true)
            AND ltuid IS NOT NULL
            AND ltoken IS NOT NULL
            """
        )
        for row in rows:
            user = UserAccount(**row)
            if (
                self.bot.debug
                or user.last_checkin_date is None
                or user.last_checkin_date.day != get_dt_now().day
            ):
                if user.daily_checkin:
                    self._genshin_count += 1
                    user = user.copy(update={"checkin_game": GameType.GENSHIN})
                    await queue.put(user)
                if user.honkai_daily:
                    self._honkai_count += 1
                    user = user.copy(update={"checkin_game": GameType.HONKAI})
                    await queue.put(user)
                if user.hsr_daily:
                    self._hsr_count += 1
                    user = user.copy(update={"checkin_game": GameType.HSR})
                    await queue.put(user)

        log.info(f"[DailyCheckin] Added {queue.qsize()} users to queue")

    async def _daily_checkin_task(
        self, api: CheckInAPI, queue: asyncio.Queue[UserAccount]
    ) -> None:
        log.info(f"[DailyCheckin] Starting {api.name} task...")

        if api is not CheckInAPI.LOCAL:
            link = self._api_links[api]
            if link is None:
                return log.warning(f"[DailyCheckin] {api.name} link is not set")

            async with self.bot.session.get(link) as resp:
                if resp.status != 200:
                    log.warning(
                        f"[DailyCheckin] {api.name} returned {resp.status} status code"
                    )
                    return

        self._total[api] = 0
        self._success[api] = 0
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
                log.warning(f"[DailyCheckin] {api.name} error: {e}")
                sentry_sdk.capture_exception(e)
                await queue.put(user)

                if api_error_count >= MAX_API_ERROR:
                    log.warning(
                        f"[DailyCheckin] {api.name} has reached {MAX_API_ERROR} API errors"
                    )
                    return
            else:
                self._total[api] += 1
                if isinstance(embed, model.DefaultEmbed):
                    await self.bot.db.users.update(
                        user.user_id, user.uid, last_checkin_date=get_dt_now()
                    )
                    self._success[api] += 1
            finally:
                await asyncio.sleep(1.5)

    async def _do_daily_checkin(
        self, api: CheckInAPI, user: UserAccount, retry_count: int = 0
    ) -> model.ShenheEmbed:
        if api is CheckInAPI.LOCAL:
            result = await self._genshin_app.claim_daily_reward(
                user.user_id, user.user_id, discord.Locale.american_english
            )
            return result.result
        api_link = self._api_links[api]
        if api_link is None:
            raise CheckInAPIError(api, 404)

        MAX_RETRY = 3

        user_lang = (await user.fetch_lang(self.bot.pool)) or "en-US"
        payload = {
            "cookie": {
                "ltuid": user.ltuid,
                "ltoken": user.ltoken,
                "cookie_token": user.cookie_token,
            },
            "lang": to_genshin_py(str(user_lang)),
            "game": user.checkin_game.value,
        }

        async with self.bot.session.post(
            url=f"{api_link}/checkin/", json=payload
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if "msg" in data and "Too many" in data["msg"]:
                    if retry_count >= MAX_RETRY:
                        sentry_sdk.capture_message(
                            f"[DailyCheckin] {api.name} retry limit reached, user: {user}"
                        )
                        raise CheckInAPIError(api, 429)
                    await asyncio.sleep(5 * (retry_count + 1))
                    return await self._do_daily_checkin(api, user, retry_count + 1)

                embed = self._create_embed(user_lang, data)
                if isinstance(embed, model.ErrorEmbed):
                    kwargs = {}
                    if user.checkin_game is GameType.GENSHIN:
                        kwargs["daily_checkin"] = False
                    elif user.checkin_game is GameType.HONKAI:
                        kwargs["honkai_daily"] = False
                    elif user.checkin_game is GameType.HSR:
                        kwargs["hsr_daily"] = False
                    await self.bot.db.users.update(user.user_id, user.uid, **kwargs)

                    error_id = f"{data['code']} {data['msg']}"
                    if error_id not in self._errors:
                        self._errors[error_id] = 0
                    self._errors[error_id] += 1

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
                """,
            )
            embed.set_thumbnail(url=data["reward"]["icon"])
        else:
            retcode = data["code"]
            message = data["msg"]
            if retcode == -5003:  # Already claimed
                embed = model.DefaultEmbed()
                embed.title = text_map.get(40, user_lang)
            elif retcode == -100:  # Invalid cookie
                embed = model.ErrorEmbed()
                embed.title = text_map.get(36, user_lang)
                embed.description = f"""
                {text_map.get(767, user_lang)}
                """
                embed.set_footer(text=text_map.get(630, user_lang))
            elif retcode == -10002:  # No game account found
                embed = model.ErrorEmbed()
                embed.title = text_map.get(772, user_lang)
            else:
                embed = model.ErrorEmbed()
                embed.title = text_map.get(135, user_lang)
                embed.description = f"""
                ```
                {message}
                ```
                """
                embed.set_footer(text=text_map.get(630, user_lang))

        if embed.description is None:
            embed.description = ""
        embed.description += f"\n\n{text_map.get(211, user_lang)}"
        game = GameType(data["game"])
        if game is GameType.HSR:
            game_name = text_map.get(770, user_lang)
            icon_url = asset.hsr_icon
        elif game is GameType.HONKAI:
            game_name = text_map.get(771, user_lang)
            icon_url = asset.honkai_icon
        else:  # GameType.GENSHIN
            game_name = text_map.get(313, user_lang)
            icon_url = asset.genshin_icon
        embed.set_author(
            name=f"{game_name} {text_map.get(370, user_lang)}", icon_url=icon_url
        )

        return embed

    async def _notify_user(self, user: UserAccount, embed: model.ShenheEmbed) -> None:
        discord_user = self.bot.get_user(user.user_id) or await self.bot.fetch_user(
            user.user_id
        )
        embed.set_user_footer(discord_user, user.uid)
        try:
            await discord_user.send(embed=embed)
        except discord.Forbidden:
            pass
        except Exception as e:  # skipcq: PYL-W0703
            sentry_sdk.capture_exception(e)

    async def _send_report(self) -> None:
        owner = self.bot.get_user(410036441129943050)
        if owner is None:
            owner = await self.bot.fetch_user(410036441129943050)

        each_api = "\n".join(
            f"{api.name}: {self._success[api]}/{self._total[api]}" for api in CheckInAPI
        )
        embed = model.DefaultEmbed(
            "Daily Checkin Report",
            f"""
            {each_api}
            Total: {sum(self._success.values())}/{sum(self._total.values())}
            
            Genshin: {self._genshin_count}
            Honkai: {self._honkai_count}
            Star Rail: {self._hsr_count}
            
            Start time: {self._start_time}
            End time: {self._end_time}
            Time taken: {self._end_time - self._start_time}
            """,
        )
        embed.timestamp = get_dt_now()

        bytes_io = io.BytesIO()
        string = "\n".join(f"{k}: {v}" for k, v in self._errors.items())
        bytes_io.write(string.encode("utf-8"))
        bytes_io.seek(0)

        await owner.send(embed=embed, file=discord.File(bytes_io, "errors.txt"))
