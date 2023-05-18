import json
import random
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

import aiofiles
import asqlite
import discord
import genshin
from discord import app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands
from discord.utils import format_dt
from dotenv import load_dotenv
from enkanetwork import Assets

import apps.genshin.checks as checks
import dev.asset as asset
import dev.exceptions as exceptions
import dev.models as models
import ui
import utils.general as general
from ambr import AmbrTopAPI, Character, Material, Weapon
from apps.draw import main_funcs
from apps.genshin import enka, hoyolab, leaderboard
from apps.genshin_data import abyss
from apps.text_map import convert_locale, text_map
from data.cards.dice_element import get_dice_emoji
from utils import (disable_view_items, get_character_emoji, get_uid,
                   get_uid_region_hash, get_user_lang, get_user_theme, log)
from utils.paginators import GeneralPaginator

load_dotenv()


class GenshinCog(commands.Cog, name="genshin"):
    def __init__(self, bot):
        self.bot: models.BotModel = bot
        self.genshin_app = hoyolab.GenshinApp(self.bot)
        self.debug = self.bot.debug

        # Right click commands
        self.search_uid_context_menu = app_commands.ContextMenu(
            name=_("UID"), callback=self.search_uid_ctx_menu
        )
        self.profile_context_menu = app_commands.ContextMenu(
            name=_("Profile", hash=498), callback=self.profile_ctx_menu
        )
        self.characters_context_menu = app_commands.ContextMenu(
            name=_("Characters", hash=499), callback=self.characters_ctx_menu
        )
        self.stats_context_menu = app_commands.ContextMenu(
            name=_("Stats", hash=56), callback=self.stats_ctx_menu
        )
        self.check_context_menu = app_commands.ContextMenu(
            name=_("Realtime notes", hash=24), callback=self.check_ctx_menu
        )
        self.bot.tree.add_command(self.search_uid_context_menu)
        self.bot.tree.add_command(self.profile_context_menu)
        self.bot.tree.add_command(self.characters_context_menu)
        self.bot.tree.add_command(self.stats_context_menu)
        self.bot.tree.add_command(self.check_context_menu)

    async def cog_load(self) -> None:
        cookie_list: List[Dict[str, str]] = []
        self.bot.genshin_client = genshin.Client()
        self.bot.genshin_client.region = genshin.Region.OVERSEAS

        rows = await self.bot.pool.fetch(
            """
            SELECT ltuid, ltoken, uid
            FROM user_accounts
            WHERE ltoken IS NOT NULL
            AND ltuid IS NOT NULL
            AND uid IS NOT NULL
            AND china = false
            """
        )
        for row in rows:
            if str(row["uid"])[0] in ("1", "2", "5"):
                continue

            ltuid = row["ltuid"]
            ltoken = row["ltoken"]
            cookie: Dict[str, Any] = {"ltuid": ltuid, "ltoken": ltoken}

            for c in cookie_list:
                if c["ltuid"] == ltuid:
                    break
            else:
                cookie_list.append(cookie)

        if cookie_list:
            try:
                self.bot.genshin_client.set_cookies(cookie_list)
            except Exception as e:  # skipcq: PYL-W0703
                log.warning(f"[Genshin Client][Error]: {e}", exc_info=e)
            else:
                log.info(f"[Genshin Client]: {len(cookie_list)} cookies loaded")

        async with self.bot.session.get(
            "https://genshin-db-api.vercel.app/api/languages"
        ) as r:
            languages = await r.json()

        self.card_data: Dict[str, List[Dict[str, Any]]] = {}
        for lang in languages:
            try:
                async with aiofiles.open(f"data/cards/card_data_{lang}.json", "r") as f:
                    self.card_data[lang] = json.loads(await f.read())
            except FileNotFoundError:
                self.card_data[lang] = []

        maps_to_open = (
            "avatar",
            "weapon",
            "material",
            "reliquary",
            "monster",
            "food",
            "furniture",
            "namecard",
            "book",
        )
        self.text_map_files: List[Dict[str, Any]] = []
        for map_ in maps_to_open:
            try:
                async with aiofiles.open(
                    f"text_maps/{map_}.json", "r", encoding="utf-8"
                ) as f:
                    data = json.loads(await f.read())
            except FileNotFoundError:
                data = {}
            self.text_map_files.append(data)
        try:
            async with aiofiles.open(
                "text_maps/item_name.json", "r", encoding="utf-8"
            ) as f:
                self.item_names = json.loads(await f.read())
        except FileNotFoundError:
            self.item_names = {}

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.search_uid_context_menu.name, type=self.search_uid_context_menu.type
        )
        self.bot.tree.remove_command(
            self.profile_context_menu.name, type=self.profile_context_menu.type
        )
        self.bot.tree.remove_command(
            self.characters_context_menu.name, type=self.characters_context_menu.type
        )
        self.bot.tree.remove_command(
            self.stats_context_menu.name, type=self.stats_context_menu.type
        )
        self.bot.tree.remove_command(
            self.check_context_menu.name, type=self.check_context_menu.type
        )

    @app_commands.command(
        name="register",
        description=_(
            "Register your genshin account in shenhe's database to use commands that require one",
            hash=410,
        ),
    )
    async def slash_register(self, inter: discord.Interaction):
        i: models.Inter = inter  # type: ignore
        await i.response.defer(ephemeral=True)
        await ui.manage_accounts.return_accounts(i)

    @checks.check_cookie()
    @app_commands.command(
        name="check",
        description=_("Check resin, pot, and expedition status", hash=414),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("Check other user's data", hash=416))
    async def slash_check(
        self,
        i: discord.Interaction,
        member: Optional[discord.User | discord.Member] = None,
    ):
        await self.check_command(i, member or i.user)

    async def check_ctx_menu(self, i: discord.Interaction, member: discord.User):
        await checks.check_cookie_predicate(i, member)
        await self.check_command(i, member, ephemeral=True)

    async def check_command(
        self,
        i: discord.Interaction,
        member: Optional[discord.User | discord.Member] = None,
        ephemeral: bool = False,
    ):
        await i.response.defer(ephemeral=ephemeral)
        member = member or i.user

        r = await self.genshin_app.get_real_time_notes(member.id, i.user.id, i.locale)
        if isinstance(r.result, models.ErrorEmbed):
            return await i.followup.send(embed=r.result, ephemeral=True)

        result = r.result
        await i.followup.send(
            embed=result.embed.set_image(url="https://i.imgur.com/cBykL8X.gif"),
            ephemeral=ephemeral,
        )

        fp = await main_funcs.draw_realtime_card(
            result.draw_input,
            result.notes,
        )
        fp.seek(0)
        await i.edit_original_response(
            embed=result.embed.set_image(url="attachment://realtime_notes.jpeg"),
            attachments=[discord.File(fp, filename="realtime_notes.jpeg")],
        )

    @checks.check_account()
    @app_commands.command(
        name="stats",
        description=_(
            "View your genshin stats: Active days, oculi number, and number of chests obtained",
            hash=417,
        ),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(
        member=_("Check other user's data", hash=416),
    )
    async def stats(
        self,
        i: discord.Interaction,
        member: Optional[discord.User | discord.Member] = None,
    ):
        await self.stats_command(i, member)

    async def stats_ctx_menu(self, i: discord.Interaction, member: discord.User):
        await checks.check_account_predicate(i, member)
        await self.stats_command(i, member, context_command=True)

    async def stats_command(
        self,
        i: discord.Interaction,
        member: Optional[discord.User | discord.Member] = None,
        context_command: bool = False,
    ) -> None:
        await i.response.defer()
        member = member or i.user

        uid = await get_uid(member.id, self.bot.pool)
        if uid is None:
            raise exceptions.UIDNotFound

        enka_info = await enka.get_enka_info(uid, self.bot.session)
        namecard_id = enka_info.player_info.name_card_id
        assets = Assets()
        namecard = assets.namecards(namecard_id)
        if namecard is None:
            raise AssertionError("Namecard not found")

        r = await self.genshin_app.get_stats(
            member.id, i.user.id, namecard, member.display_avatar, i.locale
        )
        if isinstance(r.result, models.ErrorEmbed):
            return await i.followup.send(embed=r.result, ephemeral=True)

        result = r.result
        fp = result.file
        fp.seek(0)
        _file = discord.File(fp, "stat_card.jpeg")
        await i.followup.send(
            embed=result.embed,
            ephemeral=context_command,
            files=[_file],
        )

    @checks.check_cookie()
    @app_commands.command(
        name="area",
        description=_("View exploration rates of different areas in genshin", hash=419),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(
        member=_("Check other user's data", hash=416),
    )
    async def area(
        self,
        i: discord.Interaction,
        member: Optional[discord.User | discord.Member] = None,
    ):
        await i.response.defer()
        member = member or i.user

        r = await self.genshin_app.get_area(member.id, i.user.id, i.locale)
        if isinstance(r.result, models.ErrorEmbed):
            return await i.followup.send(embed=r.result)

        result = r.result
        fp = result.file
        fp.seek(0)
        image = discord.File(fp, "area.jpeg")
        await i.followup.send(embed=result.embed, files=[image])

    @checks.check_cookie()
    @app_commands.command(
        name="claim",
        description=_(
            "View info about your Hoyolab daily check-in rewards",
            hash=420,
        ),
    )
    async def claim(self, inter: discord.Interaction):
        i: models.Inter = inter  # type: ignore
        view = ui.daily_checkin.View()
        await view.start(i)

    @checks.check_cookie()
    @app_commands.command(
        name="characters",
        description=_(
            "View all owned characters (need /register)",
            hash=421,
        ),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("Check other user's data", hash=416))
    async def characters(
        self,
        i: discord.Interaction,
        member: Optional[discord.User | discord.Member] = None,
    ):
        await self.characters_comamnd(i, member, False)

    async def characters_ctx_menu(self, i: discord.Interaction, member: discord.User):
        await checks.check_cookie_predicate(i, member)
        await self.characters_comamnd(i, member)

    async def characters_comamnd(
        self,
        inter: discord.Interaction,
        member: Optional[discord.User | discord.Member] = None,
        ephemeral: bool = True,
    ):
        i: models.Inter = inter  # type: ignore
        member = member or i.user
        user_locale = await get_user_lang(i.user.id, self.bot.pool)
        locale = user_locale or i.locale
        await i.response.send_message(
            embed=models.DefaultEmbed().set_author(
                name=text_map.get(765, locale), icon_url=asset.loader
            ),
            ephemeral=ephemeral,
        )

        r = await self.genshin_app.get_all_characters(member.id, i.user.id, i.locale)
        if isinstance(r.result, models.ErrorEmbed):
            return await i.followup.send(embed=r.result, ephemeral=ephemeral)

        result = r.result
        client = AmbrTopAPI(self.bot.session)
        characters = await client.get_character(
            include_beta=False, include_traveler=False
        )
        if not isinstance(characters, list):
            raise TypeError("Characters is not a list")
        view = ui.show_all_characters.View(
            locale, result.characters, member, characters
        )
        await view.start(i)

    @checks.check_cookie()
    @app_commands.command(
        name="diary",
        description=_(
            "View your traveler's diary: primo and mora income (needs /register)",
            hash=422,
        ),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(
        member=_("Check other user's data", hash=416),
    )
    async def diary(
        self,
        i: discord.Interaction,
        member: Optional[discord.User | discord.Member] = None,
    ):
        member = member or i.user
        await i.response.defer()
        user_locale = await get_user_lang(i.user.id, self.bot.pool)
        r = await self.genshin_app.get_diary(member.id, i.user.id, i.locale)
        if isinstance(r.result, models.ErrorEmbed):
            return await i.followup.send(embed=r.result)
        result = r.result
        view = ui.diary_view.View(
            i.user, member, self.genshin_app, user_locale or i.locale
        )
        fp = result.file
        fp.seek(0)
        await i.followup.send(
            embed=result.embed,
            view=view,
            files=[discord.File(fp, "diary.jpeg")],
        )
        view.message = await i.original_response()

    @checks.check_cookie()
    @app_commands.command(
        name="abyss",
        description=_("View abyss information", hash=428),
    )
    @app_commands.rename(
        previous=_("season", hash=430),
        member=_("user", hash=415),
    )
    @app_commands.describe(
        previous=_("Which abyss season?", hash=432),
        member=_("Check other user's data", hash=416),
    )
    @app_commands.choices(
        previous=[
            app_commands.Choice(name=_("Current season", hash=435), value=0),
            app_commands.Choice(name=_("Last season", hash=436), value=1),
        ],
    )
    async def abyss(
        self,
        i: discord.Interaction,
        previous: int = 0,
        member: Optional[discord.User | discord.Member] = None,
    ):
        member = member or i.user
        await i.response.defer()
        user_locale = await get_user_lang(i.user.id, self.bot.pool)
        result = await self.genshin_app.get_abyss(
            member.id, i.user.id, previous == 1, i.locale
        )
        if isinstance(result.result, models.ErrorEmbed):
            return await i.followup.send(embed=result.result)

        abyss_result = result.result
        view = ui.abyss_view.View(i.user, abyss_result, user_locale or i.locale)
        fp = abyss_result.overview_file
        fp.seek(0)
        image = discord.File(fp, "overview_card.jpeg")
        await i.followup.send(
            embed=abyss_result.overview_embed, view=view, files=[image]
        )
        view.message = await i.original_response()
        await leaderboard.update_user_abyss_leaderboard(
            abyss_result.abyss,
            abyss_result.genshin_user,
            abyss_result.characters,
            abyss_result.uid,
            abyss_result.genshin_user.info.nickname,
            i.user.id,
            previous,
            self.bot.pool,
        )

    @app_commands.command(name="stuck", description=_("Data not public?", hash=149))
    async def stuck(self, i: discord.Interaction):
        user_locale = await get_user_lang(i.user.id, self.bot.pool)
        embed = models.DefaultEmbed(
            text_map.get(149, i.locale, user_locale),
            text_map.get(150, i.locale, user_locale),
        )
        embed.set_image(url="https://i.imgur.com/w6Q7WwJ.gif")
        await i.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="remind", description=_("Set reminders", hash=438))
    async def remind(self, inter: discord.Interaction):
        i: models.Inter = inter # type: ignore
        view = ui.reminder_menu.View()
        await view.start(i)

    @app_commands.command(
        name="farm", description=_("View today's farmable items", hash=446)
    )
    async def farm(self, i: discord.Interaction):
        await ui.domain_view.return_farm_interaction(i)

    @app_commands.command(
        name="build",
        description=_(
            "View character builds: Talent levels, artifacts, weapons", hash=447
        ),
    )
    async def build(self, i: discord.Interaction):
        view = ui.build_view.View()
        view.author = i.user
        await i.response.send_message(view=view)
        view.message = await i.original_response()

    @app_commands.command(
        name="uid",
        description=_(
            "Search a user's genshin UID (if they are registered in shenhe)", hash=448
        ),
    )
    @app_commands.rename(player=_("user", hash=415))
    async def search_uid(self, i: discord.Interaction, player: discord.User):
        await self.search_uid_command(i, player, False)

    async def search_uid_ctx_menu(self, i: discord.Interaction, player: discord.User):
        await self.search_uid_command(i, player)

    async def search_uid_command(
        self, i: discord.Interaction, player: discord.User, ephemeral: bool = True
    ):
        locale = await get_user_lang(i.user.id, self.bot.pool) or i.locale
        uid = await get_uid(player.id, self.bot.pool)
        try:
            if uid is None:
                if i.guild is not None and i.guild.id == 916838066117824553:
                    async with asqlite.connect("../shenhe_main/main.db") as db:
                        async with db.execute(
                            "SELECT uid FROM genshin_accounts WHERE user_id = ?",
                            (player.id,),
                        ) as c:
                            uid = await c.fetchone()
                        if uid is None:
                            raise exceptions.UIDNotFound
                        uid = uid[0]
                else:
                    raise exceptions.UIDNotFound
        except exceptions.UIDNotFound:
            return await i.response.send_message(
                embed=models.ErrorEmbed(
                    description=text_map.get(165, locale)
                ).set_author(
                    name=text_map.get(166, locale),
                    icon_url=player.avatar,
                ),
                ephemeral=True,
            )

        embed = models.DefaultEmbed()
        embed.add_field(
            name=f"{text_map.get(167, locale).format(name=player.display_name)}",
            value=str(uid),
            inline=False,
        )
        embed.add_field(
            name=text_map.get(727, locale),
            value=text_map.get(get_uid_region_hash(uid), locale),
            inline=False,
        )
        embed.set_thumbnail(url=player.display_avatar.url)

        view = ui.uid_command.View(locale, uid)
        await i.response.send_message(embed=embed, ephemeral=ephemeral, view=view)
        view.message = await i.original_response()

    @app_commands.command(
        name="profile",
        description=_(
            "View your genshin profile: Character stats, artifacts, and perform damage calculations",
            hash=449,
        ),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(
        member=_("Check other user's data", hash=416),
    )
    async def profile(
        self,
        i: discord.Interaction,
        member: Optional[discord.User | discord.Member] = None,
        uid: Optional[int] = None,
    ):
        await self.profile_command(i, member, False, uid)

    async def profile_ctx_menu(self, i: discord.Interaction, member: discord.User):
        await checks.check_account_predicate(i, member)
        await self.profile_command(i, member)

    async def profile_command(
        self,
        i: discord.Interaction,
        member: Optional[discord.User | discord.Member] = None,
        ephemeral: bool = True,
        custom_uid: Optional[int] = None,
    ):
        await i.response.defer(ephemeral=ephemeral)
        member = member or i.user

        uid = custom_uid or await get_uid(member.id, self.bot.pool)
        if uid is None:
            raise exceptions.UIDNotFound
        locale = await get_user_lang(i.user.id, self.bot.pool) or i.locale

        data, en_data, card_data = await enka.get_enka_data(
            uid, convert_locale.to_enka(locale), self.bot.pool
        )

        embeds = [
            models.DefaultEmbed()
            .set_author(
                name=text_map.get(644, locale),
                icon_url=asset.loader,
            )
            .set_image(url="https://i.imgur.com/3U1bJ0Z.gif"),
            models.DefaultEmbed()
            .set_author(
                name=text_map.get(644, locale),
                icon_url=asset.loader,
            )
            .set_image(url="https://i.imgur.com/25pdyUG.gif"),
        ]

        options: List[discord.SelectOption] = []
        non_cache_ids: List[int] = []
        if card_data and card_data.characters:
            non_cache_ids = [c.id for c in card_data.characters]

        for c in data.characters:
            if c.id not in non_cache_ids:
                description = text_map.get(543, locale)
            else:
                description = None
            label = f"{c.name} | Lv.{c.level} | C{c.constellations_unlocked}R{c.equipments[-1].refinement}"
            options.append(
                discord.SelectOption(
                    label=label,
                    description=description,
                    value=str(c.id),
                    emoji=get_character_emoji(str(c.id)),
                )
            )

        view = ui.enka_profile.View([], locale)
        disable_view_items(view)

        await i.edit_original_response(
            embeds=embeds,
            attachments=[],
            view=view,
        )

        in_x_seconds = format_dt(
            general.get_dt_now() + timedelta(seconds=data.ttl), "R"
        )
        embed = models.DefaultEmbed(
            text_map.get(144, locale),
            f"""
            {asset.link_emoji} [{text_map.get(588, locale)}](https://enka.cc/u/{uid})
            {asset.time_emoji} {text_map.get(589, locale).format(in_x_seconds=in_x_seconds)}
            """,
        )
        embed.set_image(url="attachment://profile.jpeg")
        embed_two = models.DefaultEmbed(text_map.get(145, locale))
        embed_two.set_image(url="attachment://character.jpeg")
        embed_two.set_footer(text=text_map.get(511, locale))

        dark_mode = await get_user_theme(i.user.id, self.bot.pool)
        fp, fp_two = await main_funcs.draw_profile_overview_card(
            models.DrawInput(
                loop=self.bot.loop,
                session=self.bot.session,
                locale=locale,
                dark_mode=dark_mode,
            ),
            card_data or data,
        )
        fp.seek(0)
        fp_two.seek(0)

        view = ui.enka_profile.View(options, locale)
        view.overview_embeds = [embed, embed_two]
        view.overview_fps = [fp, fp_two]
        view.data = data
        view.en_data = en_data
        view.card_data = card_data
        view.member = member
        view.author = i.user
        view.locale = locale

        file_one = discord.File(fp, filename="profile.jpeg")
        file_two = discord.File(fp_two, filename="character.jpeg")
        await i.edit_original_response(
            embeds=[embed, embed_two],
            view=view,
            attachments=[file_one, file_two],
        )
        view.message = await i.original_response()

    @checks.check_cookie()
    @app_commands.command(name="redeem", description=_("Redeem a gift code", hash=450))
    async def redeem(self, inter: discord.Interaction):
        i: models.Inter = inter  # type: ignore
        view = ui.redeem.View()
        await view.start(i)

    @app_commands.command(
        name="events", description=_("View ongoing genshin events", hash=452)
    )
    async def events(self, inter: discord.Interaction):
        i: models.Inter = inter  # type: ignore
        await ui.event_type_chooser.return_events(i)

    @checks.check_account()
    @app_commands.command(
        name="leaderboard", description=_("The Shenhe leaderboard", hash=252)
    )
    async def leaderboard(self, inter: discord.Interaction):
        i: models.Inter = inter  # type: ignore
        view = ui.leaderboard_view.View()
        await view.start(i)

    @app_commands.command(
        name="search", description=_("Search anything related to genshin", hash=508)
    )
    @app_commands.rename(query=_("query", hash=509))
    async def search(self, inter: discord.Interaction, query: str):
        i: models.Inter = inter  # type: ignore

        if not query.isdigit():
            raise exceptions.AutocompleteError

        await i.response.defer()

        user_locale = await get_user_lang(i.user.id, self.bot.pool)
        locale = user_locale or i.locale
        ambr_top_locale = convert_locale.to_ambr_top(locale)
        dark_mode = await get_user_theme(i.user.id, self.bot.pool)
        client = AmbrTopAPI(self.bot.session, ambr_top_locale)

        item_type = None
        for index, file in enumerate(self.text_map_files):
            if query in file:
                item_type = index
                break
        if item_type is None:
            raise exceptions.ItemNotFound

        if item_type == 0:  # character
            character = await client.get_character_detail(query)
            if character is None:
                raise exceptions.ItemNotFound
            await ui.search_nav.parse_character_wiki(
                character, i, locale, client, dark_mode
            )

        elif item_type == 1:  # weapon
            weapon = await client.get_weapon_detail(int(query))
            if weapon is None:
                raise exceptions.ItemNotFound
            await ui.search_nav.parse_weapon_wiki(weapon, i, locale, client, dark_mode)

        elif item_type == 2:  # material
            material = await client.get_material_detail(int(query))
            if material is None:
                raise exceptions.ItemNotFound
            await ui.search_nav.parse_material_wiki(
                material, i, locale, client, dark_mode
            )

        elif item_type == 3:  # artifact
            artifact = await client.get_artifact_detail(int(query))
            if artifact is None:
                raise exceptions.ItemNotFound
            await ui.search_nav.parse_artifact_wiki(artifact, i, locale)

        elif item_type == 4:  # monster
            monster = await client.get_monster_detail(int(query))
            if monster is None:
                raise exceptions.ItemNotFound
            await ui.search_nav.parse_monster_wiki(
                monster, i, locale, client, dark_mode
            )

        elif item_type == 5:  # food
            food = await client.get_food_detail(int(query))
            if food is None:
                raise exceptions.ItemNotFound
            await ui.search_nav.parse_food_wiki(food, i, locale, client, dark_mode)

        elif item_type == 6:  # furniture
            furniture = await client.get_furniture_detail(int(query))
            if furniture is None:
                raise exceptions.ItemNotFound
            await ui.search_nav.parse_furniture_wiki(
                furniture, i, locale, client, dark_mode
            )

        elif item_type == 7:  # namecard
            namecard = await client.get_name_card_detail(int(query))
            if namecard is None:
                raise exceptions.ItemNotFound
            await ui.search_nav.parse_namecard_wiki(namecard, i, locale)

        elif item_type == 8:  # book
            book = await client.get_book_detail(int(query))
            if book is None:
                raise exceptions.ItemNotFound
            await ui.search_nav.parse_book_wiki(book, i, locale, client)

    @search.autocomplete("query")
    async def query_autocomplete(
        self, i: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        user_locale = await get_user_lang(i.user.id, self.bot.pool)
        ambr_top_locale = convert_locale.to_ambr_top(user_locale or i.locale)
        result: List[app_commands.Choice] = []
        for queries in self.text_map_files:
            for item_id, query_names in queries.items():
                if item_id in ("10000005", "10000007"):
                    continue

                item_name = query_names[ambr_top_locale]
                if current.lower() in item_name.lower() and item_name:
                    result.append(app_commands.Choice(name=item_name, value=item_id))
                elif " " in current:
                    splited = current.split(" ")
                    all_match = True
                    for word in splited:
                        if word.lower() not in item_name.lower():
                            all_match = False
                            break
                    if all_match and item_name != "":
                        result.append(
                            app_commands.Choice(name=item_name, value=item_id)
                        )
        if not current:
            random.shuffle(result)
        return result[:25]

    @checks.check_account()
    @app_commands.command(
        name="activity",
        description=_("View your past genshin activity stats", hash=459),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(
        member=_("Check other user's data", hash=416),
    )
    async def activity(
        self,
        inter: discord.Interaction,
        member: Optional[discord.User | discord.Member] = None,
    ):
        i: models.Inter = inter  # type: ignore
        await i.response.defer()
        member = member or i.user

        r = await self.genshin_app.get_activities(member.id, i.user.id, i.locale)
        if isinstance(r.result, models.ErrorEmbed):
            return await i.followup.send(embed=r.result, ephemeral=True)

        await GeneralPaginator(i, r.result).start(followup=True)

    @app_commands.command(
        name="beta",
        description=_("View the list of current beta items in Genshin", hash=434),
    )
    async def view_beta_items(self, i: discord.Interaction):
        user_locale = await get_user_lang(i.user.id, self.bot.pool)
        client = AmbrTopAPI(
            self.bot.session, convert_locale.to_ambr_top(user_locale or i.locale)
        )
        result = ""
        first_icon_url = ""
        characters = await client.get_character()
        weapons = await client.get_weapon()
        materials = await client.get_material()
        things = [characters, weapons, materials]
        for thing in things:
            result, first_icon_url = self.get_beta_items(result, thing, first_icon_url)
        if result == "":
            result = text_map.get(445, i.locale, user_locale)
        embed = models.DefaultEmbed(text_map.get(437, i.locale, user_locale), result)
        if first_icon_url != "":
            embed.set_thumbnail(url=first_icon_url)
        embed.set_footer(text=text_map.get(444, i.locale, user_locale))
        await i.response.send_message(embed=embed)

    @staticmethod
    def get_beta_items(
        result: str,
        items: List[Character | Weapon | Material],
        first_icon_url: str,
    ) -> Tuple[str, str]:
        for item in items:
            if item.beta:
                if item.name == "？？？":
                    continue
                result += f"• {item.name}\n"
                if first_icon_url == "":
                    first_icon_url = item.icon
        return result, first_icon_url

    @app_commands.command(
        name="banners", description=_("View ongoing Genshin banners", hash=375)
    )
    async def banners(self, i: discord.Interaction):
        await i.response.defer()

        locale = await get_user_lang(i.user.id, self.bot.pool) or i.locale
        lang = convert_locale.to_genshin_py(locale)
        client = genshin.Client()

        zh_tw_annoucements = await client.get_genshin_announcements(lang="zh-tw")
        annoucements = await client.get_genshin_announcements(lang=lang)
        now = general.get_dt_now(True)
        banner_ids = [
            a.id for a in zh_tw_annoucements if "祈願" in a.title and a.end_time > now
        ]
        banners = [a for a in annoucements if a.id in banner_ids]
        banners.sort(key=lambda x: x.end_time)
        if not banners:
            return await i.followup.send(
                embed=models.DefaultEmbed(
                    description=text_map.get(376, locale)
                ).set_author(name=text_map.get(23, locale))
            )

        fp = await main_funcs.draw_banner_card(
            models.DrawInput(
                loop=self.bot.loop, session=self.bot.session, locale=locale
            ),
            [w.banner for w in banners],
        )
        fp.seek(0)

        await i.followup.send(
            embed=models.DefaultEmbed(
                text_map.get(746, locale),
                text_map.get(381, locale).format(
                    time=format_dt(
                        banners[0].end_time,
                        "R",
                    )
                ),
            ).set_image(url="attachment://banner.jpeg"),
            file=discord.File(fp, "banner.jpeg"),
        )

    @app_commands.command(
        name="abyss-enemies",
        description=_("View the list of enemies in the current abyss phases", hash=294),
    )
    async def abyss_enemies(self, i: discord.Interaction):
        await i.response.defer()
        locale = await get_user_lang(i.user.id, self.bot.pool) or i.locale
        floors = await abyss.get_abyss_enemies(self.bot.gd_text_map, locale)

        ley_line_disorders = await abyss.get_ley_line_disorders(
            self.bot.gd_text_map, locale
        )

        embeds: Dict[str, discord.Embed] = {}
        enemies: Dict[str, List[models.AbyssHalf]] = {}
        for floor in floors:
            for chamber in floor.chambers:
                embed = models.DefaultEmbed(
                    f"{text_map.get(146, locale).format(a=floor.num)} - {text_map.get(177, locale).format(a=chamber.num)}"
                )
                embed.add_field(
                    name=text_map.get(706, locale),
                    value=general.add_bullet_points(
                        ley_line_disorders.get(floor.num, [])
                    ),
                    inline=False,
                )
                embed.add_field(
                    name=text_map.get(295, locale),
                    value=chamber.enemy_level,
                    inline=False,
                )
                embed.set_image(url="attachment://enemies.jpeg")
                embeds[f"{floor.num}-{chamber.num}"] = embed
                enemies[f"{floor.num}-{chamber.num}"] = chamber.halfs

        embed = models.DefaultEmbed()
        embed.set_image(url=asset.abyss_image)
        embed.set_author(
            name=f"{text_map.get(705, locale)}",
            icon_url=i.user.display_avatar.url,
        )

        buff_name, buff_desc = await abyss.get_abyss_blessing(
            self.bot.gd_text_map, locale
        )
        buff_embed = models.DefaultEmbed(text_map.get(733, locale))
        buff_embed.add_field(
            name=buff_name,
            value=buff_desc,
        )

        view = ui.abyss_enemy.View(locale, enemies, embeds, buff_embed)
        view.author = i.user
        await i.followup.send(embed=embed, view=view)
        view.message = await i.original_response()

    @app_commands.command(
        name="lineup",
        description=_(
            "Search Genshin lineups with Hoyolab's lineup simulator", hash=38
        ),
    )
    async def slash_lineup(self, inter: discord.Interaction):
        i: models.Inter = inter  # type: ignore
        locale = await get_user_lang(i.user.id, self.bot.pool) or i.locale

        client = self.bot.genshin_client
        client.lang = convert_locale.to_genshin_py(locale)
        scenarios = await client.get_lineup_scenarios()

        scenarios_to_search = [
            scenarios.abyss.spire,
            scenarios.abyss.corridor,
            scenarios.world.battles,
            scenarios.world.domain_challenges,
            scenarios.world.trounce_domains,
        ]
        options = []
        scenario_dict = {}
        for scenario in scenarios_to_search:
            options.append(
                discord.SelectOption(label=scenario.name, value=str(scenario.id))
            )
            scenario_dict[str(scenario.id)] = scenario

        ambr = AmbrTopAPI(self.bot.session, convert_locale.to_ambr_top(locale))
        characters = await ambr.get_character(include_beta=False)

        if isinstance(characters, List):
            view = ui.lineup_view.View(locale, options, scenario_dict, characters)
            view.author = i.user
            await ui.lineup_view.search_lineup(i, view)
            view.message = await i.original_response()

    @app_commands.command(
        name="tcg", description=_("Search a card in the Genshin TCG", hash=717)
    )
    @app_commands.rename(card_id=_("card", hash=718))
    async def slash_tcg(self, i: discord.Interaction, card_id: str):
        if not card_id.isdigit():
            raise exceptions.AutocompleteError

        locale = await get_user_lang(i.user.id, self.bot.pool) or i.locale
        genshin_db_locale = convert_locale.to_genshin_db(locale)

        the_card = None
        card_type = None

        for card in self.card_data[genshin_db_locale]:
            if card["id"] == int(card_id):
                the_card = card
                card_type = card["cardType"]
                break

        if the_card is None:
            raise exceptions.CardNotFound

        card = the_card

        if card_type == "tcgcharactercards":
            embed = models.DefaultEmbed(card["name"])
            embed.set_author(name=card["storytitle"])
            embed.set_footer(text=card["source"])
            embed.set_image(
                url=f"https://res.cloudinary.com/genshin/image/upload/sprites/{card['images']['filename_cardface_HD']}.png"
            )

            for skill in card["skills"]:
                cost_str = f"**{text_map.get(710, locale)}: **"
                cost_str += " / ".join(
                    [
                        f"{get_dice_emoji(cost['costtype'])} ({cost['count']})"
                        for cost in skill["playcost"]
                    ]
                )
                embed.add_field(
                    name=skill["name"],
                    value=general.parse_html(skill["description"]) + "\n" + cost_str,
                    inline=False,
                )
        elif card_type == "tcgactioncards":
            embed = models.DefaultEmbed(
                card["name"],
                card["description"],
            )
            embed.set_author(name=card["cardtypetext"])
            if "storytext" in card:
                embed.set_footer(text=card["storytext"])
            embed.set_image(
                url=f"https://res.cloudinary.com/genshin/image/upload/sprites/{card['images']['filename_cardface_HD']}.png"
            )

            if card["playcost"]:
                cost_str = " / ".join(
                    [
                        f"{get_dice_emoji(cost['costtype'])} ({cost['count']})"
                        for cost in card["playcost"]
                    ]
                )
                embed.add_field(name=text_map.get(710, locale), value=cost_str)
        elif card_type == "tcgcardbacks":
            embed = models.DefaultEmbed(card["name"], card["description"])
            embed.set_footer(text=card["source"])
            embed.set_image(
                url=f"https://res.cloudinary.com/genshin/image/upload/sprites/{card['images']['filename_icon_HD']}.png"
            )
        elif card_type == "tcgcardboxes":
            embed = models.DefaultEmbed(card["name"], card["description"])
            embed.set_footer(text=card["source"])
            embed.set_image(
                url=f"https://res.cloudinary.com/genshin/image/upload/sprites/{card['images']['filename_bg']}.png"
            )
        elif card_type == "tcgstatuseffects":
            embed = models.DefaultEmbed(card["name"], card["description"])
            embed.set_author(name=card["statustypetext"])
        else:  # card_type == "tcgsummons"
            embed = models.DefaultEmbed(card["name"], card["description"])
            embed.set_author(name=card["cardtypetext"])
            embed.set_image(
                url=f"https://res.cloudinary.com/genshin/image/upload/sprites/{card['images']['filename_cardface_HD']}.png"
            )

        await i.response.send_message(embed=embed)

    @slash_tcg.autocomplete("card_id")
    async def card_autocomplete(
        self, i: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        locale = await get_user_lang(i.user.id, self.bot.pool) or i.locale
        genshin_db_locale = convert_locale.to_genshin_db(locale)

        choices: List[app_commands.Choice] = []

        cards = self.card_data[genshin_db_locale]
        for card in cards:
            if current.lower() in card["name"].lower():
                choices.append(
                    app_commands.Choice(name=card["name"], value=str(card["id"]))
                )

        if not current:
            choices = random.choices(choices, k=25)

        return choices[:25]


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(GenshinCog(bot))
