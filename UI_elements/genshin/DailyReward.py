import asyncio
import calendar

import genshin
from discord import ButtonStyle, Interaction, Locale
from discord.errors import InteractionResponded
from discord.ui import Button

import config
from apps.genshin.genshin_app import GenshinApp
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseView
from utility.utils import DefaultEmbed, divide_chunks, ErrorEmbed, get_dt_now


class View(BaseView):
    def __init__(self, locale: Locale | str, genshin_app: GenshinApp, uid: int):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        self.genshin_app = genshin_app
        self.uid = uid
        self.add_item(ClaimReward(self.locale))
        self.add_item(ClaimRewardToggle(self.locale))


class ClaimReward(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(style=ButtonStyle.blurple, label=text_map.get(603, locale))

    async def callback(self, i: Interaction):
        await i.response.defer()
        self.view: View
        result, _ = await self.view.genshin_app.claim_daily_reward(
            i.user.id, i.user.id, i.locale
        )
        for item in self.view.children:
            item.disabled = True  # type: ignore
        await i.edit_original_response(embed=result, view=self.view)
        await asyncio.sleep(2)
        await return_claim_reward(i, self.view.genshin_app)


class ClaimRewardToggle(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(label=text_map.get(627, locale), style=ButtonStyle.green)
        self.locale = locale

    async def callback(self, i: Interaction):
        self.view: View
        await i.client.pool.execute("UPDATE user_accounts SET daily_checkin = NOT daily_checkin WHERE user_id = $1 AND uid = $2", i.user.id, self.view.uid)

        for item in self.view.children:
            item.disabled = True  # type: ignore

        await return_claim_reward(i, self.view.genshin_app)


async def return_claim_reward(i: Interaction, genshin_app: GenshinApp):
    try:
        await i.response.defer()
    except InteractionResponded:
        pass

    locale = await get_user_locale(i.user.id, i.client.pool) or i.locale  # type: ignore
    now = get_dt_now()
    day_in_month = calendar.monthrange(now.year, now.month)[1]
    shenhe_user = await genshin_app.get_user_cookie(i.user.id, i.user.id, i.locale)

    try:
        _, claimed_rewards = await shenhe_user.client.get_reward_info()
    except genshin.errors.InvalidCookies:
        embed = ErrorEmbed(description=text_map.get(35, locale))
        embed.set_author(
            name=text_map.get(36, locale),
            icon_url=i.user.display_avatar.url,
        )
        return await i.followup.send(embed=embed)

    daily_checkin: bool = await i.client.pool.fetchval("SELECT daily_checkin FROM user_accounts WHERE user_id = $1 AND uid = $2", i.user.id, shenhe_user.uid)

    embed = DefaultEmbed(
        description=f"{text_map.get(606, locale)}: {claimed_rewards}/{day_in_month}\n"
        f"{text_map.get(101, locale)}: **__{text_map.get(99 if daily_checkin else 100, locale)}__**"
    )
    embed.set_author(
        name=text_map.get(604, locale),
        icon_url=i.user.display_avatar.url,
    )

    values = []
    async for reward in shenhe_user.client.claimed_rewards(limit=claimed_rewards):
        values.append(
            f"{reward.time.month}/{reward.time.day} - {reward.name} x{reward.amount}\n"
        )
    divided_value = list(divide_chunks(values, 10))
    for index, val in enumerate(divided_value):
        r = ""
        for v in val:
            r += v
        embed.add_field(name=f"{text_map.get(605, locale)} ({index+1})", value=r)

    view = View(locale, genshin_app, shenhe_user.uid)
    try:
        await i.response.send_message(embed=embed, view=view)
    except InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)
    view.author = i.user
    view.message = await i.original_response()
