from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView
from discord import Interaction, Locale, SelectOption, ButtonStyle
from discord.ui import Button, button, Select
from apps.text_map.utils import get_user_locale
from utility.utils import default_embed
import config
from UI_elements.wish import SetAuthKey
from typing import List

import_options = {
    "PC - #1": {
        "hash": 358,
        "link": "https://www.youtube.com/watch?v=FCwZkHeIezw",
        "code": "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex \"&{$((New-Object System.Net.WebClient).DownloadString('https://gist.githubusercontent.com/MadeBaruna/1d75c1d37d19eca71591ec8a31178235/raw/702e34117b07294e6959928963b76cfdafdd94f3/getlink.ps1'))} global\"",
    },
    "PC - #2": {
        "hash": 394,
        "link": "https://www.youtube.com/watch?v=ojZzl3dmppI",
        "code": 'iex(\'Write-Host "Copy the wish history table!";while(1) { $c = Get-Clipboard -TextFormatType Html; if ($c -match "^SourceURL:https:/.+log") { break; }; for($i=5; $i -gt 0; $i--) { Write-Host "`rChecking in $i" -NoNewline; Sleep 1; }; }; Write-Host " OK"; $m=(((Get-Clipboard -TextFormatType Html) | Select-String "(https:/.+log)").Matches[0].Value);$m; Set-Clipboard -Value $m;\')',
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
    def __init__(self, locale: Locale, user_locale: str | None):
        super().__init__(timeout=config.short_timeout)
        self.locale = locale
        self.user_locale = user_locale

    @button(emoji="<:windows_logo:1024250977731223552>")
    async def pc(self, i: Interaction, button: Button):
        self.clear_items()
        options = []
        for option in list(import_options.keys()):
            if "PC" in option:
                options.append(
                    SelectOption(label=option, value=option, emoji=button.emoji)
                )
        self.add_item(ChooseMethod(options, self.user_locale or self.locale))
        self.add_item(GOBack())
        self.add_item(SubmitLink(self.locale))
        await i.response.edit_message(view=self)

    @button(emoji="<:android_logo:1024250973222350919>")
    async def android(self, i: Interaction, button: Button):
        self.clear_items()
        options = []
        for option in list(import_options.keys()):
            if "ANDROID" in option:
                options.append(
                    SelectOption(label=option, value=option, emoji=button.emoji)
                )
        self.add_item(ChooseMethod(options, self.user_locale or self.locale))
        self.add_item(GOBack())
        self.add_item(SubmitLink(self.locale))
        await i.response.edit_message(view=self)

    @button(emoji="<:apple_logo:1024250975390814269> ")
    async def ios(self, i: Interaction, button: Button):
        self.clear_items()
        options = []
        for option in list(import_options.keys()):
            if "IOS" in option:
                options.append(
                    SelectOption(label=option, value=option, emoji=button.emoji)
                )
        self.add_item(ChooseMethod(options, self.user_locale or self.locale))
        self.add_item(GOBack())
        self.add_item(SubmitLink(self.locale))
        await i.response.edit_message(view=self)


class ChooseMethod(Select):
    def __init__(self, options: List[SelectOption], locale: Locale | str):
        super().__init__(placeholder=text_map.get(3, locale), options=options)
        self.locale = locale

    async def callback(self, i: Interaction):
        self.view: View
        option = import_options.get(self.values[0])
        embed = default_embed()
        embed.set_author(name=self.values[0], icon_url=i.user.display_avatar.url)
        embed.description = text_map.get(option["hash"], self.locale)
        await i.response.edit_message(embed=embed, view=self.view)
        if option["link"] != "":
            await i.followup.send(content=option["link"], ephemeral=True)
        if option["code"] != "":
            await i.followup.send(content=f"```{option['code']}```", ephemeral=True)


class SubmitLink(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            emoji="<:submit_cookie:1019068169882718258>",
            label=text_map.get(477, locale),
            style=ButtonStyle.primary,
        )
        self.locale = locale

    async def callback(self, i: Interaction):
        await i.response.send_modal(SetAuthKey.Modal(self.locale))


class GOBack(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>")

    async def callback(self, i: Interaction):
        await i.response.defer(ephemeral=True)
        user_locale = await get_user_locale(i.user.id, i.client.db)
        view = View(i.locale, user_locale)
        embed = default_embed(message=text_map.get(366, i.locale, user_locale))
        embed.set_author(
            name=text_map.get(365, i.locale, user_locale),
            icon_url=i.user.display_avatar.url,
        )
        await i.edit_original_response(embed=embed, view=view)
        view.message = await i.original_response()
