import aiosqlite
import config
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from debug import DefaultView
from discord import ButtonStyle, Interaction, Locale, Member
from discord.ui import Button
from utility.utils import default_embed, error_embed


class View(DefaultView):
    def __init__(self, db: aiosqlite.Connection, author: Member, locale: Locale, user_locale: str | None):
        super().__init__(timeout=config.short_timeout)
        self.db = db
        self.up = None
        self.want = None
        self.author = author
        self.locale = locale
        self.user_locale = user_locale

        self.add_item(IsUP())
        self.add_item(IsStandard(locale, user_locale))

    async def interaction_check(self, i: Interaction) -> bool:
        user_locale = await get_user_locale(i.user.id, self.db)
        if i.user.id != self.author.id:
            await i.response.send_message(embed=error_embed().set_author(name=text_map.get(143, i.locale, user_locale), icon_url=i.user.display_avatar.url), ephemeral=True)
        return i.user.id == self.author.id


class IsUP(Button):
    def __init__(self):
        super().__init__(label='UP', style=ButtonStyle.blurple)

    async def callback(self, i: Interaction):
        self.view: View
        self.view.up = True
        self.view.clear_items()
        self.view.add_item(Want(self.view.locale, self.view.user_locale))
        self.view.add_item(NotWant(self.view.locale, self.view.user_locale))
        await i.response.edit_message(embed=default_embed().set_author(name=text_map.get(390, self.view.locale, self.view.user_locale), icon_url=i.user.display_avatar.url), view=self.view)


class IsStandard(Button):
    def __init__(self, locale: Locale, user_locale: str | None):
        super().__init__(label=text_map.get(387, locale, user_locale))

    async def callback(self, i: Interaction):
        self.view: View
        self.view.up = False
        self.view.clear_items()
        self.view.add_item(Want(self.view.locale, self.view.user_locale))
        self.view.add_item(NotWant(self.view.locale, self.view.user_locale))
        await i.response.edit_message(embed=default_embed().set_author(name=text_map.get(390, self.view.locale, self.view.user_locale), icon_url=i.user.display_avatar.url), view=self.view)


class Want(Button):
    def __init__(self, locale: Locale, user_locale: str | None):
        super().__init__(label=text_map.get(388, locale, user_locale), style=ButtonStyle.green)

    async def callback(self, i: Interaction):
        self.view: View
        await i.response.defer()
        self.view.want = True
        self.view.stop()


class NotWant(Button):
    def __init__(self, locale: Locale, user_locale: str | None):
        super().__init__(label=text_map.get(389, locale, user_locale), style=ButtonStyle.red)

    async def callback(self, i: Interaction):
        self.view: View
        await i.response.defer()
        self.view.want = False
        self.view.stop()
