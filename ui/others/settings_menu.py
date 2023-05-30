from typing import Any

import discord
from discord import ui

import dev.asset as asset
import dev.config as config
from apps.db.tables.user_settings import Settings
from apps.text_map import text_map
from data.others.language_options import lang_options
from dev.base_ui import BaseView, GoBackButton
from dev.models import DefaultEmbed, Inter, OriginalInfo
from ui.others.settings import custom_image, notif_menu


class View(BaseView):
    def __init__(self, lang: discord.Locale | str):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(Appearance(text_map.get(535, lang)))
        self.add_item(Langauge(text_map.get(128, lang)))
        self.add_item(CustomProfileImage(lang))
        self.add_item(Notification(lang))
        self.add_item(AutoRedeem(lang))

        self.original_info: OriginalInfo
        self.lang = lang


class Appearance(ui.Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.monitor_emoji, label=label)
        self.view: View

    async def callback(self, i: Inter) -> Any:
        lang = self.view.lang

        dark_mode = await i.client.db.settings.get(i.user.id, Settings.DARK_MODE)
        embed = get_appearance_embed(i.user.display_avatar.url, lang, dark_mode)

        view = get_appearance_view(self.view, dark_mode, lang)
        await i.response.edit_message(embed=embed, view=view)


class ModeButton(ui.Button):
    def __init__(self, toggle: bool, current: bool, lang: discord.Locale | str):
        super().__init__(
            emoji=asset.moon_emoji if toggle else asset.sun_emoji,
            style=discord.ButtonStyle.blurple
            if toggle == current
            else discord.ButtonStyle.grey,
            label=text_map.get(537 if not toggle else 536, lang),
        )
        self.toggle = toggle
        self.view: View

    async def callback(self, i: Inter) -> Any:
        await i.client.db.settings.update(i.user.id, Settings.DARK_MODE, self.toggle)
        dark_mode = await i.client.db.settings.get(i.user.id, Settings.DARK_MODE)
        embed = get_appearance_embed(
            i.user.display_avatar.url, self.view.lang, dark_mode
        )

        view = get_appearance_view(self.view, dark_mode, self.view.lang)
        await i.response.edit_message(embed=embed, view=view)


class Langauge(ui.Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.earth_emoji, label=label)
        self.view: View

    async def callback(self, i: Inter):
        lang = await i.client.db.settings.get(i.user.id, Settings.LANG)

        embed = get_language_embed(i.user.display_avatar.url, lang)
        view = get_language_view(self.view, lang)
        await i.response.edit_message(embed=embed, view=view)


class LanguageGoBack(ui.Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, row=2)

    async def callback(self, i: Inter):
        await return_settings(i, edit=True)


class LangSelect(ui.Select):
    def __init__(self, lang: discord.Locale | str):
        options = [
            discord.SelectOption(
                label=text_map.get(124, lang), emoji="🏳️", value="none"
            )
        ]
        for lang, lang_info in lang_options.items():
            options.append(
                discord.SelectOption(
                    label=lang_info["name"], value=lang, emoji=lang_info["emoji"]
                )
            )
        super().__init__(options=options, placeholder=text_map.get(32, lang), row=1)
        self.lang = lang

    async def callback(self, i: Inter) -> Any:
        self.view: View

        converted_locale = self.values[0] if self.values[0] != "none" else None
        await i.client.db.settings.update(i.user.id, Settings.LANG, converted_locale)
        lang = converted_locale or i.locale

        embed = get_language_embed(i.user.display_avatar.url, lang)
        view = get_language_view(self.view, lang)
        await i.response.edit_message(embed=embed, view=view)


class CustomProfileImage(ui.Button):
    def __init__(self, lang: str | discord.Locale):
        super().__init__(
            emoji=asset.image_emoji, label=text_map.get(275, lang), row=2
        )
        self.lang = lang
        self.view: View

    async def callback(self, i: Inter):
        view = custom_image.View(self.lang)
        view.add_item(GoBackButton(self.view.original_info))

        await i.response.edit_message(embed=view.gen_embed(), view=view)
        view.message = await i.original_response()
        view.author = i.user


class Notification(ui.Button):
    def __init__(self, lang: str | discord.Locale):
        super().__init__(
            emoji=asset.bell_badge_outline, label=text_map.get(137, lang), row=2
        )
        self.lang = lang
        self.view: View

    async def callback(self, i: Inter):
        await notif_menu.return_view(i, self.lang, OriginalInfo(view=self.view, embed=i.message.embeds[0], children=self.view.children.copy()))  # type: ignore


class AutoRedeem(ui.Button):
    def __init__(self, lang: str | discord.Locale):
        super().__init__(
            emoji=asset.gift_outline, label=text_map.get(126, lang), row=3
        )
        self.lang = lang
        self.view: View

    async def callback(self, i: Inter):
        auto_redeem = await i.client.db.settings.get(i.user.id, Settings.AUTO_REDEEM)

        embed = get_redeem_embed(i.user.display_avatar.url, self.lang)
        view = get_redeem_view(self.view, auto_redeem, self.lang)
        await i.response.edit_message(embed=embed, view=view)


class RedeemButton(ui.Button):
    def __init__(self, toggle: bool, current: bool, lang: discord.Locale | str):
        super().__init__(
            emoji=asset.gift_open_outline if toggle else asset.gift_off_outline,
            style=discord.ButtonStyle.blurple
            if toggle == current
            else discord.ButtonStyle.grey,
            label=text_map.get(99 if toggle else 100, lang),
        )
        self.toggle = toggle
        self.lang = lang
        self.view: View

    async def callback(self, i: Inter) -> Any:
        await i.client.db.settings.update(i.user.id, Settings.AUTO_REDEEM, self.toggle)

        embed = get_redeem_embed(i.user.display_avatar.url, self.lang)
        view = get_redeem_view(self.view, self.toggle, self.lang)
        await i.response.edit_message(embed=embed, view=view)


async def return_settings(i: Inter, edit: bool = False):
    lang = await i.client.db.settings.get(i.user.id, Settings.LANG)
    lang = lang or i.locale

    embed = DefaultEmbed(
        description=f"**{asset.settings_emoji} {text_map.get(539, lang)}**\n\n{text_map.get(534, lang)}"
    )
    view = View(lang)

    if edit:
        await i.response.edit_message(embed=embed, view=view)
    else:
        await i.response.send_message(embed=embed, view=view)
    view.message = await i.original_response()
    view.author = i.user
    view.original_info = OriginalInfo(
        view=view, embed=embed, children=view.children.copy()
    )


def get_appearance_embed(icon_url: str, lang: discord.Locale | str, dark_mode: bool):
    embed = DefaultEmbed(
        description=text_map.get(538, lang),
    )
    embed.set_author(
        name=text_map.get(535, lang),
        icon_url=icon_url,
    )
    if not dark_mode:
        embed.set_image(url="https://i.imgur.com/WQmUHgV.png")
    else:
        embed.set_image(url="https://i.imgur.com/QSkNr1l.png")

    return embed


def get_appearance_view(view: View, dark_mode: bool, lang: str | discord.Locale):
    view.clear_items()
    view.add_item(GoBackButton(view.original_info))
    view.add_item(ModeButton(False, dark_mode, lang))
    view.add_item(ModeButton(True, dark_mode, lang))

    return view


def get_language_embed(icon_url: str, lang: discord.Locale | str):
    embed = DefaultEmbed(description=text_map.get(125, lang))
    lang_name = lang_options.get(str(lang), {"name": "Unknown"})["name"]
    lang_name = lang_name.split("|")[0]
    embed.set_author(
        name=f"{text_map.get(34, lang)}: {lang_name}",
        icon_url=icon_url,
    )

    return embed


def get_language_view(view: View, lang: str | discord.Locale):
    view.clear_items()
    view.add_item(LanguageGoBack())
    view.add_item(LangSelect(lang))

    return view


def get_redeem_embed(icon_url: str, lang: discord.Locale | str):
    embed = DefaultEmbed(description=text_map.get(285, lang))
    embed.set_author(name=text_map.get(126, lang), icon_url=icon_url)

    return embed


def get_redeem_view(view: View, auto_redeem: bool, lang: str | discord.Locale):
    view.clear_items()
    view.add_item(GoBackButton(view.original_info))
    view.add_item(RedeemButton(True, auto_redeem, lang))
    view.add_item(RedeemButton(False, auto_redeem, lang))

    return view
