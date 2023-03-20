import typing

import discord
from discord import ui

import config
from apps.db.utility import get_profile_ver
from apps.genshin.custom_model import CustomInteraction, EnkaView
from apps.genshin.enka import edit_enka_cache
from apps.genshin.utils import get_uid
from apps.text_map.text_map_app import text_map
from base_ui import BaseView
from exceptions import UIDNotFound
from ui.genshin.EnkaDamageCalc import GoBack
from utility.utils import DefaultEmbed, ErrorEmbed


class View(BaseView):
    def __init__(self, locale: typing.Union[str, discord.Locale], enka_view: EnkaView):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        self.enka_view = enka_view

        self.add_item(VersionButton(locale))
        self.add_item(CacheButton(locale))
        self.add_item(GoBack())

    def gen_settings_embed(self) -> discord.Embed:
        embed = DefaultEmbed(text_map.get(755, self.locale))
        embed.set_image(url="https://i.imgur.com/fdACb83.png")
        return embed

    def gen_version_embed(self, version: int) -> discord.Embed:
        embed = DefaultEmbed(
            text_map.get(749, self.locale),
            f"{text_map.get(751, self.locale)}: {version}",
        )
        image_url = (
            "https://i.imgur.com/SU4uvYV.png"
            if version == 2
            else "https://i.imgur.com/mkzvnVJ.png"
        )
        embed.set_image(url=image_url)
        return embed

    def gen_cache_embed(self) -> discord.Embed:
        embed = DefaultEmbed(
            text_map.get(753, self.locale),
            text_map.get(754, self.locale),
        )
        return embed


class VersionButton(ui.Button):
    def __init__(self, locale: typing.Union[str, discord.Locale]):
        super().__init__(
            row=0,
            label=text_map.get(752, locale),
            style=discord.ButtonStyle.blurple,
            custom_id="card_version",
        )
        self.locale = locale
        self.view: View

    async def callback(self, i: CustomInteraction):
        ver = await get_profile_ver(i.user.id, i.client.pool)
        embed = self.view.gen_version_embed(ver)
        self.view.clear_items()
        self.view.add_item(VersionSelect(self.locale, ver))
        self.view.add_item(GoBack())
        await i.response.edit_message(embed=embed, view=self.view)


class VersionSelect(ui.Select):
    def __init__(self, locale: typing.Union[str, discord.Locale], ver: int):
        super().__init__(
            placeholder=text_map.get(749, locale),
            options=[
                discord.SelectOption(
                    label=text_map.get(750, locale).format(version=1),
                    value="1",
                    default=ver == 1,
                ),
                discord.SelectOption(
                    label=text_map.get(750, locale).format(version=2),
                    value="2",
                    default=ver == 2,
                ),
            ],
            row=0,
        )
        self.locale = locale
        self.view: View

    async def callback(self, i: CustomInteraction):
        await i.client.pool.execute(
            "UPDATE user_settings SET profile_ver = $1 WHERE user_id = $2",
            int(self.values[0]),
            i.user.id,
        )
        for option in self.options:
            option.default = option.value == self.values[0]
        embed = self.view.gen_version_embed(int(self.values[0]))
        await i.response.edit_message(embed=embed, view=self.view)


class CacheButton(ui.Button):
    def __init__(self, locale: typing.Union[str, discord.Locale]):
        super().__init__(
            row=0,
            label=text_map.get(753, locale),
            style=discord.ButtonStyle.blurple,
            custom_id="manage_cache",
        )
        self.locale = locale
        self.view: View

    async def callback(self, i: CustomInteraction):
        embed = self.view.gen_cache_embed()
        self.view.clear_items()

        non_cache_ids: typing.List[int] = []
        card_data = self.view.enka_view.card_data
        if card_data and card_data.characters:
            non_cache_ids = [c.id for c in card_data.characters]
        options = [
            o
            for o in self.view.enka_view.character_options
            if int(o.value) not in non_cache_ids
        ]
        if not options:
            return await i.response.send_message(
                embed=ErrorEmbed().set_author(
                    name=text_map.get(757, self.locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        self.view.add_item(CacheSelect(self.locale, options))
        self.view.add_item(GoBack())
        await i.response.edit_message(embed=embed, view=self.view)


class CacheSelect(ui.Select):
    def __init__(
        self,
        locale: typing.Union[str, discord.Locale],
        options: typing.List[discord.SelectOption],
    ):
        super().__init__(
            placeholder=text_map.get(714, locale),
            options=options,
            max_values=len(options),
            row=0,
        )
        self.locale = locale

    async def callback(self, i: CustomInteraction):
        uid = await get_uid(i.user.id, i.client.pool)
        if uid is None:
            raise UIDNotFound
        await edit_enka_cache(
            uid, [int(v) for v in self.values], i.client.pool, en=True
        )
        await i.response.edit_message(
            embed=DefaultEmbed().set_author(
                name=text_map.get(756, self.locale), icon_url=i.user.display_avatar.url
            ),
            view=None,
        )
