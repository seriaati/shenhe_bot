import aiosqlite
import config
import genshin
from apps.text_map.convert_locale import to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from discord import Interaction, Locale, TextStyle
from discord.ui import TextInput
from UI_base_models import BaseModal
from utility.utils import default_embed, error_embed, log


class Modal(BaseModal):
    url = TextInput(
        label="Auth Key URL",
        placeholder="請ctrl+v貼上複製的連結",
        style=TextStyle.long,
        required=True,
    )

    def __init__(self, locale: Locale | str):
        super().__init__(
            title=text_map.get(353, locale),
            timeout=config.mid_timeout,
            custom_id="authkey_modal",
        )
        self.url.label = text_map.get(352, locale)
        self.url.placeholder = text_map.get(354, locale)

    async def on_submit(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, i.client.db)
        client: genshin.Client = i.client.genshin_client
        client.lang = to_genshin_py(user_locale or i.locale) or "en-US"
        authkey = genshin.utility.extract_authkey(self.url.value)
        log.info(f"[Wish Import][{i.user.id}]: [Authkey]{authkey}")
        if authkey is None:
            return await i.response.send_message(
                embed=error_embed().set_author(
                    name=text_map.get(363, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        else:
            client.authkey = authkey
        await i.response.send_message(
            embed=default_embed(
                f"<a:LOADER:982128111904776242> {text_map.get(355, i.locale, user_locale)}"
            ),
            ephemeral=True,
        )
        try:
            wish_history = await client.wish_history()
        except Exception as e:
            client.region = genshin.Region.CHINESE
            try:
                wish_history = await client.wish_history()
            except:
                return await i.edit_original_response(
                    embed=error_embed(message=f"```py\n{e}\n```").set_author(
                        name=text_map.get(135, i.locale, user_locale),
                        icon_url=i.user.display_avatar.url,
                    )
                )
        async with i.client.db.cursor() as c:
            c: aiosqlite.Cursor
            for wish in wish_history:
                wish_time = wish.time.strftime("%Y/%m/%d %H:%M:%S")
                await c.execute(
                    "INSERT INTO wish_history (user_id, wish_name, wish_rarity, wish_time, wish_type, wish_banner_type, wish_id) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                    (
                        i.user.id,
                        wish.name,
                        wish.rarity,
                        wish_time,
                        wish.type,
                        wish.banner_type,
                        wish.id,
                    ),
                )
            await i.client.db.commit()
        await i.edit_original_response(
            embed=default_embed(
                f"<:wish:982419859117838386> {text_map.get(356, i.locale, user_locale)}"
            )
        )
