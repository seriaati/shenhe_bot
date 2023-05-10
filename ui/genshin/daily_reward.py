import asyncio
import calendar

import genshin
from discord import ButtonStyle, Locale
from discord.errors import InteractionResponded
from discord.ui import Button

import dev.asset as asset
import dev.config as config
from apps.genshin import GenshinApp
from apps.text_map import text_map
from dev.base_ui import BaseView
from dev.models import DefaultEmbed, ErrorEmbed, Inter
from utils import divide_chunks, get_dt_now


class View(BaseView):
    def __init__(
        self,
        locale: Locale | str,
        genshin_app: GenshinApp,
        uid: int,
        daily_checkin: bool,
    ):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        self.genshin_app = genshin_app
        self.uid = uid
        self.add_item(ClaimRewardOn(self.locale, daily_checkin))
        self.add_item(ClaimRewardOff(self.locale, not daily_checkin))
        self.add_item(ClaimReward(self.locale))

    async def start(self, i: Inter):
        try:
            await i.response.defer()
        except InteractionResponded:
            pass

        now = get_dt_now()
        day_in_month = calendar.monthrange(now.year, now.month)[1]
        shenhe_user = await self.genshin_app.get_user_cookie(i.user.id, i.user.id, i.locale)

        try:
            _, claimed_rewards = await shenhe_user.client.get_reward_info()
        except genshin.errors.InvalidCookies:
            embed = ErrorEmbed(description=text_map.get(35, self.locale))
            embed.set_author(
                name=text_map.get(36, self.locale),
                icon_url=i.user.display_avatar.url,
            )
            return await i.followup.send(embed=embed)

        embed = DefaultEmbed(
            description=f"{text_map.get(606, self.locale)}: {claimed_rewards}/{day_in_month}\n"
        )
        embed.set_author(
            name=text_map.get(604, self.locale),
            icon_url=i.user.display_avatar.url,
        )
        embed.set_footer(text=text_map.get(769, self.locale))

        values = []
        async for reward in shenhe_user.client.claimed_rewards(limit=claimed_rewards):
            values.append(
                f"{reward.time.month}/{reward.time.day} - {reward.name} x{reward.amount}\n"
            )
        divided_value = list(divide_chunks(values, 10))
        for index, val in enumerate(divided_value):
            r = "".join(val)
            embed.add_field(name=f"{text_map.get(605, self.locale)} ({index+1})", value=r)

        view = View(self.locale, self.genshin_app, shenhe_user.uid, shenhe_user.daily_checkin)
        view.message = await i.edit_original_response(embed=embed, view=view)
        view.author = i.user


class ClaimReward(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(style=ButtonStyle.green, label=text_map.get(603, locale))
        self.view: View

    async def callback(self, i: Inter):
        await i.response.defer()
        r = await self.view.genshin_app.claim_daily_reward(
            i.user.id, i.user.id, i.locale
        )
        self.view.disable_items()
        await i.edit_original_response(embed=r.result, view=self.view)
        await asyncio.sleep(2)
        await self.view.start(i)


class ClaimRewardOn(Button):
    def __init__(self, locale: Locale | str, on: bool):
        super().__init__(
            style=ButtonStyle.blurple if on else ButtonStyle.gray,
            label=text_map.get(99, locale),
            emoji=asset.gift_outline,
        )
        self.view: View

    async def callback(self, i: Inter):
        await i.client.pool.execute(
            "UPDATE user_accounts SET daily_checkin = true WHERE user_id = $1 AND uid = $2",
            i.user.id,
            self.view.uid,
        )
        await self.view.start(i)


class ClaimRewardOff(Button):
    def __init__(self, locale: Locale | str, on: bool):
        super().__init__(
            style=ButtonStyle.blurple if on else ButtonStyle.gray,
            label=text_map.get(100, locale),
            emoji=asset.gift_off_outline,
        )
        self.view: View

    async def callback(self, i: Inter):
        await i.client.pool.execute(
            "UPDATE user_accounts SET daily_checkin = false WHERE user_id = $1 AND uid = $2",
            i.user.id,
            self.view.uid,
        )
        await self.view.start(i)
