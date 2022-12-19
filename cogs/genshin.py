import json
import random
from datetime import datetime, timedelta
from typing import List, Tuple
from data.cards.dice_element import get_dice_element

from discord import File, Interaction, Member, SelectOption, User, app_commands
from discord.app_commands import Choice
from discord.app_commands import locale_str as _
from discord.ext import commands
from discord.ui import Button, Select
from discord.utils import format_dt
from dotenv import load_dotenv

import asset
from ambr.client import AmbrTopAPI
from ambr.models import Character, Event, Material, Weapon
from apps.draw import main_funcs
from apps.genshin.abyss import get_abyss_enemies
from apps.genshin.checks import *
from apps.genshin.custom_model import (
    AbyssResult,
    AreaResult,
    CharacterResult,
    DiaryResult,
    DrawInput,
    RealtimeNoteResult,
    ShenheBot,
    StatsResult,
)
from apps.genshin.genshin_app import GenshinApp
from apps.genshin.leaderboard import update_user_abyss_leaderboard
from apps.genshin.utils import (
    get_character_emoji,
    get_current_abyss_season,
    get_enka_data,
    get_farm_data,
    get_uid,
    get_uid_tz,
)
from apps.genshin.wiki import (
    parse_artifact_wiki,
    parse_book_wiki,
    parse_character_wiki,
    parse_food_wiki,
    parse_furniture_wiki,
    parse_material_wiki,
    parse_monster_wiki,
    parse_namecard_wiki,
    parse_weapon_wiki,
)
from apps.text_map.convert_locale import to_ambr_top, to_event_lang, to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_element_name, get_user_locale
from exceptions import ItemNotFound, NoPlayerFound, UIDNotFound
from UI_elements.genshin import (
    Abyss,
    AbyssEnemy,
    Build,
    Diary,
    EnkaProfile,
    EventTypeChooser,
    Leaderboard,
    Lineup,
    ShowAllCharacters,
)
from UI_elements.genshin.DailyReward import return_claim_reward
from UI_elements.genshin.ReminderMenu import return_notification_menu
from UI_elements.others import ManageAccounts
from utility.domain_paginator import DomainPaginator
from utility.paginator import GeneralPaginator, _view
from utility.utils import (
    add_bullet_points,
    default_embed,
    divide_chunks,
    error_embed,
    get_dt_now,
    get_user_appearance_mode,
    parse_HTML,
)

load_dotenv()


class GenshinCog(commands.Cog, name="genshin"):
    def __init__(self, bot):
        self.bot: ShenheBot = bot
        self.genshin_app = GenshinApp(self.bot.db, self.bot)
        self.debug = self.bot.debug
        maps_to_open = [
            "avatar",
            "weapon",
            "material",
            "reliquary",
            "monster",
            "food",
            "furniture",
            "namecard",
            "book",
        ]
        self.text_map_files = []
        for m in maps_to_open:
            try:
                with open(f"text_maps/{m}.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
            except FileNotFoundError:
                data = {}
            self.text_map_files.append(data)
        try:
            with open(f"text_maps/item_name.json", "r", encoding="utf-8") as f:
                self.item_names = json.load(f)
        except FileNotFoundError:
            self.item_names = {}

        try:
            with open("data/cards/cards_en-us.json") as f:
                self.card_en_us = json.load(f)
        except FileNotFoundError:
            self.card_en_us = {}

        try:
            with open("data/cards/cards_i18n.json") as f:
                self.card_i18n = json.load(f)
        except FileNotFoundError:
            self.card_i18n = {}

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
    async def slash_register(self, i: Interaction):
        await i.response.defer(ephemeral=True)
        await ManageAccounts.return_accounts(i)

    @check_cookie()
    @app_commands.command(
        name="check",
        description=_("Check resin, pot, and expedition status", hash=414),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("Check other user's data", hash=416))
    async def slash_check(self, i: Interaction, member: Optional[User | Member] = None):
        await self.check_command(i, member or i.user)

    async def check_ctx_menu(self, i: Interaction, member: User):
        check = await check_account_predicate(i, member)
        if not check:
            return
        await self.check_command(i, member, ephemeral=True)

    async def check_command(
        self,
        i: Interaction,
        member: Optional[User | Member] = None,
        ephemeral: bool = False,
    ):
        member = member or i.user
        await i.response.defer(ephemeral=ephemeral)
        result = await self.genshin_app.get_real_time_notes(
            member.id, i.user.id, i.locale
        )
        if not result.success:
            await i.followup.send(embed=result.result, ephemeral=True)
        else:
            note_result: RealtimeNoteResult = result.result
            fp = note_result.file
            fp.seek(0)
            await i.followup.send(
                embed=note_result.embed, file=File(fp, filename="realtime_notes.jpeg")
            )

    @check_account()
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
    async def stats(self, i: Interaction, member: Optional[User | Member] = None):
        await self.stats_command(i, member)

    async def stats_ctx_menu(self, i: Interaction, member: User):
        check = await check_account_predicate(i, member)
        if not check:
            return
        await self.stats_command(i, member, context_command=True)

    async def stats_command(
        self,
        i: Interaction,
        member: Optional[User | Member] = None,
        context_command: bool = False,
    ) -> None:
        await i.response.defer()
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        uid = await get_uid(member.id, self.bot.db)
        if uid is None:
            raise UIDNotFound
        enka_data = await get_enka_data(i, user_locale or i.locale, uid, member)
        if enka_data is None:
            return
        if enka_data.data.player is None:
            raise NoPlayerFound
        namecard = enka_data.data.player.namecard
        result = await self.genshin_app.get_stats(
            member.id, i.user.id, namecard, member.display_avatar, i.locale
        )
        if not result.success:
            await i.followup.send(embed=result.result, ephemeral=True)
        else:
            stats_result: StatsResult = result.result
            fp = stats_result.file
            fp.seek(0)
            file = File(fp, "stat_card.jpeg")
            await i.followup.send(
                embed=stats_result.embed,
                ephemeral=False if not context_command else True,
                files=[file],
            )

    @check_account()
    @app_commands.command(
        name="area",
        description=_("View exploration rates of different areas in genshin", hash=419),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(
        member=_("Check other user's data", hash=416),
    )
    async def area(self, i: Interaction, member: Optional[User | Member] = None):
        await i.response.defer()
        member = member or i.user
        result = await self.genshin_app.get_area(member.id, i.user.id, i.locale)
        if not result.success:
            await i.followup.send(embed=result.result)
        else:
            area_result: AreaResult = result.result
            fp = area_result.file
            fp.seek(0)
            image = File(fp, "area.jpeg")
            await i.followup.send(embed=area_result.embed, files=[image])

    @check_cookie()
    @app_commands.command(
        name="claim",
        description=_(
            "View info about your Hoyolab daily check-in rewards",
            hash=420,
        ),
    )
    async def claim(self, i: Interaction):
        await return_claim_reward(i, self.genshin_app)

    @check_cookie()
    @app_commands.command(
        name="characters",
        description=_(
            "View all owned characters (need /register)",
            hash=421,
        ),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("Check other user's data", hash=416))
    async def characters(self, i: Interaction, member: Optional[User | Member] = None):
        await self.characters_comamnd(i, member, False)

    async def characters_ctx_menu(self, i: Interaction, member: User):
        check = await check_cookie_predicate(i, member)
        if not check:
            return
        await self.characters_comamnd(i, member)

    async def characters_comamnd(
        self,
        i: Interaction,
        member: Optional[User | Member] = None,
        ephemeral: bool = True,
    ):
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        locale = user_locale or i.locale
        await i.response.send_message(
            embed=default_embed().set_author(
                name=text_map.get(644, locale), icon_url=asset.loader
            ),
            ephemeral=ephemeral,
        )
        result = await self.genshin_app.get_all_characters(
            member.id, i.user.id, i.locale
        )
        if not result.success:
            return await i.followup.send(embed=result.result)
        character_result: CharacterResult = result.result
        fp = character_result.file
        fp.seek(0)
        file = File(fp, "characters.jpeg")
        view = ShowAllCharacters.View(
            locale, character_result.characters, character_result.options, member
        )
        view.author = i.user
        await i.edit_original_response(
            embed=character_result.embed,
            attachments=[file],
            view=view,
        )
        view.message = await i.original_response()

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
    async def diary(self, i: Interaction, member: Optional[User | Member] = None):
        member = member or i.user
        check = await check_cookie_predicate(i, member)
        if not check:
            return
        await i.response.defer()
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        result = await self.genshin_app.get_diary(member.id, i.user.id, i.locale)
        if not result.success:
            await i.followup.send(embed=result.result)
        else:
            diary_result: DiaryResult = result.result
            view = Diary.View(i.user, member, self.genshin_app, user_locale or i.locale)
            fp = diary_result.file
            fp.seek(0)
            await i.followup.send(
                embed=diary_result.embed,
                view=view,
                files=[File(fp, "diary.jpeg")],
            )
            view.message = await i.original_response()

    @check_cookie()
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
            Choice(name=_("Current season", hash=435), value=0),
            Choice(name=_("Last season", hash=436), value=1),
        ],
    )
    async def abyss(
        self, i: Interaction, previous: int = 0, member: Optional[User | Member] = None
    ):
        member = member or i.user
        await i.response.defer()
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        result = await self.genshin_app.get_abyss(
            member.id, i.user.id, True if previous == 1 else False, i.locale
        )
        if not result.success:
            return await i.followup.send(embed=result.result)
        else:
            abyss_result: AbyssResult = result.result
            view = Abyss.View(
                i.user, abyss_result, user_locale or i.locale, self.bot.db
            )
            fp = abyss_result.overview_file
            fp.seek(0)
            image = File(fp, "overview_card.jpeg")
            await i.followup.send(
                embed=abyss_result.overview_embed, view=view, files=[image]
            )
            view.message = await i.original_response()
            await update_user_abyss_leaderboard(
                self.bot.db,
                abyss_result.abyss,
                abyss_result.genshin_user,
                abyss_result.characters,
                abyss_result.uid,
                abyss_result.genshin_user.info.nickname,
                i.user.id,
                previous,
            )

    @app_commands.command(name="stuck", description=_("Data not public?", hash=149))
    async def stuck(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        embed = default_embed(
            text_map.get(149, i.locale, user_locale),
            text_map.get(150, i.locale, user_locale),
        )
        embed.set_image(url="https://i.imgur.com/w6Q7WwJ.gif")
        await i.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="remind", description=_("Set reminders", hash=438))
    async def remind(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        await return_notification_menu(i, user_locale or i.locale, True)

    @app_commands.command(
        name="farm", description=_("View today's farmable items", hash=446)
    )
    async def farm(self, i: Interaction):
        await i.response.defer()
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        uid = await get_uid(i.user.id, self.bot.db)
        now = get_dt_now() + timedelta(hours=get_uid_tz(uid))
        result, embeds, options = await get_farm_data(i, now.weekday())

        class DomainSelect(Select):
            def __init__(self, placeholder: str, options: List[SelectOption], row: int):
                super().__init__(options=options, placeholder=placeholder, row=row)

            async def callback(self, i: Interaction):
                self.view: _view
                self.view.current_page = int(self.values[0])
                await self.view.update_children(i)

        class WeekDaySelect(Select):
            def __init__(self, placeholder: str):
                options = []
                for index in range(0, 7):
                    weekday_text = text_map.get(234 + index, i.locale, user_locale)
                    options.append(SelectOption(label=weekday_text, value=str(index)))
                super().__init__(options=options, placeholder=placeholder, row=4)

            async def callback(self, i: Interaction):
                self.view: _view
                result, embeds, options = await get_farm_data(i, int(self.values[0]))
                self.view.files = result
                self.view.embeds = embeds
                first = 1
                row = 2
                options = list(divide_chunks(options, 25))
                children = []
                for option in options:
                    children.append(
                        DomainSelect(
                            f"{text_map.get(325, i.locale, user_locale)} ({first}~{first+len(option)})",
                            option,
                            row,
                        )
                    )
                    first += 25
                    row += 1
                children.append(self)
                for child in self.view.children:
                    if isinstance(child, DomainSelect) or isinstance(
                        child, WeekDaySelect
                    ):
                        self.view.remove_item(child)
                for child in children:
                    self.view.add_item(child)
                self.view.current_page = 0
                await self.view.update_children(i)

        children = []
        options = list(divide_chunks(options, 25))
        first = 1
        row = 2
        for option in options:
            children.append(
                DomainSelect(
                    f"{text_map.get(325, i.locale, user_locale)} ({first}~{first+len(option)})",
                    option,
                    row,
                )
            )
            first += 25
            row += 1
        children.append(WeekDaySelect(text_map.get(583, i.locale, user_locale)))
        await DomainPaginator(
            i,
            embeds,
            self.bot.db,
            files=result,
            custom_children=children,
        ).start()

    @app_commands.command(
        name="build",
        description=_(
            "View character builds: Talent levels, artifacts, weapons", hash=447
        ),
    )
    async def build(self, i: Interaction):
        view = Build.View()
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
    async def search_uid(self, i: Interaction, player: User):
        await self.search_uid_command(i, player, False)

    async def search_uid_ctx_menu(self, i: Interaction, player: User):
        await self.search_uid_command(i, player)

    async def search_uid_command(
        self, i: Interaction, player: User, ephemeral: bool = True
    ):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        uid = await get_uid(player.id, self.bot.db)
        try:
            if uid is None:
                if i.guild is not None and i.guild.id == 916838066117824553:
                    async with self.bot.main_db.execute(
                        f"SELECT uid FROM genshin_accounts WHERE user_id = ?",
                        (player.id,),
                    ) as c:
                        uid = await c.fetchone()
                    if uid is None:
                        raise UIDNotFound
                    else:
                        uid = uid[0]
                else:
                    raise UIDNotFound
        except UIDNotFound:
            return await i.response.send_message(
                embed=error_embed(
                    message=text_map.get(165, i.locale, user_locale)
                ).set_author(
                    name=text_map.get(166, i.locale, user_locale),
                    icon_url=player.avatar,
                ),
                ephemeral=True,
            )
        embed = default_embed(str(uid))
        embed.set_author(
            name=f"{player.display_name}{text_map.get(167, i.locale, user_locale)}",
            icon_url=player.avatar,
        )
        await i.response.send_message(embed=embed, ephemeral=ephemeral)

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
        i: Interaction,
        member: Optional[User | Member] = None,
        uid: Optional[int] = None,
    ):
        await self.profile_command(i, member, False, uid)

    async def profile_ctx_menu(self, i: Interaction, member: User):
        check = await check_account_predicate(i, member)
        if not check:
            return
        await self.profile_command(i, member)

    async def profile_command(
        self,
        i: Interaction,
        member: Optional[User | Member] = None,
        ephemeral: bool = True,
        custom_uid: Optional[int] = None,
    ):
        await i.response.defer(ephemeral=ephemeral)
        member = member or i.user
        locale = await get_user_locale(i.user.id, self.bot.db) or i.locale
        uid = custom_uid or await get_uid(member.id, self.bot.db)
        if uid is None:
            check = await check_account_predicate(i, member)
            if not check:
                return
        enka_data = await get_enka_data(i, locale, uid, member)
        if enka_data is None:
            return
        from_cache = []
        for c in enka_data.cache.characters:
            found = False
            for d in enka_data.data.characters:
                if c.id == d.id:
                    found = True
                    break
            if not found:
                from_cache.append(c.id)

        data = enka_data.cache
        eng_data = enka_data.eng_cache

        await i.edit_original_response(
            embed=default_embed().set_author(
                name=text_map.get(644, locale),
                icon_url=asset.loader,
            ),
            view=None,
            attachments=[],
        )

        embed = default_embed(
            text_map.get(144, locale),
            f"""
            {asset.link_emoji} [{text_map.get(588, locale)}](https://enka.network/u/{uid})
            {asset.time_emoji} {text_map.get(589, locale).format(in_x_seconds=format_dt(get_dt_now()+timedelta(seconds=enka_data.data.ttl), "R"))}
            """,
        )
        embed.set_image(url="attachment://profile.jpeg")
        embed_two = default_embed(text_map.get(145, locale))
        embed_two.set_image(url="attachment://character.jpeg")
        dark_mode = await get_user_appearance_mode(i.user.id, self.bot.db)
        fp, fp_two = await main_funcs.draw_profile_card(
            DrawInput(
                loop=self.bot.loop,
                session=self.bot.session,
                locale=locale,
                dark_mode=dark_mode,
            ),
            enka_data.data,
        )
        options = []
        for character in data.characters:
            options.append(
                SelectOption(
                    label=f"{character.name} | Lv. {character.level} | C{character.constellations_unlocked}R{character.equipments[-1].refinement}",
                    description=text_map.get(543, locale)
                    if character.id in from_cache
                    else "",
                    value=str(character.id),
                    emoji=get_character_emoji(str(character.id)),
                )
            )
        view = EnkaProfile.View(
            [embed, embed_two], [fp, fp_two], options, data, eng_data, member, locale
        )
        fp.seek(0)
        fp_two.seek(0)
        discord_file = File(fp, filename="profile.jpeg")
        discord_file_two = File(fp_two, filename="character.jpeg")
        view.author = i.user
        await i.edit_original_response(
            embeds=[embed, embed_two],
            view=view,
            attachments=[discord_file, discord_file_two],
        )
        view.message = await i.original_response()

    @check_cookie()
    @app_commands.command(name="redeem", description=_("Redeem a gift code", hash=450))
    @app_commands.rename(code=_("code", hash=451))
    async def redeem(self, i: Interaction, code: str):
        await i.response.defer()
        result = await self.genshin_app.redeem_code(
            i.user.id, i.user.id, code, i.locale
        )
        await i.followup.send(embed=result.result, ephemeral=not result.success)

    @app_commands.command(
        name="events", description=_("View ongoing genshin events", hash=452)
    )
    async def events(self, i: Interaction):
        await EventTypeChooser.return_events(i)

    @check_account()
    @app_commands.command(
        name="leaderboard", description=_("The Shenhe leaderboard", hash=252)
    )
    async def leaderboard(self, i: Interaction):
        locale = await get_user_locale(i.user.id, self.bot.db) or i.locale
        uid = await get_uid(i.user.id, self.bot.db)
        if uid is None:
            raise UIDNotFound
        embed = default_embed(message=text_map.get(253, locale))
        embed.set_author(name=f"👑 {text_map.get(252, locale)}")
        view = Leaderboard.View(locale, uid)
        view.author = i.user
        await i.response.send_message(embed=embed, view=view)
        view.message = await i.original_response()

    @app_commands.command(
        name="search", description=_("Search anything related to genshin", hash=508)
    )
    @app_commands.rename(query=_("query", hash=509))
    async def search(self, i: Interaction, query: str):
        await i.response.defer()
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        dark_mode = await get_user_appearance_mode(i.user.id, self.bot.db)
        locale = user_locale or i.locale
        try:
            ambr_top_locale = to_ambr_top(locale)
            client = AmbrTopAPI(self.bot.session, ambr_top_locale)
            if not query.isdigit():
                query = (
                    self.item_names.get(query)
                    or self.item_names.get(query.title())
                    or query
                )
            item_type = None
            for index, file in enumerate(self.text_map_files):
                if query in file:
                    item_type = index
                    break
            if item_type is None:
                raise ItemNotFound

            if item_type == 0:  # character
                character = await client.get_character_detail(query)
                if character is None:
                    raise ItemNotFound
                await parse_character_wiki(character, i, locale, client, dark_mode)

            elif item_type == 1:  # weapon
                weapon = await client.get_weapon_detail(int(query))
                if weapon is None:
                    raise ItemNotFound
                await parse_weapon_wiki(weapon, i, locale, client, dark_mode)

            elif item_type == 2:  # material
                material = await client.get_material_detail(int(query))
                if material is None:
                    raise ItemNotFound
                await parse_material_wiki(material, i, locale, client, dark_mode)

            elif item_type == 3:  # artifact
                artifact = await client.get_artifact_detail(int(query))
                if artifact is None:
                    raise ItemNotFound
                await parse_artifact_wiki(artifact, i, locale)

            elif item_type == 4:  # monster
                monster = await client.get_monster_detail(int(query))
                if monster is None:
                    raise ItemNotFound
                await parse_monster_wiki(monster, i, locale, client, dark_mode)

            elif item_type == 5:  # food
                food = await client.get_food_detail(int(query))
                if food is None:
                    raise ItemNotFound
                await parse_food_wiki(food, i, locale, client, dark_mode)

            elif item_type == 6:  # furniture
                furniture = await client.get_furniture_detail(int(query))
                if furniture is None:
                    raise ItemNotFound
                await parse_furniture_wiki(furniture, i, locale, client, dark_mode)

            elif item_type == 7:  # namecard
                namecard = await client.get_name_card_detail(int(query))
                if namecard is None:
                    raise ItemNotFound
                await parse_namecard_wiki(namecard, i, locale)

            elif item_type == 8:  # book
                book = await client.get_book_detail(int(query))
                if book is None:
                    raise ItemNotFound
                await parse_book_wiki(book, i, locale, client)

        except ItemNotFound:
            await i.followup.send(
                embed=error_embed().set_author(
                    name=text_map.get(542, i.locale, user_locale),
                    icon_url=asset.error_icon,
                ),
                ephemeral=True,
            )

    @search.autocomplete("query")
    async def query_autocomplete(
        self, i: Interaction, current: str
    ) -> List[Choice[str]]:
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        ambr_top_locale = to_ambr_top(user_locale or i.locale)
        result = []
        for queries in self.text_map_files:
            for item_id, query_names in queries.items():
                item_name = query_names[ambr_top_locale]
                if current.lower() in item_name.lower() and item_name != "":
                    result.append(Choice(name=item_name, value=item_id))
                elif " " in current:
                    splited = current.split(" ")
                    all_match = True
                    for word in splited:
                        if word.lower() not in item_name.lower():
                            all_match = False
                            break
                    if all_match and item_name != "":
                        result.append(Choice(name=item_name, value=item_id))
        if current == "":
            random.shuffle(result)
        return result[:25]

    @check_account()
    @app_commands.command(
        name="activity",
        description=_("View your past genshin activity stats", hash=459),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(
        member=_("Check other user's data", hash=416),
    )
    async def activity(self, i: Interaction, member: Optional[User | Member] = None):
        await i.response.defer()
        member = member or i.user
        result = await self.genshin_app.get_activities(member.id, i.user.id, i.locale)
        if not result.success:
            return await i.followup.send(embed=result.result, ephemeral=True)
        await GeneralPaginator(i, result.result).start(followup=True)

    @app_commands.command(
        name="beta",
        description=_("View the list of current beta items in Genshin", hash=434),
    )
    async def view_beta_items(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        client = AmbrTopAPI(self.bot.session, to_ambr_top(user_locale or i.locale))
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
        embed = default_embed(text_map.get(437, i.locale, user_locale), result)
        if first_icon_url != "":
            embed.set_thumbnail(url=first_icon_url)
        embed.set_footer(text=text_map.get(444, i.locale, user_locale))
        await i.response.send_message(embed=embed)

    def get_beta_items(
        self,
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
    async def banners(self, i: Interaction):
        await i.response.defer()
        locale = await get_user_locale(i.user.id, self.bot.db) or i.locale
        client = AmbrTopAPI(self.bot.session)
        events = await client.get_events()
        banners: List[Event] = []
        for event in events:
            if "祈願" in event.name["CHT"]:
                banners.append(event)
        if len(banners) == 0:
            return await i.followup.send(
                embed=default_embed(message=text_map.get(376, locale)).set_author(
                    name=text_map.get(23, locale)
                )
            )
        event_lang = to_event_lang(locale)
        embeds = []
        for banner in banners:
            embed = default_embed(
                banner.name[event_lang],
                text_map.get(381, locale).format(
                    time=format_dt(
                        datetime.strptime(banner.end_time, "%Y-%m-%d %H:%M:%S")
                    )
                ),
            )
            embed.set_image(url=banner.banner[event_lang])
            embeds.append(embed)
        await GeneralPaginator(i, embeds).start(followup=True)

    @app_commands.command(
        name="abyss-enemies",
        description=_("View the list of enemies in the current abyss phases", hash=294),
    )
    async def abyss_enemies(self, i: Interaction):
        await i.response.defer()
        locale = await get_user_locale(i.user.id, self.bot.db) or i.locale
        floors, version = await get_abyss_enemies(self.bot.session)
        embeds = {}
        enemies = {}
        for floor in floors:
            for chamber in floor.chambers:
                embed = default_embed(
                    f"{text_map.get(146, locale).format(a=floor.num)} - {text_map.get(177, locale).format(a=chamber.num)}"
                )
                embed.add_field(
                    name=text_map.get(706, locale),
                    value=add_bullet_points(floor.ley_line_disorders),
                    inline=False,
                )
                embed.add_field(
                    name=text_map.get(295, locale),
                    value=chamber.enemy_level,
                    inline=False,
                )
                embed.add_field(
                    name=text_map.get(296, locale),
                    value=chamber.challenge_target,
                    inline=False,
                )
                embed.set_image(url="attachment://enemies.jpeg")
                embeds[embed.title] = embed
                enemies[embed.title] = chamber.halfs
        embed = default_embed()
        embed.set_image(
            url="https://cdn.esports.gg/wp-content/uploads/2022/08/04011001/Kazuha-Spiral-Abyss.jpg"
        )
        embed.set_author(
            name=f"{text_map.get(705, locale)} (v{version})",
            icon_url=i.user.display_avatar.url,
        )
        view = AbyssEnemy.View(locale, enemies, embeds)
        view.add_item(
            Button(
                url="https://genshin-impact.fandom.com/wiki/Spiral_Abyss/Floors",
                label=text_map.get(96, locale),
                emoji=asset.fandom_emoji,
            )
        )
        view.author = i.user
        await i.followup.send(embed=embed, view=view)
        view.message = await i.original_response()

    @app_commands.command(
        name="lineup",
        description=_(
            "Search Genshin lineups with Hoyolab's lineup simulator", hash=38
        ),
    )
    async def slash_lineup(self, i: Interaction):
        locale = await get_user_locale(i.user.id, self.bot.db) or i.locale

        client = self.bot.genshin_client
        client.lang = to_genshin_py(locale)
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
            options.append(SelectOption(label=scenario.name, value=str(scenario.id)))
            scenario_dict[str(scenario.id)] = scenario

        ambr = AmbrTopAPI(i.client.session, to_ambr_top(locale))
        characters = await ambr.get_character(include_beta=False)

        if isinstance(characters, List):
            view = Lineup.View(locale, options, scenario_dict, characters)
            view.author = i.user
            await Lineup.search_lineup(i, view)
            view.message = await i.original_response()

    @app_commands.command(
        name="tcg", description=_("Search a card in the Genshin TCG", hash=717)
    )
    @app_commands.rename(card_id=_("card", hash=718))
    async def slash_tcg(self, i: Interaction, card_id: str):
        locale = await get_user_locale(i.user.id, self.bot.db) or i.locale
        g_locale = to_genshin_py(locale)

        the_card = None
        card_type = None

        for card in self.card_en_us["role_card_infos"]:
            if card["id"] == int(card_id):
                the_card = card
                card_type = "role"
                break

        if not the_card:
            for card in self.card_en_us["action_card_infos"]:
                if card["id"] == int(card_id):
                    the_card = card
                    card_type = "action"
                    break

        if not the_card:
            return await i.response.send_message(
                embed=error_embed().set_author(
                    name=text_map.get(719, locale), icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )

        card = the_card

        if card_type == "role":
            embed = default_embed(self.tcg_trans(card["name"], g_locale))
            embed.set_footer(
                text=f"{text_map.get(33, locale)}: {self.tcg_trans(card['weapon'], g_locale)}"
            )
            for skill in card["role_skill_infos"]:
                cost_str = f"**{text_map.get(710, locale)}: **"
                cost_str += " / ".join(
                    [
                        f"{get_element_name(get_dice_element(cost['cost_icon']), locale)} ({cost['cost_num']})"
                        for cost in skill["skill_costs"]
                        if cost["cost_num"]
                    ]
                )
                embed.add_field(
                    name=self.tcg_trans(skill["name"], g_locale),
                    value=parse_HTML(self.tcg_trans(skill["skill_text"], g_locale))
                    + "\n"
                    + cost_str,
                    inline=False,
                )
        else:
            embed = default_embed(
                self.tcg_trans(card["name"], g_locale),
                parse_HTML(self.tcg_trans(card["content"], g_locale)),
            )
            if card["cost_num1"]:
                cost_str = f"{get_element_name(get_dice_element(card['cost_type1_icon']), locale)} ({card['cost_num1']})"
                if card["cost_num2"]:
                    cost_str += f" / {get_element_name(get_dice_element(card['cost_type2_icon']), locale)} ({card['cost_num2']})"
                embed.add_field(name=text_map.get(710, locale), value=cost_str)
        embed.set_image(url=card["resource"].replace("-sea", ""))

        await i.response.send_message(embed=embed)

    @slash_tcg.autocomplete("card_id")
    async def query_autocomplete(
        self, i: Interaction, current: str
    ) -> List[Choice[str]]:
        locale = await get_user_locale(i.user.id, self.bot.db) or i.locale
        g_locale = to_genshin_py(locale)

        choices = []

        cards = (
            self.card_en_us["role_card_infos"] + self.card_en_us["action_card_infos"]
        )

        for card in cards:
            if g_locale == "en-us":
                card_name = card["name"]
            else:
                card_name = self.card_i18n[g_locale][card["name"]]
            if current.lower() in card_name.lower():
                choices.append(Choice(name=card_name, value=str(card["id"])))

        if not current:
            choices = random.choices(choices, k=25)

        return choices[:25]

    def tcg_trans(self, text: str, locale: str):
        if locale == "en-us":
            return text
        else:
            return self.card_i18n[locale][text]


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GenshinCog(bot))
