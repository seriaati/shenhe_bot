from discord import ButtonStyle, Interaction, Locale, ui

import asset
import config
from apps.genshin.custom_model import OriginalInfo
from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView, GoBackButton
from utility.utils import DefaultEmbed, get_user_notification


class View(BaseView):
    def __init__(self, locale: Locale | str, current: bool, original_info: OriginalInfo):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(NotificationButton(locale, True, current))
        self.add_item(NotificationButton(locale, False, current))

        self.original_info = original_info


class NotificationButton(ui.Button):
    def __init__(self, locale: Locale | str, toggle: bool, current: bool):
        super().__init__(
            emoji=asset.bell_outline if toggle else asset.bell_off_outline,
            label=text_map.get(99 if toggle else 100, locale),
            style=ButtonStyle.primary if current == toggle else ButtonStyle.secondary,
        )
        self.toggle = toggle
        self.locale = locale

    async def callback(self, i: Interaction):
        self.view: View
        await i.client.pool.execute(
            "UPDATE user_settings SET notification = $1 WHERE user_id = $2",
            self.toggle,
            i.user.id,
        )
        await return_view(i, self.locale, self.view.original_info)


async def return_view(
    i: Interaction, locale: Locale | str, original_info: OriginalInfo
):
    notif = await get_user_notification(i.user.id, i.client.pool)  # type: ignore
    view = View(locale, notif, original_info)
    view.add_item(GoBackButton(original_info))
    embed = DefaultEmbed(description=text_map.get(138, locale))
    embed.set_author(name=text_map.get(137, locale), icon_url=i.user.display_avatar.url)
    await i.response.edit_message(embed=embed, view=view)
    view.author = i.user
    view.message = await i.original_response()
