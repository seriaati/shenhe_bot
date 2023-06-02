import asyncio
import datetime
import io
import os
from typing import Any, Dict, List, Optional, Union

import discord
import sentry_sdk
from dotenv import load_dotenv
from genshin import GenshinException

import dev.asset as asset
import dev.models as model
from apps.db.tables.hoyo_account import HoyoAccount, convert_game_type
from apps.db.tables.user_settings import Settings
from apps.text_map import text_map
from apps.text_map.convert_locale import to_genshin_py
from dev.enum import CheckInAPI, GameType
from dev.exceptions import CheckInAPIError
from utils import get_dt_now, log
from utils.general import get_dc_user

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

        self._api_links = {
            CheckInAPI.VERCEL: os.getenv("VERCEL_URL"),
            CheckInAPI.DETA: os.getenv("DETA_URL"),
            CheckInAPI.RENDER: os.getenv("RENDER_URL"),
        }

    async def start(self) -> None:
        try:
            log.info("[DailyCheckin] Starting...")
            self._start_time = get_dt_now()

            # initialize the queue
            queue: asyncio.Queue[Optional[HoyoAccount]] = asyncio.Queue()

            # add users to queue
            tasks: List[asyncio.Task] = [
                asyncio.create_task(self._add_users_to_queue(queue))
            ]

            # add checkin tasks
            apis = [
                CheckInAPI.LOCAL,
                CheckInAPI.VERCEL,
                CheckInAPI.DETA,
                CheckInAPI.RENDER,
            ]
            for api in apis:
                tasks.append(asyncio.create_task(self._genshin_daily_task(api, queue)))

            # wait for all tasks to finish
            await asyncio.gather(*tasks)
            self._end_time = get_dt_now()

            await self._send_report()
        except Exception as e:  # skipcq: PYL-W0703
            sentry_sdk.capture_exception(e)
            log.warning(f"[DailyCheckin] {e}")
            owner = await get_dc_user(self.bot, self.bot.owner_id)
            await owner.send(f"An error occurred in DailyCheckin:\n```\n{e}\n```")
        finally:
            log.info("[DailyCheckin] Finished")

    async def _add_users_to_queue(
        self, queue: asyncio.Queue[Optional[HoyoAccount]]
    ) -> None:
        log.info("[DailyCheckin] Adding users to queue...")

        rows = await self.bot.pool.fetch(
            """
            SELECT * FROM hoyo_account
            WHERE (genshin_daily = true OR hsr_daily = true OR honkai_daily = true)
            """
        )
        for row in rows:
            user = await self.bot.db.users.get_by_row(row)
            if (
                self.bot.debug
                or user.last_checkin is None
                or user.last_checkin.day != get_dt_now().day
            ):
                if user.genshin_daily:
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

        await queue.put(None)

    async def _genshin_daily_task(
        self, api: CheckInAPI, queue: asyncio.Queue[Optional[HoyoAccount]]
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

        while True:
            user = await queue.get()
            if user is None:
                break
            try:
                embed = await self._do_genshin_daily(api, user)
                notif = await self.bot.db.settings.get(
                    user.user_id, Settings.NOTIFICATION
                )
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
                        user.user_id, user.uid, last_checkin=get_dt_now()
                    )
                    self._success[api] += 1
            finally:
                await asyncio.sleep(1.5)
                queue.task_done()

    async def _do_genshin_daily(
        self, api: CheckInAPI, user: HoyoAccount, retry_count: int = 0
    ) -> model.ShenheEmbed:
        lang = (await user.settings).lang or "en-US"
        if api is CheckInAPI.LOCAL:
            try:
                client = await user.client
                reward = await client.claim_daily_reward(
                    game=convert_game_type(user.checkin_game)
                )
            except GenshinException as e:
                data = {
                    "code": e.retcode,
                    "msg": e.msg,
                }
            else:
                data = {
                    "reward": {
                        "name": reward.name,
                        "amount": reward.amount,
                    }
                }
        else:
            api_link = self._api_links[api]
            if api_link is None:
                raise CheckInAPIError(api, 404)

            MAX_RETRY = 3

            cookie = await user.cookie
            payload = {
                "cookie": {
                    "ltuid": cookie.ltuid,
                    "ltoken": cookie.ltoken,
                    "cookie_token": cookie.cookie_token,
                },
                "lang": to_genshin_py(str(lang)),
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
                        return await self._do_genshin_daily(api, user, retry_count + 1)
                else:
                    raise CheckInAPIError(api, resp.status)

        embed = self._create_embed(lang, data)
        if isinstance(embed, model.ErrorEmbed):
            kwargs = {}
            if user.checkin_game is GameType.GENSHIN:
                kwargs["genshin_daily"] = False
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

    @staticmethod
    def _create_embed(
        lang: str, data: Dict[str, Any]
    ) -> Union[model.DefaultEmbed, model.ErrorEmbed]:
        if "reward" in data:
            embed = model.DefaultEmbed(
                text_map.get(42, lang),
                f"""
                {text_map.get(41, lang).format(
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
                embed.title = text_map.get(40, lang)
            elif retcode == -100:  # Invalid cookie
                embed = model.ErrorEmbed()
                embed.title = text_map.get(36, lang)
                embed.description = f"""
                {text_map.get(767, lang)}
                """
                embed.set_footer(text=text_map.get(630, lang))
            elif retcode == -10002:  # No game account found
                embed = model.ErrorEmbed()
                embed.title = text_map.get(772, lang)
            else:
                embed = model.ErrorEmbed()
                embed.title = text_map.get(135, lang)
                embed.description = f"""
                ```
                {message}
                ```
                """
                embed.set_footer(text=text_map.get(630, lang))

        if embed.description is None:
            embed.description = ""
        embed.description += f"\n\n{text_map.get(211, lang)}"
        game = GameType(data["game"])
        if game is GameType.HSR:
            game_name = text_map.get(770, lang)
            icon_url = asset.hsr_icon
        elif game is GameType.HONKAI:
            game_name = text_map.get(771, lang)
            icon_url = asset.honkai_icon
        else:  # GameType.GENSHIN
            game_name = text_map.get(313, lang)
            icon_url = asset.genshin_icon
        embed.set_author(
            name=f"{game_name} {text_map.get(370, lang)}", icon_url=icon_url
        )

        return embed

    async def _notify_user(self, user: HoyoAccount, embed: model.ShenheEmbed) -> None:
        dc_user = await get_dc_user(self.bot, user.user_id)
        embed.set_user_footer(dc_user, user.uid)
        try:
            await dc_user.send(embed=embed)
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

        bytes_io = None
        if self._errors:
            bytes_io = io.BytesIO()
            string = "\n".join(f"{k}: {v}" for k, v in self._errors.items())
            bytes_io.write(string.encode("utf-8"))
            bytes_io.seek(0)

        if bytes_io:
            file_ = discord.File(bytes_io, "errors.txt")
            await owner.send(embed=embed, file=file_)
        else:
            await owner.send(embed=embed)
