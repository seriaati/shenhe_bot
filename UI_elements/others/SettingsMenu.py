from typing import Any

import aiosqlite
import config
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseModal, BaseView
from discord import Interaction, Locale, SelectOption
from discord.ui import Button, Select, TextInput
from utility.utils import default_embed
from data.others.language_options import lang_options
import pytz


class View(BaseView):
    def __init__(self, locale: Locale | str):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(Appearance(text_map.get(535, locale)))
        self.add_item(Langauge(text_map.get(128, locale)))
        self.add_item(DeveloperMessage(text_map.get(541, locale)))
        self.add_item(Timezone(text_map.get(186, locale)))


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
        lang_name = lang_options.get(user_locale or str(i.locale))["name"]
        lang_name = lang_name.split("|")[0]
        embed.set_author(
            name=f"{text_map.get(34, i.locale, user_locale)}: {lang_name}",
            icon_url=i.user.display_avatar.url,
        )
        embed.set_image(url="https://i.imgur.com/KWWkeyz.png")
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
        embed.set_image(url="https://i.imgur.com/vXEcZnW.png")
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(
            NotifiactionONButton(text_map.get(99, i.locale, user_locale))
        )
        self.view.add_item(
            NotificationOFFButton(text_map.get(100, i.locale, user_locale))
        )
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
        embed.set_image(url="https://i.imgur.com/WM6C1Tk.png")
        await i.response.edit_message(embed=embed, view=view)
        view.message = await i.original_response()


class Timezone(Button):
    def __init__(self, label: str):
        super().__init__(emoji="🕛", label=label)

    async def callback(self, i: Interaction):
        self.view.add_item(CommonTimezoneSelect())
        await i.response.edit_message(view=self.view)
    
class CommonTimezoneSelect(Select):
    def __init__(self):
        options = [
            SelectOption(emoji='🇹🇼', label='UTC+8', value='Asia/Taipei'),
            SelectOption(emoji='🇺🇸', label='UTC-5', value='America/New_York'),
            SelectOption(emoji='🇬🇧', label='UTC+0', value='Europe/London'),
            SelectOption(emoji='🇯🇵', label='UTC+9', value='Asia/Tokyo'),
            SelectOption(emoji='🇦🇺', label='UTC+10', value='Australia/Sydney'),
            SelectOption(emoji='🇨🇳', label='UTC+8', value='Asia/Shanghai'),
            SelectOption(emoji='🇪🇺', label='UTC+2', value='Europe/Brussels'),
            SelectOption(emoji='🇮🇳', label='UTC+5.5', value='Asia/Kolkata'),
            SelectOption(emoji='🇰🇷', label='UTC+9', value='Asia/Seoul'),
            SelectOption(emoji='🇷🇺', label='UTC+3', value='Europe/Moscow'),
            SelectOption(emoji='🇸🇬', label='UTC+8', value='Asia/Singapore'),
            SelectOption(emoji='🇺🇦', label='UTC+2', value='Europe/Kiev'),
        ]
        super().__init__(options=options)


class SubmitTimezone(BaseModal):
    timezone = TextInput(
        label="Timezone", placeholder="Timezone", min_length=1, max_length=100
    )

    def __init__(self, i: Interaction, locale: Locale | str):
        self.timezone.label = text_map.get(144, locale)
        self.timezone.placeholder = text_map.get(145, locale)
        super().__init__(title=text_map.get(154, locale), timeout=config.mid_timeout)
        self.locale = locale

    async def on_submit(self, i: Interaction) -> None:
        if self.timezone.value not in pytz.all_timezones:
            await i.response.send_message(
                text_map.get(160, self.locale), ephemeral=True
            )
        else:
            async with i.client.db.execute(
                "INSERT INTO user_settings (user_id, timezone) VALUES (?, ?) ON CONFLICT (user_id) DO UPDATE SET timezone = ? WHERE user_id = ?",
                (i.user.id, self.timezone.value, self.timezone.value, i.user.id),
            ) as c:
                await i.client.db.commit()
            embed = default_embed(
                message=f"{text_map.get(220, self.locale)}: {self.timezone.value}"
            )
            embed.set_author(
                name=text_map.get(179, self.locale), icon_url=i.user.display_avatar.url
            )
            await i.response.send_message(embed=embed, ephemeral=True)
