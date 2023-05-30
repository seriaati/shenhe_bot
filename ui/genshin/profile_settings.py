import typing

import discord
from discord import ui

import dev.config as config
from apps.genshin import edit_enka_cache
from apps.text_map import text_map
from dev.base_ui import BaseView, EnkaView
from dev.models import DefaultEmbed, ErrorEmbed, Inter
from ui.genshin.enka_damage_calc import GoBack
from utils import create_user_settings, get_profile_ver


class View(BaseView):
    def __init__(self, lang: typing.Union[str, discord.Locale], enka_view: EnkaView):
        super().__init__(timeout=config.mid_timeout)
        self.lang = lang
        self.enka_view = enka_view

        self.add_item(VersionButton(lang))
        self.add_item(CacheButton(lang))
        self.add_item(GoBack())

    def gen_settings_embed(self) -> discord.Embed:
        embed = DefaultEmbed(text_map.get(755, self.lang))
        embed.set_image(url="https://i.imgur.com/fdACb83.png")
        return embed

    def gen_version_embed(self, version: int) -> discord.Embed:
        embed = DefaultEmbed(
            text_map.get(749, self.lang),
            f"{text_map.get(751, self.lang)}: {version}",
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
            text_map.get(753, self.lang),
            text_map.get(754, self.lang),
        )
        return embed


class VersionButton(ui.Button):
    def __init__(self, lang: typing.Union[str, discord.Locale]):
        super().__init__(
            row=0,
            label=text_map.get(752, lang),
            style=discord.ButtonStyle.blurple,
            custom_id="card_version",
        )
        self.lang = lang
        self.view: View

    async def callback(self, i: Inter):
        ver = await get_profile_ver(i.user.id, i.client.pool)
        embed = self.view.gen_version_embed(ver)
        self.view.clear_items()
        self.view.add_item(VersionSelect(self.lang, ver))
        self.view.add_item(GoBack())
        await i.response.edit_message(embed=embed, view=self.view)


class VersionSelect(ui.Select):
    def __init__(self, lang: typing.Union[str, discord.Locale], ver: int):
        super().__init__(
            placeholder=text_map.get(749, lang),
            options=[
                discord.SelectOption(
                    label=text_map.get(750, lang).format(version=1),
                    value="1",
                    default=ver == 1,
                ),
                discord.SelectOption(
                    label=text_map.get(750, lang).format(version=2),
                    value="2",
                    default=ver == 2,
                ),
            ],
            row=0,
        )
        self.lang = lang
        self.view: View

    async def callback(self, i: Inter):
        await create_user_settings(i.user.id, i.client.pool)
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
    def __init__(self, lang: typing.Union[str, discord.Locale]):
        super().__init__(
            row=0,
            label=text_map.get(753, lang),
            style=discord.ButtonStyle.blurple,
            custom_id="manage_cache",
        )
        self.lang = lang
        self.view: View

    async def callback(self, i: Inter):
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
                    name=text_map.get(757, self.lang),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        self.view.add_item(CacheSelect(self.lang, options))
        self.view.add_item(GoBack())
        await i.response.edit_message(embed=embed, view=self.view)


class CacheSelect(ui.Select):
    def __init__(
        self,
        lang: typing.Union[str, discord.Locale],
        options: typing.List[discord.SelectOption],
    ):
        super().__init__(
            placeholder=text_map.get(714, lang),
            options=options,
            max_values=len(options),
            row=0,
        )
        self.lang = lang

    async def callback(self, i: Inter):
        uid = await i.client.db.users.get_uid(i.user.id)
        await edit_enka_cache(
            uid, [int(v) for v in self.values], i.client.pool, en=True
        )
        await i.response.edit_message(
            embed=DefaultEmbed().set_author(
                name=text_map.get(756, self.lang), icon_url=i.user.display_avatar.url
            ),
            view=None,
        )
