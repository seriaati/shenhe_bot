import asyncio
import calendar
from typing import Dict, Union

from discord import ButtonStyle, ui
from discord.errors import InteractionResponded

import dev.asset as asset
import dev.config as config
from apps.db.tables.hoyo_account import HoyoAccount, convert_game_type
from apps.text_map import text_map
from dev.base_ui import BaseView
from dev.enum import GameType
from dev.models import DefaultEmbed, Inter
from utils import divide_chunks, get_dt_now


class View(BaseView):
    def __init__(self):
        super().__init__(timeout=config.mid_timeout)
        self.lang: str
        self.uid: int
        self.user: HoyoAccount
        self.daily_checkin: bool
        self.game: GameType

    async def start(self, i: Inter):
        try:
            await i.response.defer()
        except InteractionResponded:
            pass

        self.user = await i.client.db.users.get(i.user.id)
        self.game = self.user.game
        self.recognize_daily_checkin()

        lang = (await self.user.settings).lang
        self.lang = lang or str(i.locale)

        self.add_components()
        await self.update(i)

        self.author = i.user
        self.message = await i.original_response()

    def recognize_daily_checkin(self) -> None:
        if self.game is GameType.HONKAI:
            self.daily_checkin = self.user.honkai_daily
        elif self.game is GameType.HSR:
            self.daily_checkin = self.user.hsr_daily
        else:
            self.daily_checkin = self.user.genshin_daily

    def add_components(self) -> None:
        self.clear_items()
        self.add_item(ClaimRewardOn(self.lang, self.daily_checkin))
        self.add_item(ClaimRewardOff(self.lang, self.daily_checkin))
        self.add_item(ClaimReward(self.lang))

    async def update(self, i: Inter) -> None:
        now = get_dt_now()
        day_in_month = calendar.monthrange(now.year, now.month)[1]

        client = await self.user.client
        _, claimed_rewards = await client.get_reward_info(
            game=convert_game_type(self.game)
        )

        embed = DefaultEmbed(
            description=f"{text_map.get(606, self.lang)}: {claimed_rewards}/{day_in_month}\n"
        )
        embed.set_author(
            name=text_map.get(604, self.lang),
            icon_url=i.user.display_avatar.url,
        )
        embed.set_footer(text=text_map.get(769, self.lang))

        values = []
        client = await self.user.client
        async for reward in client.claimed_rewards(
            limit=claimed_rewards, game=convert_game_type(self.game)
        ):
            values.append(
                f"{reward.time.month}/{reward.time.day} - {reward.name} x{reward.amount}\n"
            )
        divided_value = list(divide_chunks(values, 10))
        for index, val in enumerate(divided_value):
            r = "".join(val)
            embed.add_field(
                name=f"{text_map.get(605, self.lang)} ({index+1})", value=r
            )

        await i.edit_original_response(embed=embed, view=self)

    def create_kwargs(self, toggle: bool) -> Dict[str, bool]:
        kwargs = {}
        if self.game is GameType.HSR:
            kwargs["hsr_daily"] = toggle
        elif self.game is GameType.HONKAI:
            kwargs["honkai_daily"] = toggle
        elif self.game is GameType.GENSHIN:
            kwargs["genshin_daily"] = toggle

        return kwargs


class ClaimReward(ui.Button):
    def __init__(self, lang: str):
        super().__init__(style=ButtonStyle.green, label=text_map.get(603, lang))
        self.view: View

    async def callback(self, i: Inter):
        await i.response.defer()

        client = await self.view.user.client
        reward = await client.claim_daily_reward(game=convert_game_type(self.view.game))
        reward_str = f"{reward.amount}x {reward.name}"
        embed = DefaultEmbed(
            description=text_map.get(41, self.view.lang).format(reward=reward_str)
        )
        embed.set_author(
            name=text_map.get(42, self.view.lang),
            icon_url=i.user.display_avatar.url,
        )
        embed.set_thumbnail(url=reward.icon)

        self.view.disable_items()
        await i.edit_original_response(embed=embed, view=self.view)
        self.view.enable_items()
        await asyncio.sleep(1.5)
        await self.view.update(i)


class ClaimToggle(ui.Button):
    def __init__(self, toggle: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view: View
        self.toggle = toggle

    async def callback(self, i: Inter):
        self.view.daily_checkin = self.toggle
        kwargs = self.view.create_kwargs(self.toggle)
        await i.client.db.users.update(i.user.id, **kwargs)
        self.view.add_components()

        await i.response.edit_message(view=self.view)


class ClaimRewardOn(ClaimToggle):
    def __init__(self, lang: str, current: bool):
        super().__init__(
            True,
            style=ButtonStyle.blurple if current else ButtonStyle.gray,
            label=text_map.get(99, lang),
            emoji=asset.gift_outline,
        )


class ClaimRewardOff(ClaimToggle):
    def __init__(self, lang: str, current: bool):
        super().__init__(
            False,
            style=ButtonStyle.blurple if not current else ButtonStyle.gray,
            label=text_map.get(100, lang),
            emoji=asset.gift_off_outline,
        )