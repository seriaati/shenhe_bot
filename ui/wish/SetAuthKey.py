import io
from typing import Any, Dict, List, Tuple

import asyncpg
import discord
import genshin
from discord import ui

import asset
import config
from apps.genshin.custom_model import Wish, WishInfo
from apps.genshin.utils import get_account_select_options, get_uid, get_wish_info_embed
from apps.text_map.convert_locale import to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from base_ui import BaseModal, BaseView
from ui.wish import ChoosePlatform
from utility.utils import DefaultEmbed, ErrorEmbed, log


class View(BaseView):
    def __init__(self, locale: discord.Locale | str, disabled: bool, empty: bool):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale
        self.add_item(ImportWishHistory(locale, not disabled))
        self.add_item(ExportWishHistory(locale, empty))
        self.add_item(LinkUID(locale, disabled))
        self.add_item(ClearWishHistory(locale, empty))


async def wish_import_command(i: discord.Interaction, responded: bool = False):
    if not responded:
        await i.response.defer()
    embed, linked, empty = await get_wish_import_embed(i)
    view = View(
        await get_user_locale(i.user.id, i.client.pool) or i.locale, linked, empty
    )
    view.message = await i.edit_original_response(embed=embed, view=view)
    view.author = i.user


class GOBack(ui.Button):
    def __init__(self):
        super().__init__(emoji=asset.back_emoji, style=discord.ButtonStyle.grey, row=4)

    async def callback(self, i: discord.Interaction):
        await wish_import_command(i)


class LinkUID(ui.Button):
    def __init__(self, locale: discord.Locale | str, disabled: bool):
        super().__init__(
            label=text_map.get(677, locale),
            style=discord.ButtonStyle.green,
            emoji=asset.link_emoji,
            disabled=disabled,
            row=0,
        )

    async def callback(self, i: discord.Interaction):
        self.view: View
        locale = self.view.locale
        embed = DefaultEmbed(description=text_map.get(681, locale)).set_author(
            name=text_map.get(677, locale), icon_url=i.user.display_avatar.url
        )
        accounts = await i.client.pool.fetch(
            "SELECT uid, ltuid, current, nickname FROM user_accounts WHERE user_id = $1",
            i.user.id,
        )
        options = get_account_select_options(accounts, str(locale))  # type: ignore
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(UIDSelect(locale, options))
        await i.response.edit_message(embed=embed, view=self.view)


class UIDSelect(ui.Select):
    def __init__(
        self, locale: discord.Locale | str, options: List[discord.SelectOption]
    ):
        super().__init__(placeholder=text_map.get(682, locale), options=options)

    async def callback(self, i: discord.Interaction):
        pool: asyncpg.pool.Pool = i.client.pool  # type: ignore
        await pool.execute(
            "UPDATE wish_history SET uid = $1 WHERE user_id = $2",
            self.values[0],
            i.user.id,
        )
        await wish_import_command(i)


class ImportWishHistory(ui.Button):
    def __init__(self, locale: discord.Locale | str, disabled: bool):
        super().__init__(
            label=text_map.get(678, locale),
            style=discord.ButtonStyle.blurple,
            emoji=asset.import_emoji,
            row=0,
            disabled=disabled,
        )

    async def callback(self, i: discord.Interaction):
        self.view: View
        locale = self.view.locale
        embed = DefaultEmbed().set_author(
            name=text_map.get(685, locale), icon_url=i.user.display_avatar.url
        )
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(ImportGenshinImpact(locale))
        self.view.add_item(ImportShenhe(locale))
        await i.response.edit_message(embed=embed, view=self.view)


class ImportGenshinImpact(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        self.locale = locale

        super().__init__(
            label=text_map.get(313, locale),
            emoji=asset.genshin_emoji,
            row=0,
        )

    async def callback(self, i: discord.Interaction):
        embed = DefaultEmbed().set_author(
            name=text_map.get(365, self.locale), icon_url=i.user.display_avatar.url
        )
        view = ChoosePlatform.View(self.locale)
        view.add_item(GOBack())
        await i.response.edit_message(embed=embed, view=view)
        view.message = await i.original_response()
        view.author = i.user


class ImportShenhe(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        self.locale = locale

        super().__init__(
            label=text_map.get(684, locale),
            emoji=asset.shenhe_emoji,
            row=0,
        )

    async def callback(self, i: discord.Interaction):
        embed = DefaultEmbed(description=(text_map.get(687, self.locale))).set_author(
            name=(text_map.get(686, self.locale)),
            icon_url=i.user.display_avatar.url,
        )
        await i.response.send_message(embed=embed, ephemeral=True)


class ExportWishHistory(ui.Button):
    def __init__(self, locale: discord.Locale | str, disabled: bool):
        super().__init__(
            label=text_map.get(679, locale),
            style=discord.ButtonStyle.blurple,
            emoji=asset.export_emoji,
            row=0,
            disabled=disabled,
        )

    async def callback(self, i: discord.Interaction):
        await i.response.defer(ephemeral=True)
        s = io.StringIO()

        wishes: List[Dict[str, Any]] = []
        pool: asyncpg.pool.Pool = i.client.pool  # type: ignore
        rows = await pool.fetch(
            "SELECT wish_name, wish_rarity, wish_time, wish_banner_type, wish_id, item_id FROM wish_history WHERE user_id = $1 AND uid = $2 ORDER BY wish_id DESC",
            i.user.id,
            await get_uid(i.user.id, pool),
        )
        for row in rows:
            wishes.append(
                {
                    "wish_name": row["wish_name"],
                    "wish_rarity": row["wish_rarity"],
                    "wish_time": row["wish_time"],
                    "wish_banner_type": row["wish_banner_type"],
                    "wish_id": row["wish_id"],
                    "item_id": row["item_id"],
                }
            )

        s.write(str(wishes))
        s.seek(0)
        await i.followup.send(
            file=discord.File(s, "shenhe_wish_export.txt"), ephemeral=True
        )


class ClearWishHistory(ui.Button):
    def __init__(self, locale: discord.Locale | str, disabled: bool):
        super().__init__(
            label=text_map.get(680, locale),
            style=discord.ButtonStyle.red,
            row=1,
            disabled=disabled,
        )

    async def callback(self, i: discord.Interaction):
        self.view: View
        locale = self.view.locale
        embed = DefaultEmbed(description=text_map.get(689, locale)).set_author(
            name=text_map.get(688, locale), icon_url=i.user.display_avatar.url
        )
        self.view.clear_items()
        self.view.add_item(Confirm(locale))
        self.view.add_item(Cancel(locale))
        await i.response.edit_message(embed=embed, view=self.view)


class Confirm(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            label=text_map.get(388, locale),
            style=discord.ButtonStyle.red,
        )

    async def callback(self, i: discord.Interaction):
        pool: asyncpg.pool.Pool = i.client.pool  # type: ignore

        uid = await get_uid(i.user.id, pool)
        await pool.execute(
            "DELETE FROM wish_history WHERE uid = $1 AND user_id = $2",
            uid,
            i.user.id,
        )
        await wish_import_command(i)


class Cancel(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            label=text_map.get(389, locale),
            style=discord.ButtonStyle.gray,
        )

    async def callback(self, i: discord.Interaction):
        await wish_import_command(i)


class ConfirmWishImport(ui.Button):
    def __init__(
        self,
        locale: discord.Locale | str,
        wish_history: List[genshin.models.Wish] | List[Dict[str, Any]],
        from_text_file: bool = False,
    ):
        super().__init__(
            label=text_map.get(388, locale),
            style=discord.ButtonStyle.green,
        )
        self.wish_history = wish_history
        self.from_text_file = from_text_file

    async def callback(self, i: discord.Interaction):
        self.view: View
        pool: asyncpg.pool.Pool = i.client.pool  # type: ignore

        uid = await get_uid(i.user.id, pool)
        embed = DefaultEmbed().set_author(
            name=text_map.get(355, self.view.locale), icon_url=asset.loader
        )
        await i.response.edit_message(embed=embed, view=None)

        if self.from_text_file:
            for wish in self.wish_history:
                if not isinstance(wish, dict):
                    raise AssertionError
                await pool.execute(
                    "INSERT INTO wish_history (user_id, wish_name, wish_rarity, wish_time, wish_banner_type, wish_id, uid, item_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) ON CONFLICT DO NOTHING",
                    i.user.id,
                    wish["wish_name"],
                    wish["wish_rarity"],
                    wish["wish_time"],
                    wish["wish_banner_type"],
                    wish["wish_id"],
                    uid,
                    wish["item_id"],
                )
        else:
            for wish in self.wish_history:
                if not isinstance(wish, genshin.models.Wish):
                    raise AssertionError
                await pool.execute(
                    """
                    INSERT INTO wish_history
                    (wish_id, user_id, uid, wish_name, wish_rarity,
                    wish_time, wish_type, wish_banner_type, item_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT DO NOTHING
                    """,
                    wish.id,
                    i.user.id,
                    uid,
                    wish.name,
                    wish.rarity,
                    wish.time,
                    wish.type,
                    wish.banner_type,
                    text_map.get_id_from_name(wish.name),
                )

        banners = (100, 200, 301, 302, 400)
        for banner in banners:
            wishes = await pool.fetch(
                "SELECT wish_id, wish_rarity, pity_pull FROM wish_history WHERE user_id = $1 AND wish_banner_type = $2 AND uid = $3 ORDER BY wish_id ASC",
                i.user.id,
                banner,
                uid,
            )

            if not wishes:
                count = 1
            else:
                if wishes[-1]["pity_pull"] is None:
                    count = 1
                else:
                    count = wishes[-1]["pity_pull"] + 1

            for wish in wishes:
                await pool.execute(
                    "UPDATE wish_history SET pity_pull = $1 WHERE user_id = $2 AND wish_id = $3 AND uid = $4",
                    count,
                    i.user.id,
                    wish["wish_id"],
                    uid,
                )
                if wish["wish_rarity"] == 5:
                    count = 1
                else:
                    count += 1

        await wish_import_command(i, True)


class CancelWishImport(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            label=text_map.get(389, locale),
            style=discord.ButtonStyle.gray,
        )

    async def callback(self, i: discord.Interaction):
        await wish_import_command(i)


class Modal(BaseModal):
    url = ui.TextInput(
        label="Auth Key URL",
        placeholder="請ctrl+v貼上複製的連結",
        style=discord.TextStyle.long,
        required=True,
    )

    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            title=text_map.get(353, locale),
            timeout=config.mid_timeout,
            custom_id="authkey_modal",
        )
        self.url.label = text_map.get(352, locale)
        self.url.placeholder = text_map.get(354, locale)

    async def on_submit(self, i: discord.Interaction):
        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
        authkey = genshin.utility.extract_authkey(self.url.value)
        log.info(f"[Wish Import][{i.user.id}]: [Authkey]{authkey}")
        if authkey is None:
            await i.response.edit_message(
                embed=ErrorEmbed().set_author(
                    name=text_map.get(363, locale),
                    icon_url=i.user.display_avatar.url,
                ),
                view=None,
            )
            return await wish_import_command(i, True)

        client: genshin.Client = i.client.genshin_client
        client.lang = to_genshin_py(locale)
        uid = await get_uid(i.user.id, i.client.pool)
        if str(uid)[0] in ["1", "2", "5"]:
            client.region = genshin.Region.CHINESE
            client.region = genshin.Region.OVERSEAS
        client.authkey = authkey

        await i.response.edit_message(
            embed=DefaultEmbed().set_author(
                name=text_map.get(355, locale),
                icon_url="https://i.imgur.com/V76M9Wa.gif",
            ),
            view=None,
        )
        try:
            wish_history = await client.wish_history()
        except genshin.errors.InvalidAuthkey:
            return await i.edit_original_response(
                embed=ErrorEmbed().set_author(
                    name=text_map.get(363, locale),
                    icon_url=i.user.display_avatar.url,
                )
            )
        except genshin.errors.AuthkeyTimeout:
            return await i.edit_original_response(
                embed=ErrorEmbed().set_author(
                    name=text_map.get(702, locale),
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
                time=newest_wish.time,
                name=newest_wish.name,
                rarity=newest_wish.rarity,
            ),
            oldest_wish=Wish(
                time=oldest_wish.time,
                name=oldest_wish.name,
                rarity=oldest_wish.rarity,
            ),
            character_banner_num=character_banner,
            weapon_banner_num=weapon_banner,
            permanent_banner_num=permanent_banner,
            novice_banner_num=novice_banner,
        )
        embed = await get_wish_info_embed(i, str(locale), wish_info, True)
        view = View(locale, True, True)
        view.author = i.user
        view.clear_items()
        view.add_item(ConfirmWishImport(locale, list(wish_history)))
        view.add_item(CancelWishImport(locale))
        view.message = await i.edit_original_response(embed=embed, view=view)


async def get_wish_import_embed(
    i: discord.Interaction,
) -> Tuple[discord.Embed, bool, bool]:
    linked = True
    pool: asyncpg.pool.Pool = i.client.pool  # type: ignore
    locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
    uid = await get_uid(i.user.id, i.client.pool)

    wish_data = await pool.fetch(
        """
        SELECT wish_time, wish_rarity, item_id, wish_banner_type, uid
        FROM wish_history
        WHERE user_id = $1
        ORDER BY wish_id DESC
        """,
        i.user.id,
    )
    if not wish_data:
        embed = DefaultEmbed(description=f"UID: {uid}").set_author(
            name=text_map.get(683, locale),
            icon_url=i.user.display_avatar.url,
        )
        return embed, linked, True
    if any(wish["uid"] is None for wish in wish_data):
        linked = False

    newest_wish = wish_data[0]
    oldest_wish = wish_data[-1]
    character_banner = 0
    weapon_banner = 0
    permanent_banner = 0
    novice_banner = 0
    for wish in wish_data:
        banner = wish["wish_banner_type"]
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
            time=newest_wish["wish_time"],
            rarity=newest_wish["wish_rarity"],
            name=text_map.get_weapon_name(int(newest_wish["item_id"]), locale)
            or text_map.get_character_name(str(newest_wish["item_id"]), locale)
            or "",
        ),
        oldest_wish=Wish(
            time=oldest_wish["wish_time"],
            rarity=oldest_wish["wish_rarity"],
            name=text_map.get_weapon_name(int(oldest_wish["item_id"]), locale)
            or text_map.get_character_name(str(oldest_wish["item_id"]), locale)
            or "",
        ),
        character_banner_num=character_banner,
        weapon_banner_num=weapon_banner,
        permanent_banner_num=permanent_banner,
        novice_banner_num=novice_banner,
    )
    embed = await get_wish_info_embed(
        i, str(locale), wish_info, import_command=True, linked=linked
    )
    return embed, linked, False
