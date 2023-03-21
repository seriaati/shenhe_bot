from discord import ButtonStyle, Interaction, Locale, ui

import config
from apps.genshin import check_cookie_predicate
from apps.text_map import text_map
from base_ui import BaseView


class View(BaseView):
    def __init__(self, code: str, genshin_app, locale: Locale | str):
        self.code = code
        self.genshin_app = genshin_app

        super().__init__(timeout=config.mid_timeout)

        self.add_item(MeTooButton(text_map.get(132, locale)))


class MeTooButton(ui.Button):
    def __init__(self, label: str):
        super().__init__(style=ButtonStyle.green, label=label)
        self.view: View

    async def callback(self, i: Interaction):
        await i.response.defer()
        await check_cookie_predicate(i)

        result = await self.view.genshin_app.redeem_code(
            i.user.id, i.user.id, self.view.code, i.locale
        )
        await i.followup.send(embed=result.result, view=self.view)
