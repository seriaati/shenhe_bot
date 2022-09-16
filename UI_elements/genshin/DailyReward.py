import asyncio
from apps.genshin.genshin_app import GenshinApp
import calendar
from datetime import datetime
from apps.text_map.utils import get_user_locale
from debug import DefaultView
import config
from discord import Locale, ButtonStyle, Interaction
from discord.errors import InteractionResponded
from discord.ui import Button
from apps.text_map.text_map_app import text_map
from utility.utils import default_embed


class View(DefaultView):
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
    value = ""
    _, claimed_rewards = await shenhe_user.client.get_reward_info()
    embed = default_embed()
    embed.set_author(
        name=text_map.get(604, i.locale, user_locale), icon_url=i.user.display_avatar.url
    )
    embed.add_field(
        name=text_map.get(606, i.locale, user_locale),
        value=f"{claimed_rewards}/{day_in_month}",
    )
    count = 0
    async for reward in shenhe_user.client.claimed_rewards(limit=claimed_rewards):
        count += 1
        value += (
            f"{reward.time.month}/{reward.time.day} - {reward.name} x{reward.amount}\n"
        )
        if count//10 == 1:
            embed.add_field(
                name=f"{text_map.get(605, i.locale, user_locale)} ({count//10})", value=value, inline=False
            )
            value = ""
            count = 0
    view = View(locale, genshin_app)
    try:
        await i.response.send_message(embed=embed, view=view)
    except InteractionResponded:
        await i.edit_original_response(embed=embed, view=view)
    view.author = i.user
    view.message = await i.original_response()
