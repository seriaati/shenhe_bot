import io
from typing import List, Tuple

import genshin
import sentry_sdk
from discord import (
    ButtonStyle,
    Embed,
    File,
    Interaction,
    Locale,
    SelectOption,
    TextStyle,
)
from discord.ui import Button, Select, TextInput
from apps.genshin.custom_model import Wish, WishInfo

import asset
import config
from apps.genshin.utils import (
    get_account_options,
    get_uid,
    get_wish_info_embed,
)
from apps.text_map.convert_locale import to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseModal, BaseView
from UI_elements.wish import ChoosePlatform
from utility.utils import default_embed, error_embed, log


class View(BaseView):
    def __init__(self, locale: Locale | str, disabled: bool, empty: bool):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        self.add_item(ImportWishHistory(locale, not disabled))
        self.add_item(ExportWishHistory(locale, empty))
        self.add_item(LinkUID(locale, disabled))
        self.add_item(ClearWishHistory(locale, empty))


async def wish_import_command(i: Interaction, responded: bool = False):
    if not responded:
        await i.response.defer()
    embed, linked, empty = await get_wish_import_embed(i)
    view = View(
        await get_user_locale(i.user.id, i.client.db) or i.locale, linked, empty
    )
    view.message = await i.edit_original_response(embed=embed, view=view)
    view.author = i.user


class GOBack(Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, style=ButtonStyle.grey, row=4)

    async def callback(self, i: Interaction):
        await wish_import_command(i)


class LinkUID(Button):
    def __init__(self, locale: Locale | str, disabled: bool):
        super().__init__(
            label=text_map.get(677, locale),
            style=ButtonStyle.green,
            emoji=asset.link_emoji,
            disabled=disabled,
            row=0,
        )

    async def callback(self, i: Interaction):
        self.view: View
        locale = self.view.locale
        embed = default_embed(message=text_map.get(681, locale)).set_author(
            name=text_map.get(677, locale), icon_url=i.user.display_avatar.url
        )
        async with i.client.db.execute(
            "SELECT uid, ltuid, current, nickname FROM user_accounts WHERE user_id = ?",
            (i.user.id,),
        ) as cursor:
            accounts = await cursor.fetchall()
        options = get_account_options(accounts, locale)
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(UIDSelect(locale, options))
        await i.response.edit_message(embed=embed, view=self.view)


class UIDSelect(Select):
    def __init__(self, locale: Locale | str, options: List[SelectOption]):
        super().__init__(placeholder=text_map.get(682, locale), options=options)

    async def callback(self, i: Interaction):
        await i.client.db.execute(
            "UPDATE wish_history SET uid = ? WHERE user_id = ?",
            (self.values[0], i.user.id),
        )
        await i.client.db.commit()
        await wish_import_command(i)


class ImportWishHistory(Button):
    def __init__(self, locale: Locale | str, disabled: bool):
        super().__init__(
            label=text_map.get(678, locale),
            style=ButtonStyle.blurple,
            emoji=asset.import_emoji,
            row=0,
            disabled=disabled,
        )

    async def callback(self, i: Interaction):
        self.view: View
        locale = self.view.locale
        embed = default_embed().set_author(
            name=text_map.get(685, locale), icon_url=i.user.display_avatar.url
        )
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(ImportGenshinImpact(locale))
        self.view.add_item(ImportShenhe(locale))
        self.view.add_item(ImportPaimonMoe())
        await i.response.edit_message(embed=embed, view=self.view)


class ImportGenshinImpact(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            label=text_map.get(313, locale),
            emoji=asset.genshin_emoji,
            row=0,
        )

    async def callback(self, i: Interaction):
        embed = default_embed().set_author(
            name=text_map.get(365, self.view.locale), icon_url=i.user.display_avatar.url
        )
        view = ChoosePlatform.View(self.view.locale)
        view.add_item(GOBack())
        await i.response.edit_message(embed=embed, view=view)
        view.message = await i.original_response()
        view.author = i.user


class ImportShenhe(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            label=text_map.get(684, locale),
            emoji=asset.shenhe_emoji,
            row=0,
        )

    async def callback(self, i: Interaction):
        embed = default_embed(message=(text_map.get(687, self.view.locale))).set_author(
            name=(text_map.get(686, self.view.locale)),
            icon_url=i.user.display_avatar.url,
        )
        await i.response.send_message(embed=embed, ephemeral=True)

class ImportPaimonMoe(Button):
    def __init__(self):
        super().__init__(label="Paimon.moe", row=0)
        
    async def callback(self, i: Interaction):
        embed = default_embed(message=(text_map.get(687, self.view.locale))).set_author(
            name=(text_map.get(686, self.view.locale)),
            icon_url=i.user.display_avatar.url,
        )
        await i.response.send_message(embed=embed, ephemeral=True)
        

class ExportWishHistory(Button):
    def __init__(self, locale: Locale | str, disabled: bool):
        super().__init__(
            label=text_map.get(679, locale),
            style=ButtonStyle.blurple,
            emoji=asset.export_emoji,
            row=0,
            disabled=disabled,
        )

    async def callback(self, i: Interaction):
        await i.response.defer(ephemeral=True)
        s = io.StringIO()
        async with i.client.db.execute(
            "SELECT wish_name, wish_rarity, wish_time, wish_banner_type, wish_id, item_id FROM wish_history WHERE user_id = ? AND uid = ? ORDER BY wish_id DESC",
            (i.user.id, await get_uid(i.user.id, i.client.db)),
        ) as c:
            wishes = await c.fetchall()
        s.write(str(wishes))
        s.seek(0)
        await i.followup.send(file=File(s, "shenhe_wish_export.txt"), ephemeral=True)


class ClearWishHistory(Button):
    def __init__(self, locale: Locale | str, disabled: bool):
        super().__init__(
            label=text_map.get(680, locale),
            style=ButtonStyle.red,
            row=1,
            disabled=disabled,
        )

    async def callback(self, i: Interaction):
        self.view: View
        locale = self.view.locale
        embed = default_embed(message=text_map.get(689, locale)).set_author(
            name=text_map.get(688, locale), icon_url=i.user.display_avatar.url
        )
        self.view.clear_items()
        self.view.add_item(Confirm(locale))
        self.view.add_item(Cancel(locale))
        await i.response.edit_message(embed=embed, view=self.view)


class Confirm(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            label=text_map.get(388, locale),
            style=ButtonStyle.red,
        )

    async def callback(self, i: Interaction):
        uid = await get_uid(i.user.id, i.client.db)
        await i.client.db.execute(
            "DELETE FROM wish_history WHERE uid = ? AND user_id = ?", (uid, i.user.id)
        )
        await i.client.db.commit()
        await wish_import_command(i)


class Cancel(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            label=text_map.get(389, locale),
            style=ButtonStyle.gray,
        )

    async def callback(self, i: Interaction):
        await wish_import_command(i)


class ConfirmWishImport(Button):
    def __init__(
        self,
        locale: Locale | str,
        wish_history: List[genshin.models.Wish],
        from_text_file: bool = False,
    ):
        super().__init__(
            label=text_map.get(388, locale),
            style=ButtonStyle.green,
        )
        self.wish_history = wish_history
        self.from_text_file = from_text_file

    async def callback(self, i: Interaction):
        embed = default_embed().set_author(
            name=text_map.get(355, self.view.locale), icon_url=asset.loader
        )
        await i.response.edit_message(embed=embed, view=None)
        if self.from_text_file:
            for item in self.wish_history:
                name = item[0]
                rarity = item[1]
                time = item[2]
                banner = item[3]
                wish_id = item[4]
                item_id = item[5]
                await i.client.db.execute(
                    "INSERT INTO wish_history (user_id, wish_name, wish_rarity, wish_time, wish_banner_type, wish_id, uid, item_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) ON CONFLICT DO NOTHING",
                    (
                        i.user.id,
                        name,
                        rarity,
                        time,
                        banner,
                        wish_id,
                        await get_uid(i.user.id, i.client.db),
                        item_id,
                    ),
                )
        else:
            for wish in self.wish_history:
                await i.client.db.execute(
                    "INSERT INTO wish_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                    (
                        i.user.id,
                        wish.name,
                        wish.rarity,
                        wish.time.strftime("%Y/%m/%d %H:%M:%S"),
                        wish.type,
                        wish.banner_type,
                        wish.id,
                        await get_uid(i.user.id, i.client.db),
                        text_map.get_id_from_name(wish.name),
                    ),
                )
        await i.client.db.commit()
        await wish_import_command(i, True)


class CancelWishImport(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            label=text_map.get(389, locale),
            style=ButtonStyle.gray,
        )

    async def callback(self, i: Interaction):
        await wish_import_command(i)


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
        locale = await get_user_locale(i.user.id, i.client.db) or i.locale
        client: genshin.Client = i.client.genshin_client
        client.lang = to_genshin_py(locale)
        authkey = genshin.utility.extract_authkey(self.url.value)
        log.info(f"[Wish Import][{i.user.id}]: [Authkey]{authkey}")
        if authkey is None:
            await i.response.edit_message(
                embed=error_embed().set_author(
                    name=text_map.get(363, locale),
                    icon_url=i.user.display_avatar.url,
                ),
                view=None,
            )
            return await wish_import_command(i, True)
        else:
            client.authkey = authkey
        await i.response.edit_message(
            embed=default_embed().set_author(
                name=text_map.get(355, locale),
                icon_url="https://i.imgur.com/V76M9Wa.gif",
            ),
            view=None,
        )
        try:
            wish_history = await client.wish_history()
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return await i.edit_original_response(
                embed=error_embed(message=f"```py\n{e}\n```").set_author(
                    name=text_map.get(135, locale),
                    icon_url=i.user.display_avatar.url,
                )
            )
        character_banner = 0
        weapon_banner = 0
        permanent_banner = 0
        novice_banner = 0
        for wish in wish_history:
            if wish.banner_type == genshin.models.BannerType.CHARACTER:
                character_banner += 1
            elif wish.banner_type == genshin.models.BannerType.WEAPON:
                weapon_banner += 1
            elif wish.banner_type == genshin.models.BannerType.PERMANENT:
                permanent_banner += 1
            elif wish.banner_type == genshin.models.BannerType.NOVICE:
                novice_banner += 1
        newest_wish = wish_history[0]
        oldest_wish = wish_history[-1]
        wish_info = WishInfo(
            total=len(wish_history),
            newest_wish=Wish(
                time=newest_wish.time.strftime("%Y/%m/%d %H:%M:%S"),
                name=newest_wish.name,
                rarity=newest_wish.rarity,
            ),
            oldest_wish=Wish(
                time=oldest_wish.time.strftime("%Y/%m/%d %H:%M:%S"),
                name=oldest_wish.name,
                rarity=oldest_wish.rarity,
            ),
            character_banner_num=character_banner,
            weapon_banner_num=weapon_banner,
            permanent_banner_num=permanent_banner,
            novice_banner_num=novice_banner,
        )
        embed = await get_wish_info_embed(i, locale, wish_info)
        view = View(locale, True, True)
        view.author = i.user
        view.clear_items()
        view.add_item(ConfirmWishImport(locale, wish_history))
        view.add_item(CancelWishImport(locale))
        view.message = await i.edit_original_response(embed=embed, view=view)


async def get_wish_import_embed(i: Interaction) -> Tuple[Embed, bool, bool]:
    linked = True
    locale = await get_user_locale(i.user.id, i.client.db) or i.locale
    uid = await get_uid(i.user.id, i.client.db)
    async with i.client.db.execute(
        "SELECT wish_time, wish_rarity, item_id, wish_banner_type FROM wish_history WHERE user_id = ? AND uid IS NULL ORDER BY wish_id DESC",
        (i.user.id,),
    ) as c:  # 檢查是否有未綁定 UID 的歷史紀錄
        wish_data = await c.fetchall()
        if not wish_data:  # 沒有未綁定 UID 的歷史紀錄
            await c.execute(
                "SELECT wish_time, wish_rarity, item_id, wish_banner_type FROM wish_history WHERE user_id = ? AND uid = ? ORDER BY wish_id DESC",
                (i.user.id, uid),
            )  # 檢查是否有綁定 UID 的歷史紀錄
            wish_data = await c.fetchall()
            if not wish_data:  # 使用者完全沒有任何歷史紀錄
                embed = default_embed(message=f"UID: {uid}").set_author(
                    name=text_map.get(683, locale),
                    icon_url=i.user.display_avatar.url,
                )
                return embed, linked, True
        else:  # 有未綁定 UID 的歷史紀錄
            linked = False
    newest_wish = wish_data[0]
    oldest_wish = wish_data[-1]
    character_banner = 0
    weapon_banner = 0
    permanent_banner = 0
    novice_banner = 0
    for wish in wish_data:
        banner = wish[3]
        if banner in [301, 400]:
            character_banner += 1
        elif banner == 302:
            weapon_banner += 1
        elif banner == 200:
            permanent_banner += 1
        elif banner == 100:
            novice_banner += 1
    wish_info = WishInfo(
        total=len(wish_data),
        newest_wish=Wish(
            time=newest_wish[0],
            rarity=newest_wish[1],
            name=text_map.get_weapon_name(int(newest_wish[2]), locale) or text_map.get_character_name(int(newest_wish[2]), locale),
        ),
        oldest_wish=Wish(
            time=oldest_wish[0],
            rarity=oldest_wish[1],
            name=text_map.get_weapon_name(int(oldest_wish[2]), locale) or text_map.get_character_name(int(oldest_wish[2]), locale),
        ),
        character_banner_num=character_banner,
        weapon_banner_num=weapon_banner,
        permanent_banner_num=permanent_banner,
        novice_banner_num=novice_banner,
    )
    embed = await get_wish_info_embed(i, locale, wish_info, import_command=True, linked=linked)
    return embed, linked, False
