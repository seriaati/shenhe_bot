from typing import Any

from discord import Interaction, Locale, SelectOption
from discord.ui import Button, Select

import asset
import config
from apps.genshin.custom_model import OriginalInfo
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.others.language_options import lang_options
from UI_base_models import BaseView
from UI_elements.others.settings import CustomImage, Notif
from utility.utils import default_embed


class View(BaseView):
    def __init__(self, locale: Locale | str):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(Appearance(text_map.get(535, locale)))
        self.add_item(Langauge(text_map.get(128, locale)))
        self.add_item(CustomProfileImage(locale))
        self.add_item(Notification(locale))


class Appearance(Button):
    def __init__(self, label: str):
        super().__init__(emoji="🖥️", label=label)

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        user_locale = await get_user_locale(i.user.id, i.client.pool)
        async with i.client.pool.acquire() as db:
            async with db.execute(
                "INSERT INTO user_settings (user_id) VALUES (?) ON CONFLICT (user_id) DO NOTHING",
                (i.user.id,),
            ) as c:
                await c.execute(
                    "SELECT dark_mode FROM user_settings WHERE user_id = ?",
                    (i.user.id,),
                )
                toggle = await c.fetchone()

        emoji = "🌙" if toggle == 1 else "☀️"
        toggle_text = 536 if toggle == 1 else 537
        embed = default_embed(
            message=text_map.get(538, i.locale, user_locale),
        )
        embed.set_author(
            name=f"{text_map.get(101, i.locale, user_locale)}: {emoji} {text_map.get(toggle_text, i.locale, user_locale)}",
            icon_url=i.user.display_avatar.url,
        )
        embed.set_image(url="https://i.imgur.com/rxBXn1l.png")
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(LightModeButton(text_map.get(537, i.locale, user_locale)))
        self.view.add_item(DarkModeButton(text_map.get(536, i.locale, user_locale)))
        await i.response.edit_message(embed=embed, view=self.view)


class LightModeButton(Button):
    def __init__(self, label: str):
        super().__init__(emoji="☀️", label=label)

    async def callback(self, i: Interaction) -> Any:
        async with i.client.pool.acquire() as db:
            await db.execute(
                "UPDATE user_settings SET dark_mode = 0 WHERE user_id = ?",
                (i.user.id,),
            )
            await db.commit()
        await Appearance.callback(self, i)  # type: ignore


class DarkModeButton(Button):
    def __init__(self, label: str):
        super().__init__(emoji="🌙", label=label)

    async def callback(self, i: Interaction) -> Any:
        async with i.client.pool.acquire() as db:
            await db.execute(
                "UPDATE user_settings SET dark_mode = 1 WHERE user_id = ?",
                (i.user.id,),
            )
            await db.commit()
        await Appearance.callback(self, i)  # type: ignore


class Langauge(Button):
    def __init__(self, label: str):
        super().__init__(emoji="🌍", label=label)

    async def callback(self, i: Interaction):
        self.view: View
        locale = await get_user_locale(i.user.id, i.client.pool) or str(i.locale)
        embed = default_embed(message=text_map.get(125, locale))
        lang_name = lang_options.get(locale, {"name": "Unknown"})["name"]
        lang_name = lang_name.split("|")[0]
        embed.set_author(
            name=f"{text_map.get(34, locale)}: {lang_name}",
            icon_url=i.user.display_avatar.url,
        )
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(LangSelect(locale))
        await i.response.edit_message(embed=embed, view=self.view)


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
        async with i.client.pool.acquire() as db:
            if self.values[0] == "none":
                await db.execute(
                    "DELETE FROM user_settings WHERE user_id = ?", (i.user.id,)
                )
            else:
                await db.execute(
                    "INSERT INTO user_settings (user_id, lang) VALUES (?, ?) ON CONFLICT (user_id) DO UPDATE SET lang = ? WHERE user_id = ?",
                    (i.user.id, self.values[0], self.values[0], i.user.id),
                )
            await db.commit()
        await Langauge.callback(self, i)  # type: ignore


class GOBack(Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, row=2)

    async def callback(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, i.client.pool)
        view = View(user_locale or i.locale)
        view.author = i.user
        embed = default_embed(message=text_map.get(534, i.locale, user_locale))
        embed.set_author(
            name=f"⚙️ {text_map.get(539, i.locale, user_locale)}",
            icon_url=i.user.display_avatar.url,
        )
        await i.response.edit_message(embed=embed, view=view)
        view.message = await i.original_response()


class CustomProfileImage(Button):
    def __init__(self, locale: str | Locale):
        super().__init__(emoji="🖼️", label=text_map.get(275, locale), row=2)
        self.locale = locale

    async def callback(self, i: Interaction):
        embed = default_embed(message=text_map.get(276, self.locale))
        embed.set_author(
            name=text_map.get(62, self.locale), icon_url=i.user.display_avatar.url
        )
        view = CustomImage.View(self.locale)
        view.author = i.user
        await i.response.edit_message(embed=embed, view=view)
        view.message = await i.original_response()


class Notification(Button):
    def __init__(self, locale: str | Locale):
        super().__init__(emoji="🔔", label=text_map.get(137, locale), row=2)
        self.locale = locale

    async def callback(self, i: Interaction):
        self.view: View
        await Notif.return_view(i, self.locale, OriginalInfo(view=self.view, embed=i.message.embeds[0]))  # type: ignore
