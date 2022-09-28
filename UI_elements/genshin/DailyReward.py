import asyncio
from apps.genshin.genshin_app import GenshinApp
import calendar
from datetime import datetime
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseView
import config
from discord import Locale, ButtonStyle, Interaction
from discord.errors import InteractionResponded
from discord.ui import Button
from apps.text_map.text_map_app import text_map
from utility.utils import default_embed, divide_chunks, error_embed
import genshin


class View(BaseView):
    def __init__(self, locale: Locale | str, genshin_app: GenshinApp):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        self.genshin_app = genshin_app
        self.add_item(ClaimReward(self.locale))


class ClaimReward(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(style=ButtonStyle.blurple, label=text_map.get(603, locale))

    async def callback(self, i: Interaction):
        await i.response.defer()
        self.view: View
        result, _ = await self.view.genshin_app.claim_daily_reward(i.user.id, i.locale)
        for item in self.view.children:
            item.disabled = True
        await i.edit_original_response(embed=result, view=self.view)
        await asyncio.sleep(2)
        await return_claim_reward(i, self.view.genshin_app)

async def return_claim_reward(i: Interaction, genshin_app: GenshinApp):
    try:
        await i.response.defer()
    except InteractionResponded:
        pass
    user_locale = await get_user_locale(i.user.id, i.client.db)
    locale = user_locale or i.locale
    day_in_month = calendar.monthrange(datetime.now().year, datetime.now().month)[1]
    shenhe_user = await genshin_app.get_user_cookie(i.user.id, i.locale)
    try:
        _, claimed_rewards = await shenhe_user.client.get_reward_info()
    except genshin.errors.InvalidCookies:
        embed = error_embed(message=text_map.get(35, locale))
        embed.set_author(
            name=text_map.get(36, locale),
            icon_url=i.user.display_avatar.url,
        )
        return await i.followup.send(embed=embed)
    embed = default_embed(message=f"{text_map.get(606, i.locale, user_locale)}: {claimed_rewards}/{day_in_month}")
    embed.set_author(
        name=text_map.get(604, i.locale, user_locale), icon_url=i.user.display_avatar.url
    )
    value = []
    async for reward in shenhe_user.client.claimed_rewards(limit=claimed_rewards):
        value.append(
            f"{reward.time.month}/{reward.time.day} - {reward.name} x{reward.amount}\n"
        )
    value = list(divide_chunks(value, 10))
    for index, val in enumerate(value):
        r = ''
        for v in val:
            r += v
        embed.add_field(name=f"{text_map.get(605, i.locale, user_locale)} ({index+1})", value=r)
    view = View(locale, genshin_app)
    try:
        await i.response.send_message(embed=embed, view=view)
    except InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)
    view.author = i.user
    view.message = await i.original_response()
