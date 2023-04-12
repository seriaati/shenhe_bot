import asyncio
from typing import Any, Dict, List, Union

import discord
import sentry_sdk

import dev.models as model
from apps.db.utility import get_user_lang
from apps.genshin.hoyolab import GenshinApp
from apps.text_map import text_map
from apps.text_map.convert_locale import to_genshin_py
from dev.enum import CheckInAPI
from dev.exceptions import CheckInAPIError
from utility.utils import get_dt_now, log


class DailyCheckin:
    def __init__(self, bot: model.BotModel) -> None:
        self.bot = bot
        self.total: Dict[CheckInAPI, int] = {}
        self.debug = self.bot.debug
        self.genshin_app = GenshinApp(self.bot)

    async def start(self) -> None:
        log.info("[DailyCheckin] Starting...")

        queue: asyncio.Queue[model.User] = asyncio.Queue()
        tasks = [self._add_user_to_queue(queue)]

        apis = [CheckInAPI.LOCAL, CheckInAPI.VERCEL, CheckInAPI.DETA, CheckInAPI.RENDER]
        for api in apis:
            tasks.append(self._daily_checkin_task(api, queue))

        await asyncio.gather(*tasks)

    async def _add_user_to_queue(self, queue: asyncio.Queue[model.User]) -> None:
        log.info("[DailyCheckin] Adding users to queue...")

        rows = await self.bot.pool.fetch(
            """
            SELECT * FROM user_accounts
            WHERE daily_checkin = true 
            AND ltuid IS NOT NULL
            AND ltoken IT NOT NULL
            """
        )
        for row in rows:
            user = model.User.from_row(row)
            if user.last_checkin_date != get_dt_now().day:
                await queue.put(user)

    async def _daily_checkin_task(
        self, api: CheckInAPI, queue: asyncio.Queue[model.User]
    ) -> None:
        log.info(f"[DailyCheckin] Starting {api.name} task...")

        if api is not CheckInAPI.LOCAL:
            if api.value is None:
                return

            async with self.bot.session.get(api.value) as resp:
                if resp.status != 200:
                    log.error(
                        f"[DailyCheckin] {api.name} returned {resp.status} status code"
                    )

        self.total[api] = 0
        MAX_API_ERROR = 5
        api_error_count = 0

        while not queue.empty():
            user = await queue.get()
            try:
                await self._daily_checkin(api, user)
            except CheckInAPIError as e:
                if e.api is not api:
                    raise e
                api_error_count += 1
                if api_error_count >= MAX_API_ERROR:
                    log.error(
                        f"[DailyCheckin] {api.name} has reached {MAX_API_ERROR} API errors"
                    )
                    return
                log.error(f"[DailyCheckin] {api.name} returned {e.status} status code")
                await queue.put(user)
                continue
            except Exception as e: # skipcq: PYL-W0703
                log.error(f"[DailyCheckin] {api.name} raised an exception", exc_info=e)
                sentry_sdk.capture_exception(e)
            else:
                self.total[api] += 1

    async def _daily_checkin(
        self, api: CheckInAPI, user: model.User
    ) -> model.ShenheEmbed:
        if api is CheckInAPI.LOCAL:
            result = await self.genshin_app.claim_daily_reward(
                user.user_id, user.user_id, discord.Locale.american_english
            )
            return result.result
        else:
            if api.value is None:
                raise CheckInAPIError(api, 404)

            user_lang = (await get_user_lang(user.user_id, self.bot.pool)) or "en-US"
            payload = {
                "cookie": {
                    "ltuid": user.ltuid,
                    "ltoken": user.ltoken,
                },
                "lang": to_genshin_py(str(user_lang)),
            }
            async with self.bot.session.post(api.value, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed = self._create_embed(user_lang, data)
                    return embed
                else:
                    raise CheckInAPIError(api, resp.status)

    def _create_embed(
        self, user_lang: str, data: Dict[str, Any]
    ) -> Union[model.DefaultEmbed, model.ErrorEmbed]:
        if "reward" in data:
            embed = model.DefaultEmbed(
                text_map.get(42, user_lang),
                f"""
                {text_map.get(41, user_lang).format(
                    reward=f'{data["reward"]["name"]} x{data["reward"]["amount"]}'
                )}
                
                > {text_map.get(211, user_lang)}
                """,
            )
            embed.set_thumbnail(url=data["reward"]["icon"])
        else:
            embed = model.ErrorEmbed()
            retcode = data["code"]
            message = data["msg"]
            if retcode == -5003:  # Already claimed
                embed.title = text_map.get(40, user_lang)
                embed.description = f"> {text_map.get(211, user_lang)}"
            elif retcode == -100:  # Invalid cookie
                embed.title = text_map.get(36, user_lang)
                embed.description = f"""
                {text_map.get(767, user_lang)}
                
                > {text_map.get(211, user_lang)}
                """
            else:
                embed.title = text_map.get(135, user_lang)
                embed.description = f"""
                ```
                {message}
                ```
                
                > {text_map.get(211, user_lang)}
                """
        embed.set_author(
            name=text_map.get(370, user_lang), icon_url=self.bot.user.display_avatar.url
        )
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

    async def _notify_results(self):
        pass
