from base_ui import BaseView
from apps.genshin.checks import check_cookie_predicate
from apps.text_map.text_map_app import text_map
import config
from discord import Locale, ui
from discord import ButtonStyle, Interaction


class View(BaseView):
    def __init__(self, code: str, genshin_app, locale: Locale | str):
        self.code = code
        self.genshin_app = genshin_app

        super().__init__(timeout=config.mid_timeout)

        self.add_item(MeToo(text_map.get(132, locale)))


class MeToo(ui.Button):
    def __init__(self, label: str):
        super().__init__(style=ButtonStyle.green, label=label)

    async def callback(self, i: Interaction):
        self.view: View

        await i.response.defer()
        await check_cookie_predicate(i)

        result = await self.view.genshin_app.redeem_code(
            i.user.id, i.user.id, self.view.code, i.locale
        )
        await i.followup.send(embed=result.result, view=self.view)
