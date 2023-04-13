import io
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import asyncpg
import discord
import genshin
import yaml
from discord import ui

import dev.asset as asset
import dev.config as config
from apps.text_map import text_map, to_genshin_py
from apps.wish.models import WishHistory, WishInfo
from dev.base_ui import BaseModal, BaseView
from dev.models import DefaultEmbed, ErrorEmbed, Inter
from ui.wish import choose_platform
from utils import (
    get_account_select_options,
    get_uid,
    get_user_lang,
    get_wish_info_embed,
    log,
)


class View(BaseView):
    def __init__(
        self, locale: discord.Locale | str, disabled: bool, empty: bool
    ) -> None:
        super().__init__(timeout=config.long_timeout)
        self.locale = locale
        self.add_item(ImportWishHistory(locale, not disabled))
        self.add_item(ExportWishHistory(locale, empty))
        self.add_item(LinkUID(locale, disabled))
        self.add_item(ClearWishHistory(locale, empty))


async def wish_import_command(i: Inter, responded: bool = False) -> None:
    if not responded:
        await i.response.defer()
    embed, linked, empty = await get_wish_import_embed(i)
    view = View(
        await get_user_lang(i.user.id, i.client.pool) or i.locale, linked, empty
    )
    view.message = await i.edit_original_response(embed=embed, view=view)
    view.author = i.user


class GOBack(ui.Button):
    def __init__(self) -> None:
        super().__init__(emoji=asset.back_emoji, style=discord.ButtonStyle.grey, row=4)

    @staticmethod
    async def callback(i: Inter) -> None:
        await wish_import_command(i)


class LinkUID(ui.Button):
    def __init__(self, locale: discord.Locale | str, disabled: bool) -> None:
        super().__init__(
            label=text_map.get(677, locale),
            style=discord.ButtonStyle.green,
            emoji=asset.link_emoji,
            disabled=disabled,
            row=0,
        )
        self.view: View

    async def callback(self, i: Inter) -> None:
        locale = self.view.locale
        embed = DefaultEmbed(description=text_map.get(681, locale)).set_author(
            name=text_map.get(677, locale), icon_url=i.user.display_avatar.url
        )
        accounts = await i.client.pool.fetch(
            """
            SELECT uid,
                ltuid,
                current,
                nickname
            FROM   user_accounts
            WHERE  user_id = $1
            """,
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
    ) -> None:
        super().__init__(placeholder=text_map.get(682, locale), options=options)

    async def callback(self, i: Inter) -> None:
        pool: asyncpg.pool.Pool = i.client.pool  # type: ignore
        await pool.execute(
            """
            UPDATE wish_history
            SET    uid = $1
            WHERE  user_id = $2
            """,
            int(self.values[0]),
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
        self.view: View

    async def callback(self, i: Inter):
        locale = self.view.locale
        embed = DefaultEmbed().set_author(
            name=text_map.get(685, locale), icon_url=i.user.display_avatar.url
        )
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(ImportGenshin(locale))
        self.view.add_item(ImportShenhe(locale))
        await i.response.edit_message(embed=embed, view=self.view)


class ImportGenshin(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        self.locale = locale

        super().__init__(
            label=text_map.get(313, locale),
            emoji=asset.genshin_emoji,
            row=0,
        )

    async def callback(self, i: Inter):
        embed = DefaultEmbed().set_author(
            name=text_map.get(365, self.locale), icon_url=i.user.display_avatar.url
        )
        view = choose_platform.View(self.locale)
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

    async def callback(self, i: Inter):
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

    @staticmethod
    async def callback(i: Inter):
        await i.response.defer(ephemeral=True)
        s = io.StringIO()

        wishes: List[Dict[str, Any]] = []
        pool: asyncpg.pool.Pool = i.client.pool  # type: ignore
        rows = await pool.fetch(
            """
            SELECT *
            FROM wish_history
            WHERE user_id = $1
                AND UID = $2
            ORDER BY wish_id DESC
            """,
            i.user.id,
            await get_uid(i.user.id, pool),
        )
        history = [WishHistory.from_row(row) for row in rows]
        wishes = [wish.to_dict() for wish in history]

        s.write(str(yaml.safe_dump(wishes, indent=4, allow_unicode=True)))
        s.seek(0)
        await i.followup.send(
            file=discord.File(s, f"SHENHE_WISH_{uuid4()}.yaml"), ephemeral=True  # type: ignore
        )


class ClearWishHistory(ui.Button):
    def __init__(self, locale: discord.Locale | str, disabled: bool):
        super().__init__(
            label=text_map.get(680, locale),
            style=discord.ButtonStyle.red,
            row=1,
            disabled=disabled,
        )
        self.view: View

    async def callback(self, i: Inter):
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

    @staticmethod
    async def callback(i: Inter):
        pool: asyncpg.pool.Pool = i.client.pool  # type: ignore

        uid = await get_uid(i.user.id, pool)
        await pool.execute(
            """
            DELETE
            FROM wish_history
            WHERE UID = $1
                AND user_id = $2
            """,
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

    @staticmethod
    async def callback(i: Inter):
        await wish_import_command(i)


class ConfirmWishimport(ui.Button):
    def __init__(
        self,
        locale: discord.Locale | str,
        wish_history: List[genshin.models.Wish] | List[WishHistory],
        from_text_file: bool = False,
    ) -> None:
        super().__init__(
            label=text_map.get(388, locale),
            style=discord.ButtonStyle.green,
        )
        self.wish_history = wish_history
        self.from_text_file = from_text_file
        self.view: View

    async def callback(self, i: Inter) -> None:
        pool: asyncpg.pool.Pool = i.client.pool

        uid = await get_uid(i.user.id, pool)
        embed = DefaultEmbed().set_author(
            name=text_map.get(355, self.view.locale), icon_url=asset.loader
        )
        await i.response.edit_message(embed=embed, view=None)

        if self.from_text_file:
            for wish in self.wish_history:
                if not isinstance(wish, WishHistory):
                    raise AssertionError
                await pool.execute(
                    """
                    INSERT INTO wish_history
                    (wish_id, user_id, uid, wish_name,
                    wish_rarity, wish_time, wish_type,
                    wish_banner_type, item_id, pity_pull)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT DO NOTHING
                    """,
                    wish.id,
                    wish.user_id,
                    wish.uid,
                    wish.name,
                    wish.rarity,
                    wish.time.replace(tzinfo=None),
                    wish.type,
                    wish.banner,
                    wish.item_id,
                    wish.pity,
                )
        else:
            for wish in self.wish_history:
                if not isinstance(wish, genshin.models.Wish):
                    raise AssertionError
                await pool.execute(
                    """
                    INSERT INTO wish_history
                    (wish_id, user_id, UID, wish_name, wish_rarity,
                    wish_time, wish_type, wish_banner_type,
                    item_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT DO NOTHING
                    """,
                    wish.id,
                    i.user.id,
                    uid,
                    wish.name,
                    wish.rarity,
                    wish.time.replace(tzinfo=None),
                    wish.type,
                    wish.banner_type,
                    text_map.get_id_from_name(wish.name),
                )

        # calcualte pity pulls
        banners = (100, 200, 301, 302, 400)
        for banner in banners:
            rows = await pool.fetch(
                """
                SELECT *
                FROM    wish_history
                WHERE   user_id = $1
                    AND wish_banner_type = $2
                    AND uid = $3
                ORDER BY wish_id ASC
                """,
                i.user.id,
                banner,
                uid,
            )
            wishes = [WishHistory.from_row(row) for row in rows]

            if not wishes:
                count = 1
            else:
                if wishes[-1].pity is None:
                    count = 1
                else:
                    count = wishes[-1].pity + 1

            for wish in wishes:
                await pool.execute(
                    """
                    UPDATE wish_history
                    SET    pity_pull = $1
                    WHERE  user_id = $2
                        AND wish_id = $3
                        AND uid = $4
                    """,
                    count,
                    i.user.id,
                    wish.id,
                    uid,
                )
                if wish.rarity == 5:
                    count = 1
                else:
                    count += 1

        await wish_import_command(i, True)


class CancelWishimport(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            label=text_map.get(389, locale),
            style=discord.ButtonStyle.gray,
        )

    @staticmethod
    async def callback(i: Inter):
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

    async def on_submit(self, i: Inter):
        locale = await get_user_lang(i.user.id, i.client.pool) or i.locale
        authkey = genshin.utility.extract_authkey(self.url.value)
        log.info(f"[Wish import][{i.user.id}]: [Authkey]{authkey}")
        if authkey is None:
            await i.response.edit_message(
                embed=ErrorEmbed().set_author(
                    name=text_map.get(363, locale),
                    icon_url=i.user.display_avatar.url,
                ),
                view=None,
            )
            return await wish_import_command(i, True)

        client = genshin.Client()
        client.lang = to_genshin_py(locale)
        client.uid = await get_uid(i.user.id, i.client.pool)
        if str(client.uid)[0] in ("1", "2", "5"):
            client.region = genshin.Region.CHINESE
        else:
            client.region = genshin.Region.OVERSEAS
        client.set_authkey(authkey)

        await i.response.edit_message(
            embed=DefaultEmbed().set_author(
                name=text_map.get(355, locale),
                icon_url=asset.loader,
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

        wish_info = WishInfo(
            total=len(wish_history),
            newest_wish=WishHistory.from_genshin_wish(wish_history[0], i.user.id),
            oldest_wish=WishHistory.from_genshin_wish(wish_history[-1], i.user.id),
            character_banner_num=character_banner,
            weapon_banner_num=weapon_banner,
            permanent_banner_num=permanent_banner,
            novice_banner_num=novice_banner,
        )
        embed = await get_wish_info_embed(i, str(locale), wish_info)

        view = View(locale, True, True)
        view.author = i.user
        view.clear_items()
        view.add_item(ConfirmWishimport(locale, list(wish_history)))
        view.add_item(CancelWishimport(locale))
        view.message = await i.edit_original_response(embed=embed, view=view)


async def get_wish_import_embed(
    i: Inter,
) -> Tuple[discord.Embed, bool, bool]:
    linked = True
    pool: asyncpg.pool.Pool = i.client.pool  # type: ignore
    locale = await get_user_lang(i.user.id, i.client.pool) or i.locale
    uid = await get_uid(i.user.id, i.client.pool)

    history = await pool.fetch(
        """
        SELECT *
        FROM   wish_history
        WHERE  user_id = $1
        ORDER  BY wish_id DESC
        """,
        i.user.id,
    )
    history = [WishHistory.from_row(wish) for wish in history]
    if not history:
        embed = DefaultEmbed(description=f"UID: {uid}").set_author(
            name=text_map.get(683, locale),
            icon_url=i.user.display_avatar.url,
        )
        return embed, linked, True

    if any(wish.uid is None for wish in history):
        linked = False

    character_banner = 0
    weapon_banner = 0
    permanent_banner = 0
    novice_banner = 0
    for wish in history:
        banner = wish.banner
        if banner in (301, 400):
            character_banner += 1
        elif banner == 302:
            weapon_banner += 1
        elif banner == 200:
            permanent_banner += 1
        elif banner == 100:
            novice_banner += 1

    wish_info = WishInfo(
        total=len(history),
        newest_wish=history[0],
        oldest_wish=history[-1],
        character_banner_num=character_banner,
        weapon_banner_num=weapon_banner,
        permanent_banner_num=permanent_banner,
        novice_banner_num=novice_banner,
    )
    embed = await get_wish_info_embed(i, str(locale), wish_info, import_command=True)
    return embed, linked, False
