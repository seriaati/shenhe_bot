import calendar

from discord import ButtonStyle, Embed, ui
from discord.errors import InteractionResponded
from genshin import GeetestTriggered

import dev.asset as asset
import dev.config as config
from apps.db.tables.hoyo_account import HoyoAccount, convert_game_type
from apps.text_map import text_map
from dev.base_ui import BaseButton, BaseView
from dev.enum import GameType
from dev.models import DefaultEmbed, ErrorEmbed, Inter
from utils import divide_chunks, get_dt_now
from utils.genshin import get_checkin_url
from utils.text_map import get_game_name


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
        self.daily_checkin = self.user.daily_checkin

        lang = (await self.user.settings).lang
        self.lang = lang or str(i.locale)

        self.add_components()
        embed = await self.fetch_embed(i)
        await i.edit_original_response(embed=embed, view=self)

        self.author = i.user
        self.message = await i.original_response()

    def add_components(self) -> None:
        self.clear_items()
        self.add_item(ClaimRewardOn(self.lang, self.daily_checkin))
        self.add_item(ClaimRewardOff(self.lang, self.daily_checkin))
        self.add_item(ClaimReward(self.lang))

    async def fetch_embed(self, i: Inter) -> Embed:
        now = get_dt_now()
        day_in_month = calendar.monthrange(now.year, now.month)[1]

        client = await self.user.client
        _, claimed_rewards = await client.get_reward_info(
            game=convert_game_type(self.game)
        )

        game_name = get_game_name(self.game, self.lang)
        embed = DefaultEmbed(
            description=f"{text_map.get(606, self.lang)}: {claimed_rewards}/{day_in_month}\n"
        )
        embed.set_author(
            name=f"{text_map.get(604, self.lang)} - {game_name}",
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
            embed.add_field(name=f"{text_map.get(605, self.lang)} ({index+1})", value=r)

        return embed


class ClaimReward(BaseButton):
    def __init__(self, lang: str):
        super().__init__(style=ButtonStyle.green, label=text_map.get(603, lang))
        self.view: View

    async def callback(self, i: Inter):
        await self.loading(i)

        client = await self.view.user.client
        try:
            reward = await client.claim_daily_reward(
                game=convert_game_type(self.view.game)
            )
        except GeetestTriggered:
            self.restore_state()
            await i.edit_original_response(view=self.view)

            embed = ErrorEmbed(description=text_map.get(807, self.view.lang))
            embed.set_author(name=text_map.get(806, self.view.lang))
            view = BaseView()
            url = get_checkin_url(self.view.game)
            view.add_item(
                ui.Button(emoji=asset.hoyolab_emoji, url=url, label="HoYoLAB")
            )
            await i.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            self.restore_state()
            r_embed = await self.view.fetch_embed(i)
            await i.edit_original_response(embed=r_embed, view=self.view)

            reward_str = f"{reward.amount}x {reward.name}"
            embed = DefaultEmbed(
                description=text_map.get(41, self.view.lang).format(reward=reward_str)
            )
            embed.set_author(
                name=text_map.get(42, self.view.lang),
                icon_url=i.user.display_avatar.url,
            )
            embed.set_thumbnail(url=reward.icon)
            await i.followup.send(embed=embed)


class ClaimToggle(ui.Button):
    def __init__(self, toggle: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view: View
        self.toggle = toggle

    async def callback(self, i: Inter):
        self.view.daily_checkin = self.toggle
        await i.client.db.users.update(
            i.user.id, self.view.user.uid, daily_checkin=self.toggle
        )
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
