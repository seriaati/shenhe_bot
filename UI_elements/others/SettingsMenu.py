from typing import Any

from discord import ButtonStyle, Interaction, Locale, SelectOption
from discord.ui import Button, Select

import asset
import config
from apps.genshin.custom_model import OriginalInfo
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.others.language_options import lang_options
from UI_base_models import BaseView, GoBackButton
from UI_elements.others.settings import CustomImage, Notif
from utility.utils import (DefaultEmbed, get_user_appearance_mode,
                           get_user_auto_redeem)


class View(BaseView):
    def __init__(self, locale: Locale | str):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(Appearance(text_map.get(535, locale)))
        self.add_item(Langauge(text_map.get(128, locale)))
        self.add_item(CustomProfileImage(locale))
        self.add_item(Notification(locale))
        self.add_item(AutoRedeem(locale))

        self.original_info: OriginalInfo
        self.locale = locale


class Appearance(Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.monitor_emoji, label=label)

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        locale = self.view.locale

        dark_mode = await get_user_appearance_mode(i.user.id, i.client.pool)  # type: ignore

        embed = DefaultEmbed(
            description=text_map.get(538, locale),
        )
        embed.set_author(
            name=text_map.get(535, locale),
            icon_url=i.user.display_avatar.url,
        )
        if not dark_mode:
            embed.set_image(url="https://i.imgur.com/WQmUHgV.png")
        else:
            embed.set_image(url="https://i.imgur.com/QSkNr1l.png")

        self.view.clear_items()
        self.view.add_item(GoBackButton(self.view.original_info))
        self.view.add_item(ModeButton(False, dark_mode, locale))
        self.view.add_item(ModeButton(True, dark_mode, locale))
        await i.response.edit_message(embed=embed, view=self.view)


class ModeButton(Button):
    def __init__(self, toggle: bool, current: bool, locale: Locale | str):
        super().__init__(
            emoji=asset.moon_emoji if toggle else asset.sun_emoji,
            style=ButtonStyle.blurple if toggle == current else ButtonStyle.grey,
            label=text_map.get(537 if not toggle else 536, locale),
        )
        self.toggle = toggle

    async def callback(self, i: Interaction) -> Any:
        self.view: View

        async with i.client.pool.acquire() as db:  # type: ignore
            await db.execute(
                "UPDATE user_settings SET dark_mode = ? WHERE user_id = ?",
                (1 if self.toggle else 0, i.user.id),
            )
            await db.commit()
        await Appearance.callback(self, i)  # type: ignore


class Langauge(Button):
    def __init__(self, label: str):
        super().__init__(emoji=asset.earth_emoji, label=label)

    async def callback(self, i: Interaction):
        self.view: View
        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale  # type: ignore

        embed = DefaultEmbed(description=text_map.get(125, locale))
        lang_name = lang_options.get(str(locale), {"name": "Unknown"})["name"]
        lang_name = lang_name.split("|")[0]
        embed.set_author(
            name=f"{text_map.get(34, locale)}: {lang_name}",
            icon_url=i.user.display_avatar.url,
        )
        self.view.clear_items()
        self.view.add_item(LanguageGoBack())
        self.view.add_item(LangSelect(locale))
        await i.response.edit_message(embed=embed, view=self.view)

class LanguageGoBack(Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, row=2)
        
    async def callback(self, i: Interaction):
        await return_settings(i)

class LangSelect(Select):
    def __init__(self, locale: Locale | str):
        options = [
            SelectOption(label=text_map.get(124, locale), emoji="🏳️", value="none")
        ]
        for lang, lang_info in lang_options.items():
            options.append(
                SelectOption(
                    label=lang_info["name"], value=lang, emoji=lang_info["emoji"]
                )
            )
        super().__init__(options=options, placeholder=text_map.get(32, locale), row=1)
        self.locale = locale

    async def callback(self, i: Interaction) -> Any:
        async with i.client.pool.acquire() as db:  # type: ignore
            await db.execute(
                "INSERT INTO user_settings (user_id, lang) VALUES (?, ?) ON CONFLICT (user_id) DO UPDATE SET lang = ? WHERE user_id = ?",
                (
                    i.user.id,
                    None if self.values[0] == "none" else self.values[0],
                    self.values[0],
                    i.user.id,
                ),
            )
            await db.commit()
        await Langauge.callback(self, i)  # type: ignore


class CustomProfileImage(Button):
    def __init__(self, locale: str | Locale):
        super().__init__(
            emoji=asset.image_emoji, label=text_map.get(275, locale), row=2
        )
        self.locale = locale

    async def callback(self, i: Interaction):
        self.view: View

        embed = DefaultEmbed(description=text_map.get(276, self.locale))
        embed.set_author(
            name=text_map.get(62, self.locale), icon_url=i.user.display_avatar.url
        )

        view = CustomImage.View(self.locale)
        view.add_item(GoBackButton(self.view.original_info))

        await i.response.edit_message(embed=embed, view=view)
        view.message = await i.original_response()
        view.author = i.user


class Notification(Button):
    def __init__(self, locale: str | Locale):
        super().__init__(
            emoji=asset.bell_badge_outline, label=text_map.get(137, locale), row=2
        )
        self.locale = locale

    async def callback(self, i: Interaction):
        self.view: View
        await Notif.return_view(i, self.locale, OriginalInfo(view=self.view, embed=i.message.embeds[0], children=self.view.children.copy()))  # type: ignore


class AutoRedeem(Button):
    def __init__(self, locale: str | Locale):
        super().__init__(
            emoji=asset.gift_outline, label=text_map.get(126, locale), row=3
        )
        self.locale = locale

    async def callback(self, i: Interaction):
        self.view: View

        auto_redeem = await get_user_auto_redeem(i.user.id, i.client.pool)  # type: ignore

        embed = DefaultEmbed(description=text_map.get(285, self.locale))
        embed.set_author(
            name=text_map.get(126, self.locale), icon_url=i.user.display_avatar.url
        )

        self.view.clear_items()
        self.view.add_item(GoBackButton(self.view.original_info))
        self.view.add_item(RedeemButton(True, auto_redeem, self.locale))
        self.view.add_item(RedeemButton(False, auto_redeem, self.locale))
        await i.response.edit_message(embed=embed, view=self.view)


class RedeemButton(Button):
    def __init__(self, toggle: bool, current: bool, locale: Locale | str):
        super().__init__(
            emoji=asset.gift_open_outline if toggle else asset.gift_off_outline,
            style=ButtonStyle.blurple if toggle == current else ButtonStyle.grey,
            label=text_map.get(99 if toggle else 100, locale),
        )
        self.toggle = toggle
        self.locale = locale

    async def callback(self, i: Interaction) -> Any:
        self.view: View

        async with i.client.pool.acquire() as db:  # type: ignore
            await db.execute(
                "UPDATE user_settings SET auto_redeem = ? WHERE user_id = ?",
                (1 if self.toggle else 0, i.user.id),
            )
            await db.commit()
        await AutoRedeem.callback(self, i)  # type: ignore

async def return_settings(i: Interaction):
    locale = await get_user_locale(i.user.id, i.client.pool) or i.locale

    embed = DefaultEmbed(
        description=f"**{asset.settings_emoji} {text_map.get(539, locale)}**\n\n{text_map.get(534, locale)}"
    )
    view = View(locale)

    await i.response.send_message(embed=embed, view=view)
    view.message = await i.original_response()
    view.author = i.user
    view.original_info = OriginalInfo(
        view=view, embed=embed, children=view.children.copy()
    )