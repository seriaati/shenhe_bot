from typing import Any

import discord
from discord import ui

import dev.asset as asset
import config
from apps.db import get_user_auto_redeem, get_user_lang, get_user_theme
from apps.text_map import text_map
from base_ui import BaseView, GoBackButton
from data.others.language_options import lang_options
from dev.models import CustomInteraction, DefaultEmbed, OriginalInfo
from ui.others.settings import CustomImage, Notif


class View(BaseView):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(Appearance(text_map.get(535, locale)))
        self.add_item(Langauge(text_map.get(128, locale)))
        self.add_item(CustomProfileImage(locale))
        self.add_item(Notification(locale))
        self.add_item(AutoRedeem(locale))

        self.original_info: OriginalInfo
        self.locale = locale


class Appearance(ui.Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.monitor_emoji, label=label)
        self.view: View

    async def callback(self, i: CustomInteraction) -> Any:
        locale = self.view.locale

        dark_mode = await get_user_theme(i.user.id, i.client.pool)  # type: ignore
        embed = get_appearance_embed(i.user.display_avatar.url, locale, dark_mode)

        view = get_appearance_view(self.view, dark_mode, locale)
        await i.response.edit_message(embed=embed, view=view)


class ModeButton(ui.Button):
    def __init__(self, toggle: bool, current: bool, locale: discord.Locale | str):
        super().__init__(
            emoji=asset.moon_emoji if toggle else asset.sun_emoji,
            style=discord.ButtonStyle.blurple
            if toggle == current
            else discord.ButtonStyle.grey,
            label=text_map.get(537 if not toggle else 536, locale),
        )
        self.toggle = toggle
        self.view: View

    async def callback(self, i: CustomInteraction) -> Any:
        await i.client.pool.execute(
            "UPDATE user_settings SET dark_mode = $1 WHERE user_id = $2",
            self.toggle,
            i.user.id,
        )
        dark_mode = await get_user_theme(i.user.id, i.client.pool)  # type: ignore
        embed = get_appearance_embed(
            i.user.display_avatar.url, self.view.locale, dark_mode
        )

        view = get_appearance_view(self.view, dark_mode, self.view.locale)
        await i.response.edit_message(embed=embed, view=view)


class Langauge(ui.Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.earth_emoji, label=label)
        self.view: View

    async def callback(self, i: CustomInteraction):
        locale = await get_user_lang(i.user.id, i.client.pool) or i.locale  # type: ignore

        embed = get_language_embed(i.user.display_avatar.url, locale)
        view = get_language_view(self.view, locale)
        await i.response.edit_message(embed=embed, view=view)


class LanguageGoBack(ui.Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, row=2)

    async def callback(self, i: CustomInteraction):
        await return_settings(i, edit=True)


class LangSelect(ui.Select):
    def __init__(self, locale: discord.Locale | str):
        options = [
            discord.SelectOption(
                label=text_map.get(124, locale), emoji="🏳️", value="none"
            )
        ]
        for lang, lang_info in lang_options.items():
            options.append(
                discord.SelectOption(
                    label=lang_info["name"], value=lang, emoji=lang_info["emoji"]
                )
            )
        super().__init__(options=options, placeholder=text_map.get(32, locale), row=1)
        self.locale = locale

    async def callback(self, i: CustomInteraction) -> Any:
        self.view: View

        converted_locale = self.values[0] if self.values[0] != "none" else None
        await i.client.pool.execute(
            "UPDATE user_settings SET lang = $1 WHERE user_id = $2",
            converted_locale,
            i.user.id,
        )
        locale = converted_locale or i.locale

        embed = get_language_embed(i.user.display_avatar.url, locale)
        view = get_language_view(self.view, locale)
        await i.response.edit_message(embed=embed, view=view)


class CustomProfileImage(ui.Button):
    def __init__(self, locale: str | discord.Locale):
        super().__init__(
            emoji=asset.image_emoji, label=text_map.get(275, locale), row=2
        )
        self.locale = locale
        self.view: View

    async def callback(self, i: CustomInteraction):
        view = CustomImage.View(self.locale)
        view.add_item(GoBackButton(self.view.original_info))

        await i.response.edit_message(embed=view.gen_embed(), view=view)
        view.message = await i.original_response()
        view.author = i.user


class Notification(ui.Button):
    def __init__(self, locale: str | discord.Locale):
        super().__init__(
            emoji=asset.bell_badge_outline, label=text_map.get(137, locale), row=2
        )
        self.locale = locale
        self.view: View

    async def callback(self, i: CustomInteraction):
        await Notif.return_view(i, self.locale, OriginalInfo(view=self.view, embed=i.message.embeds[0], children=self.view.children.copy()))  # type: ignore


class AutoRedeem(ui.Button):
    def __init__(self, locale: str | discord.Locale):
        super().__init__(
            emoji=asset.gift_outline, label=text_map.get(126, locale), row=3
        )
        self.locale = locale
        self.view: View

    async def callback(self, i: CustomInteraction):
        auto_redeem = await get_user_auto_redeem(i.user.id, i.client.pool)  # type: ignore

        embed = get_redeem_embed(i.user.display_avatar.url, self.locale)
        view = get_redeem_view(self.view, auto_redeem, self.locale)
        await i.response.edit_message(embed=embed, view=view)


class RedeemButton(ui.Button):
    def __init__(self, toggle: bool, current: bool, locale: discord.Locale | str):
        super().__init__(
            emoji=asset.gift_open_outline if toggle else asset.gift_off_outline,
            style=discord.ButtonStyle.blurple
            if toggle == current
            else discord.ButtonStyle.grey,
            label=text_map.get(99 if toggle else 100, locale),
        )
        self.toggle = toggle
        self.locale = locale
        self.view: View

    async def callback(self, i: CustomInteraction) -> Any:
        await i.client.pool.execute(
            "UPDATE user_settings SET auto_redeem = $1 WHERE user_id = $2",
            self.toggle,
            i.user.id,
        )

        embed = get_redeem_embed(i.user.display_avatar.url, self.locale)
        view = get_redeem_view(self.view, self.toggle, self.locale)
        await i.response.edit_message(embed=embed, view=view)


async def return_settings(i: CustomInteraction, edit: bool = False):
    locale = await get_user_lang(i.user.id, i.client.pool) or i.locale

    embed = DefaultEmbed(
        description=f"**{asset.settings_emoji} {text_map.get(539, locale)}**\n\n{text_map.get(534, locale)}"
    )
    view = View(locale)

    if edit:
        await i.response.edit_message(embed=embed, view=view)
    else:
        await i.response.send_message(embed=embed, view=view)
    view.message = await i.original_response()
    view.author = i.user
    view.original_info = OriginalInfo(
        view=view, embed=embed, children=view.children.copy()
    )


def get_appearance_embed(icon_url: str, locale: discord.Locale | str, dark_mode: bool):
    embed = DefaultEmbed(
        description=text_map.get(538, locale),
    )
    embed.set_author(
        name=text_map.get(535, locale),
        icon_url=icon_url,
    )
    if not dark_mode:
        embed.set_image(url="https://i.imgur.com/WQmUHgV.png")
    else:
        embed.set_image(url="https://i.imgur.com/QSkNr1l.png")

    return embed


def get_appearance_view(view: View, dark_mode: bool, locale: str | discord.Locale):
    view.clear_items()
    view.add_item(GoBackButton(view.original_info))
    view.add_item(ModeButton(False, dark_mode, locale))
    view.add_item(ModeButton(True, dark_mode, locale))

    return view


def get_language_embed(icon_url: str, locale: discord.Locale | str):
    embed = DefaultEmbed(description=text_map.get(125, locale))
    lang_name = lang_options.get(str(locale), {"name": "Unknown"})["name"]
    lang_name = lang_name.split("|")[0]
    embed.set_author(
        name=f"{text_map.get(34, locale)}: {lang_name}",
        icon_url=icon_url,
    )

    return embed


def get_language_view(view: View, locale: str | discord.Locale):
    view.clear_items()
    view.add_item(LanguageGoBack())
    view.add_item(LangSelect(locale))

    return view


def get_redeem_embed(icon_url: str, locale: discord.Locale | str):
    embed = DefaultEmbed(description=text_map.get(285, locale))
    embed.set_author(name=text_map.get(126, locale), icon_url=icon_url)

    return embed


def get_redeem_view(view: View, auto_redeem: bool, locale: str | discord.Locale):
    view.clear_items()
    view.add_item(GoBackButton(view.original_info))
    view.add_item(RedeemButton(True, auto_redeem, locale))
    view.add_item(RedeemButton(False, auto_redeem, locale))

    return view
