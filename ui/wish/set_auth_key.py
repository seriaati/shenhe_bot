import io
from typing import List, Union
from uuid import uuid4

import discord
import genshin
import yaml
from discord import ui

import dev.asset as asset
import dev.config as config
from apps.db.tables.hoyo_account import HoyoAccount
from apps.db.tables.wish_history import WishHistoryTable
from apps.text_map import text_map
from apps.wish.models import WishHistory, WishInfo
from dev.base_ui import BaseButton, BaseModal, BaseView
from dev.models import DefaultEmbed, ErrorEmbed, Inter
from utils import get_account_options, get_wish_info_embed


class View(BaseView):
    def __init__(self) -> None:
        super().__init__(timeout=config.long_timeout)

        self.lang: str
        self.user: HoyoAccount
        self.author: Union[discord.User, discord.Member]
        self.wishes: List[WishHistory]

    async def init(self, i: Inter) -> None:
        user = await i.client.db.users.get(i.user.id)
        settings = await user.settings
        self.user = user
        self.lang = settings.lang or str(i.locale)
        self.author = i.user

    async def get_wishes(
        self, wish_table: WishHistoryTable, linked: bool
    ) -> List[WishHistory]:
        if linked:
            self.wishes = await wish_table.get_with_uid(self.user.uid)
        else:
            self.wishes = await wish_table.get_with_user_id(self.user.user_id)
        return self.wishes

    async def start(self, i: Inter) -> None:
        await i.response.defer()
        await self.init(i)

        linked = await i.client.db.wish.check_linked(self.user.user_id)
        await self.get_wishes(i.client.db.wish, linked)
        self.add_components(linked)
        embed = self.get_wish_import_embed(linked)

        await i.followup.send(embed=embed, view=self)
        self.message = await i.original_response()

    def get_wish_import_embed(self, linked: bool) -> discord.Embed:
        if not self.wishes:
            embed = ErrorEmbed(description=f"UID: {self.user.uid}")
            embed.set_title(683, self.lang, self.author)
            return embed

        character_banner = 0
        weapon_banner = 0
        permanent_banner = 0
        novice_banner = 0
        for wish in self.wishes:
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
            total=len(self.wishes),
            newest_wish=self.wishes[0],
            oldest_wish=self.wishes[-1],
            character_banner_num=character_banner,
            weapon_banner_num=weapon_banner,
            permanent_banner_num=permanent_banner,
            novice_banner_num=novice_banner,
        )

        return get_wish_info_embed(
            self.author,
            self.lang,
            wish_info,
            self.user.uid,
            linked,
            import_command=True,
        )

    def add_components(self, linked: bool) -> None:
        self.clear_items()
        self.add_item(ImportWishHistory(self.lang, not linked))
        self.add_item(ExportWishHistory(self.lang, not self.wishes))
        self.add_item(LinkUID(self.lang, linked))
        self.add_item(ClearWishHistory(self.lang, not self.wishes))


class GOBack(ui.Button):
    def __init__(self) -> None:
        super().__init__(emoji=asset.back_emoji, style=discord.ButtonStyle.grey, row=4)
        self.view: View

    async def callback(self, i: Inter) -> None:
        await i.response.defer()
        linked = await i.client.db.wish.check_linked(self.view.user.user_id)
        await self.view.get_wishes(i.client.db.wish, linked)
        embed = self.view.get_wish_import_embed(linked)
        self.view.add_components(linked)
        await i.followup.send(embed=embed, view=self.view)


class LinkUID(ui.Button):
    def __init__(self, lang: str, disabled: bool) -> None:
        super().__init__(
            label=text_map.get(677, lang),
            style=discord.ButtonStyle.green,
            emoji=asset.link_emoji,
            disabled=disabled,
            row=0,
        )
        self.view: View

    async def callback(self, i: Inter) -> None:
        lang = self.view.lang
        embed = DefaultEmbed(description=text_map.get(681, lang)).set_author(
            name=text_map.get(677, lang), icon_url=i.user.display_avatar.url
        )
        accounts = await i.client.db.users.get_all_of_user(i.user.id)
        options = get_account_options(accounts)
        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(UIDSelect(lang, options))
        await i.response.edit_message(embed=embed, view=self.view)


class UIDSelect(ui.Select):
    def __init__(self, lang: str, options: List[discord.SelectOption]) -> None:
        super().__init__(placeholder=text_map.get(682, lang), options=options)
        self.view: View

    async def callback(self, i: Inter) -> None:
        uid = int(self.values[0])
        await i.client.pool.execute(
            """
            UPDATE wish_history
            SET uid = $1
            WHERE user_id = $2
            """,
            uid,
            i.user.id,
        )

        await i.client.db.wish.get_with_uid(uid)
        embed = self.view.get_wish_import_embed(True)
        self.view.add_components(True)
        await i.response.edit_message(embed=embed, view=self.view)


class ImportWishHistory(ui.Button):
    def __init__(self, lang: str, disabled: bool):
        super().__init__(
            label=text_map.get(678, lang),
            style=discord.ButtonStyle.blurple,
            emoji=asset.import_emoji,
            row=0,
            disabled=disabled,
        )
        self.view: View

    async def callback(self, i: Inter):
        lang = self.view.lang
        embed = DefaultEmbed()
        embed.set_title(474, lang, i.user)

        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(ImportGenshin(lang))
        self.view.add_item(ImportShenhe(lang))

        await i.response.edit_message(embed=embed, view=self.view)


class ImportGenshin(ui.Button):
    def __init__(self, lang: str):
        self.lang = lang

        super().__init__(
            label=text_map.get(313, lang),
            emoji=asset.genshin_emoji,
            row=0,
        )
        self.view: View

    async def callback(self, i: Inter):
        embed = DefaultEmbed(description=text_map.get(779, self.lang))
        embed.set_title(474, self.lang, i.user)

        self.view.clear_items()
        self.view.add_item(GOBack())
        self.view.add_item(SubmitLink(text_map.get(477, self.lang)))
        await i.response.edit_message(embed=embed, view=self.view)


class SubmitLink(ui.Button):
    def __init__(self, label: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.green,
            row=0,
            emoji=asset.import_emoji,
        )
        self.view: View

    async def callback(self, i: Inter):
        modal = AuthKeyModal(self.view.lang)
        await i.response.send_modal(modal)
        await modal.wait()

        authkey = genshin.utility.extract_authkey(modal.url.value)
        if authkey is None:
            embed = ErrorEmbed()
            embed.set_title(363, self.view.lang, i.user)
            return await i.response.send_message(
                embed=embed,
            )

        await i.edit_original_response(
            embed=DefaultEmbed().set_author(
                name=text_map.get(355, self.view.lang),
                icon_url=asset.loader,
            ),
            view=None,
        )

        client = await self.view.user.client
        client.set_authkey(authkey)
        wish_history = await client.wish_history()

        character_banner = 0
        weapon_banner = 0
        permanent_banner = 0
        novice_banner = 0
        for wish in wish_history:
            if wish.banner_type is genshin.models.BannerType.CHARACTER:
                character_banner += 1
            elif wish.banner_type is genshin.models.BannerType.WEAPON:
                weapon_banner += 1
            elif wish.banner_type is genshin.models.BannerType.PERMANENT:
                permanent_banner += 1
            elif wish.banner_type is genshin.models.BannerType.NOVICE:
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

        linked = await i.client.db.wish.check_linked(self.view.user.user_id)
        embed = get_wish_info_embed(
            i.user, self.view.lang, wish_info, self.view.user.uid, linked
        )

        self.view.clear_items()
        self.view.add_item(ConfirmWishimport(self.view.lang, list(wish_history)))
        self.view.add_item(CancelWishimport(self.view.lang))
        await i.edit_original_response(embed=embed, view=self.view)


class ImportShenhe(ui.Button):
    def __init__(self, lang: str):
        self.lang = lang

        super().__init__(
            label=text_map.get(684, lang),
            emoji=asset.shenhe_emoji,
            row=0,
        )

    async def callback(self, i: Inter):
        embed = DefaultEmbed(description=(text_map.get(687, self.lang)))
        embed.set_title(686, self.lang, i.user)
        await i.response.send_message(embed=embed, ephemeral=True)


class ExportWishHistory(BaseButton):
    def __init__(self, lang: str, disabled: bool):
        super().__init__(
            label=text_map.get(679, lang),
            style=discord.ButtonStyle.blurple,
            emoji=asset.export_emoji,
            row=0,
            disabled=disabled,
        )
        self.view: View

    async def callback(self, i: Inter):
        await i.response.defer(ephemeral=True)
        s = io.StringIO()

        linked = await i.client.db.wish.check_linked(self.view.user.user_id)
        wishes = await self.view.get_wishes(i.client.db.wish, linked)

        wishes_dict = [wish.to_dict() for wish in wishes]
        s.write(str(yaml.safe_dump(wishes_dict, indent=4, allow_unicode=True)))
        s.seek(0)
        await i.followup.send(
            file=discord.File(s, f"SHENHE_WISH_{uuid4()}.yaml"),  # type: ignore
            ephemeral=True,
        )


class ClearWishHistory(ui.Button):
    def __init__(self, lang: str, disabled: bool):
        super().__init__(
            label=text_map.get(680, lang),
            style=discord.ButtonStyle.red,
            row=1,
            disabled=disabled,
        )
        self.view: View

    async def callback(self, i: Inter):
        lang = self.view.lang
        embed = DefaultEmbed(description=text_map.get(689, lang)).set_author(
            name=text_map.get(688, lang), icon_url=i.user.display_avatar.url
        )

        self.view.clear_items()
        self.view.add_item(Confirm(lang))
        self.view.add_item(Cancel(lang))
        await i.response.edit_message(embed=embed, view=self.view)


class Confirm(ui.Button):
    def __init__(self, lang: str):
        super().__init__(
            label=text_map.get(388, lang),
            style=discord.ButtonStyle.red,
        )
        self.view: View

    async def callback(self, i: Inter):
        linked = await i.client.db.wish.check_linked(self.view.user.user_id)
        if linked:
            await i.client.db.wish.delete_with_uid(self.view.user.uid)
        else:
            await i.client.db.wish.delete_with_user_id(i.user.id)

        self.view.wishes = []
        embed = self.view.get_wish_import_embed(linked)
        self.view.add_components(linked)
        await i.response.edit_message(embed=embed, view=self.view)


class Cancel(ui.Button):
    def __init__(self, lang: str):
        super().__init__(
            label=text_map.get(389, lang),
            style=discord.ButtonStyle.gray,
        )
        self.view: View

    async def callback(self, i: Inter):
        linked = await i.client.db.wish.check_linked(self.view.user.user_id)
        embed = self.view.get_wish_import_embed(linked)
        self.view.add_components(linked)
        await i.response.edit_message(embed=embed, view=self.view)


class ConfirmWishimport(ui.Button):
    def __init__(
        self,
        lang: str,
        wishes: List[Union[genshin.models.Wish, WishHistory]],
    ) -> None:
        super().__init__(
            label=text_map.get(388, lang),
            style=discord.ButtonStyle.green,
        )

        self.wishes = wishes
        self.view: View

    async def callback(self, i: Inter) -> None:
        # Create a new embed with the author set to the name of the user and the bot's icon
        embed = DefaultEmbed().set_author(
            name=text_map.get(355, self.view.lang), icon_url=asset.loader
        )
        # Edit the original response to show the new embed and remove the view
        await i.response.edit_message(embed=embed, view=None)

        # Loop through each wish in the list of wishes
        for wish in self.wishes:
            # If the wish is a WishHistory object, insert it into the database
            if isinstance(wish, WishHistory):
                await i.client.db.wish.insert(wish)
            # If the wish is a genshin.models.Wish object, convert it to a WishHistory object and insert it into the database
            else:
                wish_history = WishHistory.from_genshin_wish(wish, i.user.id)
                wish_history.uid = self.view.user.uid
                await i.client.db.wish.insert(wish_history)

        # Calculate pity pulls for each banner type
        banners = (100, 200, 301, 302, 400)
        for banner in banners:
            # Fetch all wishes for the current user and banner type
            rows = await i.client.pool.fetch(
                """
                SELECT *
                FROM wish_history
                WHERE user_id = $1
                AND wish_banner_type = $2
                AND uid = $3
                ORDER BY wish_id ASC
                """,
                i.user.id,
                banner,
                self.view.user.uid,
            )
            # Convert each row to a WishHistory object
            wishes = [WishHistory(**row) for row in rows]

            # If there are no wishes, set the pity count to 1
            if not wishes:
                count = 1
            # If there are wishes, set the pity count to the last wish's pity count + 1
            else:
                if wishes[-1].pity is None:
                    count = 1
                else:
                    count = wishes[-1].pity + 1

            # Loop through each wish and update the pity count
            for wish in wishes:
                if wish.item_id is None:
                    item_id = text_map.get_id_from_name(wish.name)
                else:
                    item_id = wish.item_id
                await i.client.pool.execute(
                    """
                    UPDATE wish_history
                    SET pity_pull = $1,
                    item_id = $5
                    WHERE user_id = $2
                    AND wish_id = $3
                    AND uid = $4
                    """,
                    count,
                    i.user.id,
                    wish.wish_id,
                    self.view.user.uid,
                    item_id,
                )
                # If the wish is a 5-star, reset the pity count to 1, otherwise increment it
                count = 1 if wish.rarity == 5 else count + 1

        # Check if the user is linked to a UID
        linked = await i.client.db.wish.check_linked(self.view.user.user_id)
        # Get the user's wishes and update the view
        await self.view.get_wishes(i.client.db.wish, linked)
        embed = self.view.get_wish_import_embed(linked)
        self.view.add_components(linked)
        # Edit the original response to show the new embed and updated view
        await i.edit_original_response(embed=embed, view=self.view)


class CancelWishimport(ui.Button):
    def __init__(self, lang: str):
        super().__init__(
            label=text_map.get(389, lang),
            style=discord.ButtonStyle.gray,
        )
        self.view: View

    async def callback(self, i: Inter):
        linked = await i.client.db.wish.check_linked(self.view.user.user_id)
        embed = self.view.get_wish_import_embed(linked)
        self.view.add_components(linked)
        await i.response.edit_message(embed=embed, view=self.view)


class AuthKeyModal(BaseModal):
    url = ui.TextInput(
        label="AUTH KEY URL",
        placeholder="CTRL+V TO PASTE LINK",
        style=discord.TextStyle.long,
        required=True,
    )

    def __init__(self, lang: str):
        super().__init__(
            title=text_map.get(353, lang),
            timeout=config.mid_timeout,
            custom_id="authkey_modal",
        )
        self.url.label = text_map.get(352, lang)
        self.url.placeholder = text_map.get(354, lang)

        self.lang = lang

    async def on_submit(self, i: Inter):
        await i.response.defer()
        self.stop()
