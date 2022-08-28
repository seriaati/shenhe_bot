import sentry_sdk
from apps.text_map.text_map_app import text_map
from discord import Interaction, Locale
from discord.ui import TextInput
from debug import DefaultModal
from utility.utils import error_embed, log


class Modal(DefaultModal):
    resin_threshold = TextInput(label="樹脂閥值", placeholder="例如: 140 (不得大於 160)")
    max_notif = TextInput(label="最大提醒值", placeholder="例如: 5")

    def __init__(self, locale: Locale, user_locale: str):
        super().__init__(title=text_map.get(151, locale, user_locale))
        self.resin_threshold.label = text_map.get(152, locale, user_locale)
        self.resin_threshold.placeholder = text_map.get(153, locale, user_locale)
        self.max_notif.label = text_map.get(154, locale, user_locale)
        self.max_notif.placeholder = text_map.get(155, locale, user_locale)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        self.stop()

    async def on_error(self, i: Interaction, e: Exception) -> None:
        log.warning(
            f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
        )
        sentry_sdk.capture_exception(e)
        await i.response.send_message(
            embed=error_embed().set_author(
                name=text_map.get(135, i.locale), icon_url=i.user.display_avatar.url
            ),
            ephemeral=True,
        )
