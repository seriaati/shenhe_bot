from typing import List

import discord
from discord import ui

import dev.config as config
from apps.db import get_user_lang
from apps.text_map import text_map
from dev.base_ui import BaseView
from dev.models import CustomInteraction, DefaultEmbed
from ui.wish import SetAuthKey

import_options = {
    "PC - #1": {
        "hash": 358,
        "link": "https://www.youtube.com/watch?v=FCwZkHeIezw",
        "code": "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex \"&{$((New-Object System.Net.WebClient).DownloadString('https://gist.githubusercontent.com/MadeBaruna/1d75c1d37d19eca71591ec8a31178235/raw/702e34117b07294e6959928963b76cfdafdd94f3/getlink.ps1'))} global\"",
    },
    "PC - #2": {
        "hash": 394,
        "link": "https://www.youtube.com/watch?v=ojZzl3dmppI",
        "code": 'iex(\'Write-Host "Copy the wish history table!";while(1) { $c = Get-Clipboard -TextFormatType Html; if ($c -match "^SourceURL:https:/.+log") { break; }; for($i=5; $i -gt 0; $i--) { Write-Host "`rChecking in $i" -NoNewline; Sleep 1; }; }; Write-Host " OK"; $m=(((Get-Clipboard -TextFormatType Html) | ui.Select-String "(https:/.+log)").Matches[0].Value);$m; Set-Clipboard -Value $m;\')',
    },
    "PC - #3": {"hash": 403, "link": "", "code": ""},
    "ANDROID - Wifi": {
        "hash": 426,
        "link": "https://www.youtube.com/watch?v=6C5Zqhcm3NI",
        "code": "",
    },
    "ANDROID - Data": {
        "hash": 426,
        "link": "https://www.youtube.com/watch?v=rHN1iRjmKmc",
        "code": "",
    },
    "ANDROID - Alt": {
        "hash": 426,
        "link": "https://www.youtube.com/watch?v=jAKq94KpGHA",
        "code": "",
    },
    "IOS - #1": {
        "hash": 362,
        "link": "https://www.youtube.com/watch?v=WfBpraUq41c",
        "code": "",
    },
}


class View(BaseView):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(timeout=config.short_timeout)
        self.locale = locale

    @ui.button(emoji="<:windows_logo:1024250977731223552>")
    async def pc(self, i: discord.Interaction, button: ui.Button):
        self.clear_items()
        options = []
        for option in list(import_options.keys()):
            if "PC" in option:
                options.append(
                    discord.SelectOption(label=option, value=option, emoji=button.emoji)
                )
        embed = DefaultEmbed().set_author(
            name=text_map.get(3, self.locale), icon_url=i.user.display_avatar.url
        )
        self.add_item(ChooseMethod(options, self.locale))
        self.add_item(GOBack())
        self.add_item(SubmitLink(self.locale))
        await i.response.edit_message(embed=embed, view=self)

    @ui.button(emoji="<:apple_logo:1024250975390814269>")
    async def ios(self, i: discord.Interaction, button: ui.Button):
        self.clear_items()
        options = []
        for option in list(import_options.keys()):
            if "IOS" in option:
                options.append(
                    discord.SelectOption(label=option, value=option, emoji=button.emoji)
                )
        embed = DefaultEmbed().set_author(
            name=text_map.get(3, self.locale), icon_url=i.user.display_avatar.url
        )
        self.add_item(ChooseMethod(options, self.locale))
        self.add_item(GOBack())
        self.add_item(SubmitLink(self.locale))
        await i.response.edit_message(view=self, embed=embed)


class ChooseMethod(ui.Select):
    def __init__(
        self, options: List[discord.SelectOption], locale: discord.Locale | str
    ):
        super().__init__(placeholder=text_map.get(3, locale), options=options)
        self.locale = locale

    async def callback(self, i: CustomInteraction):
        self.view: View
        embeds = []
        option = import_options.get(self.values[0], {})
        embed = DefaultEmbed()
        embed.set_author(name=self.values[0], icon_url=i.user.display_avatar.url)
        embed.description = text_map.get(option["hash"], self.locale)
        embeds.append(embed)
        if option["link"] != "":
            video_embed = DefaultEmbed(description=option["link"])
            video_embed.set_author(
                name=text_map.get(364, self.locale),
                icon_url="https://i.pinimg.com/originals/7d/c9/93/7dc993c70d4adba215b87cafdc59d82d.png",
            )
            embeds.append(video_embed)
        await i.response.edit_message(embeds=embeds, view=self.view)
        if option["code"] != "":
            await i.followup.send(content=f"```{option['code']}```", ephemeral=True)


class SubmitLink(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            emoji="<:submit_cookie:1019068169882718258>",
            label=text_map.get(477, locale),
            style=discord.ButtonStyle.primary,
        )
        self.locale = locale

    async def callback(self, i: CustomInteraction):
        await i.response.send_modal(SetAuthKey.Modal(self.locale))


class GOBack(ui.Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>")
        self.view: View

    async def callback(self, i: CustomInteraction):
        await i.response.defer(ephemeral=True)
        user_locale = await get_user_lang(i.user.id, i.client.pool)
        view = View(self.view.locale)
        embed = DefaultEmbed()
        embed.set_author(
            name=text_map.get(365, i.locale, user_locale),
            icon_url=i.user.display_avatar.url,
        )
        view.message = await i.edit_original_response(embed=embed, view=view)
