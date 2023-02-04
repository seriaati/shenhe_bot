from discord import Interaction, Locale, ui, ButtonStyle
import asset
import config
from apps.genshin.custom_model import OriginalInfo
from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView, GoBackButton
from utility.utils import DefaultEmbed, get_user_notification


class View(BaseView):
    def __init__(self, locale: Locale | str, current: int, original_info: OriginalInfo):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(NotificationButton(locale, 1, current))
        self.add_item(NotificationButton(locale, 0, current))

        self.original_info = original_info


class NotificationButton(ui.Button):
    def __init__(self, locale: Locale | str, toggle: int, current: int):
        super().__init__(
            emoji=asset.bell_outline if toggle == 1 else asset.bell_off_outline,
            label=text_map.get(99 if toggle == 1 else 100, locale),
            style=ButtonStyle.primary if current == toggle else ButtonStyle.secondary,
        )
        self.toggle = toggle
        self.locale = locale

    async def callback(self, i: Interaction):
        self.view: View
        await button_callback(i, self.toggle, self.locale, self.view.original_info)


async def button_callback(
    i: Interaction, toggle: int, locale: Locale | str, original_info: OriginalInfo
):
    async with i.client.pool.acquire() as db:
        await db.execute(
            f"UPDATE user_settings SET notification = {toggle} WHERE user_id = ?",
            (i.user.id,),
        )
        await db.commit()
    await return_view(i, locale, original_info)


async def return_view(
    i: Interaction, locale: Locale | str, original_info: OriginalInfo
):
    notif = await get_user_notification(i.user.id, i.client.pool)  # type: ignore
    view = View(locale, 1 if notif else 0, original_info)
    view.add_item(GoBackButton(original_info))
    embed = DefaultEmbed(description=text_map.get(138, locale))
    embed.set_author(name=text_map.get(137, locale), icon_url=i.user.display_avatar.url)
    await i.response.edit_message(embed=embed, view=view)
    view.author = i.user
    view.message = await i.original_response()
