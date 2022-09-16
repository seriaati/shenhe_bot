from typing import Any

import aiosqlite
import config
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from debug import DefaultView
from discord import Interaction, Locale, SelectOption
from discord.ui import Button, Select
from utility.utils import default_embed
from data.others.language_options import lang_options


class View(DefaultView):
    def __init__(self, locale: Locale | str):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(Appearance(text_map.get(535, locale)))
        self.add_item(Langauge(text_map.get(128, locale)))
        self.add_item(DeveloperMessage(text_map.get(541, locale)))


class Appearance(Button):
    def __init__(self, label: str):
        super().__init__(emoji="🖥️", label=label)

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        user_locale = await get_user_locale(i.user.id, i.client.db)
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute(
            "INSERT INTO user_settings (user_id) VALUES (?) ON CONFLICT (user_id) DO NOTHING",
            (i.user.id,),
        )
        await c.execute(
            "SELECT dark_mode FROM user_settings WHERE user_id = ?", (i.user.id,)
        )
        (toggle,) = await c.fetchone()
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
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute(
            "UPDATE user_settings SET dark_mode = 0 WHERE user_id = ?",
            (i.user.id,),
        )
        await i.client.db.commit()
        await Appearance.callback(self, i)


class DarkModeButton(Button):
    def __init__(self, label: str):
        super().__init__(emoji="🌙", label=label)

    async def callback(self, i: Interaction) -> Any:
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute(
            "UPDATE user_settings SET dark_mode = 1 WHERE user_id = ?",
            (i.user.id,),
        )
        await i.client.db.commit()
        await Appearance.callback(self, i)


class Langauge(Button):
    def __init__(self, label: str):
        super().__init__(emoji="🌍", label=label)

    async def callback(self, i: Interaction):
        self.view: View
        user_locale = await get_user_locale(i.user.id, i.client.db)
        embed = default_embed(
            message=f"• {text_map.get(125, i.locale, user_locale)}\n"
            f"• {text_map.get(126, i.locale, user_locale)}\n"
            f"• {text_map.get(127, i.locale, user_locale)}\n"
            f"• {text_map.get(511, i.locale, user_locale)}\n"
            "• [crowdin](https://crowdin.com/project/shenhe-bot)"
        )
        lang_name = lang_options.get(user_locale or str(i.locale))['name']
        lang_name = lang_name.split('|')[0]
        embed.set_author(
            name=f"{text_map.get(34, i.locale, user_locale)}: {lang_name}",
            icon_url=i.user.display_avatar.url,
        )
        embed.set_image(url='https://i.imgur.com/KWWkeyz.png')
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(LangSelect(i.locale, user_locale))
        await i.response.edit_message(embed=embed, view=self.view)


class LangSelect(Select):
    def __init__(self, locale: Locale, user_locale: str):
        options = [
            SelectOption(
                label=text_map.get(124, locale, user_locale), emoji="🏳️", value="none"
            )
        ]
        for lang, lang_info in lang_options.items():
            options.append(
                SelectOption(
                    label=lang_info["name"], value=lang, emoji=lang_info["emoji"]
                )
            )
        super().__init__(
            options=options, placeholder=text_map.get(32, locale, user_locale), row=1
        )
        self.locale = locale

    async def callback(self, i: Interaction) -> Any:
        c: aiosqlite.Cursor = await i.client.db.cursor()
        if self.values[0] == "none":
            await c.execute("DELETE FROM user_settings WHERE user_id = ?", (i.user.id,))
        else:
            await c.execute(
                "INSERT INTO user_settings (user_id, lang) VALUES (?, ?) ON CONFLICT (user_id) DO UPDATE SET lang = ? WHERE user_id = ?",
                (i.user.id, self.values[0], self.values[0], i.user.id),
            )
        await i.client.db.commit()
        await Langauge.callback(self, i)
        
class DeveloperMessage(Button):
    def __init__(self, label: str):
        super().__init__(emoji="✉️", label=label)

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        user_locale = await get_user_locale(i.user.id, i.client.db)
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute(
            "INSERT INTO user_settings (user_id) VALUES (?) ON CONFLICT (user_id) DO NOTHING",
            (i.user.id,),
        )
        await c.execute(
            "SELECT dev_msg FROM user_settings WHERE user_id = ?", (i.user.id,)
        )
        (toggle,) = await c.fetchone()
        emoji = "🔔" if toggle == 1 else "🔕"
        toggle_text = 99 if toggle == 1 else 100
        embed = default_embed(
            message=text_map.get(540, i.locale, user_locale),
        )
        embed.set_author(
            name=f"{text_map.get(101, i.locale, user_locale)}: {emoji} {text_map.get(toggle_text, i.locale, user_locale)}",
            icon_url=i.user.display_avatar.url,
        )
        embed.set_image(url='https://i.imgur.com/vXEcZnW.png')
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(NotifiactionONButton(text_map.get(99, i.locale, user_locale)))
        self.view.add_item(NotificationOFFButton(text_map.get(100, i.locale, user_locale)))
        await i.response.edit_message(embed=embed, view=self.view)


class NotifiactionONButton(Button):
    def __init__(self, label: str):
        super().__init__(emoji="🔔", label=label)

    async def callback(self, i: Interaction) -> Any:
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute(
            "UPDATE user_settings SET dev_msg = 1 WHERE user_id = ?",
            (i.user.id,),
        )
        await i.client.db.commit()
        await DeveloperMessage.callback(self, i)


class NotificationOFFButton(Button):
    def __init__(self, label: str):
        super().__init__(emoji="🔕", label=label)

    async def callback(self, i: Interaction) -> Any:
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute(
            "UPDATE user_settings SET dev_msg = 0 WHERE user_id = ?",
            (i.user.id,),
        )
        await i.client.db.commit()
        await DeveloperMessage.callback(self, i)


class GOBack(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>", row=2)

    async def callback(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, i.client.db)
        view = View(user_locale or i.locale)
        embed = default_embed(message=text_map.get(534, i.locale, user_locale))
        embed.set_author(
            name=f"⚙️ {text_map.get(539, i.locale, user_locale)}",
            icon_url=i.user.display_avatar.url,
        )
        embed.set_image(url='https://i.imgur.com/WM6C1Tk.png')
        await i.response.edit_message(embed=embed, view=view)
        view.message = await i.original_response()
