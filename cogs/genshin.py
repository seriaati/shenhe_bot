import asyncio
import json
from datetime import datetime
from pprint import pprint
from diskcache import FanoutCache
import random
from time import process_time
from typing import Dict, List
import aiosqlite
import GGanalysislib
from ambr.client import AmbrTopAPI
from ambr.models import Character, Weapon
from apps.genshin.genshin_app import GenshinApp
from apps.genshin.utils import (
    calculate_artifact_score,
    get_artifact,
    get_character,
    get_city_emoji,
    get_fight_prop,
    get_uid,
    get_weapon,
    parse_character_wiki_embed,
)
from apps.genshin.checks import *
from apps.text_map.convert_locale import to_ambr_top, to_enka, to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale, get_weekday_name
from apps.wish.wish_app import get_user_event_wish
from data.game.equip_types import equip_types
from data.game.fight_prop import fight_prop
from dateutil import parser
from discord import File, Interaction, SelectOption, User, app_commands
from discord.ui import Select
from discord.app_commands import Choice
from discord.app_commands import locale_str as _
from discord.ext import commands
from discord.utils import format_dt
from enkanetwork import (
    EnkaNetworkAPI,
    UIDNotFounded,
    EnkaNetworkResponse,
)
from enkanetwork.enum import DigitType, EquipmentsType
from UI_elements.genshin import (
    Abyss,
    ArtifactLeaderboard,
    Build,
    CharacterWiki,
    Diary,
    EnkaProfile,
    EventTypeChooser,
    ShowAllCharacters,
)
from UI_elements.genshin.DailyReward import return_claim_reward
from UI_elements.genshin.ReminderMenu import return_notification_menu
from utility.paginator import GeneralPaginator
from utility.domain_paginator import DomainPaginator
from utility.utils import (
    default_embed,
    divide_chunks,
    divide_dict,
    error_embed,
    get_user_appearance_mode,
    get_weekday_int_with_name,
    parse_HTML,
)
from UI_elements.others import ManageAccounts
from yelan.draw import draw_abyss_overview_card


class GenshinCog(commands.Cog, name="genshin"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.genshin_app = GenshinApp(self.bot.db, self.bot)
        self.debug = self.bot.debug
        with open(f"text_maps/avatar.json", "r", encoding="utf-8") as f:
            avatar = json.load(f)
        with open(f"text_maps/weapon.json", "r", encoding="utf-8") as f:
            weapon = json.load(f)
        with open(f"text_maps/material.json", "r", encoding="utf-8") as f:
            material = json.load(f)
        with open(f"text_maps/reliquary.json", "r", encoding="utf-8") as f:
            reliquary = json.load(f)
        self.text_map_files = [avatar, weapon, material, reliquary]
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

    @app_commands.command(
        name="check",
        description=_("Check resin, pot, and expedition status", hash=414),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("check other user's data", hash=416))
    async def check(self, i: Interaction, member: User = None):
        member = member or i.user
        check = await check_cookie_predicate(i, member)
        if not check:
            return
        await i.response.defer()
        result, success = await self.genshin_app.get_real_time_notes(
            member.id, i.locale
        )
        await i.followup.send(embed=result, ephemeral=not success)

    async def check_ctx_menu(self, i: Interaction, member: User):
        check = await check_cookie_predicate(i)
        if not check:
            return
        result, _ = await self.genshin_app.get_real_time_notes(member.id, i.locale)
        await i.response.send_message(embed=result, ephemeral=True)

    @app_commands.command(
        name="stats",
        description=_(
            "View your genshin stats: Active days, oculi number, and number of chests obtained",
            hash=417,
        ),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(
        member=_("check other user's data", hash=416),
    )
    async def stats(self, i: Interaction, member: User = None):
        await self.stats_command(i, member)

    async def stats_ctx_menu(self, i: Interaction, member: User):
        await self.stats_command(i, member, context_command=True)

    async def stats_command(
        self,
        i: Interaction,
        member: User = None,
        context_command: bool = False,
    ) -> None:
        check = await check_account_predicate(i, member or i.user)
        if not check:
            return
        await i.response.defer()
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        uid = await get_uid(member.id, self.bot.db)
        with FanoutCache("data/cache/enka_data_cache") as enka_cache:
            cache: EnkaNetworkResponse = enka_cache.get(uid)
        async with EnkaNetworkAPI() as enka:
            try:
                data = await enka.fetch_user(uid)
            except (UIDNotFounded, asyncio.exceptions.TimeoutError):
                if cache is None:
                    return await i.followup.send(
                        embed=error_embed(
                            message=text_map.get(519, i.locale, user_locale)
                        ).set_author(
                            name=text_map.get(286, i.locale, user_locale),
                            icon_url=i.user.display_avatar.url,
                        ),
                        ephemeral=True,
                    )
                else:
                    data = cache
        if cache is None:
            with FanoutCache("data/cache/enka_data_cache") as enka_cache:
                enka_cache[uid] = data
        if cache is not None and cache.player.namecard.id != data.player.namecard.id:
            cache.player.namecard.id = data.player.namecard.id
            with FanoutCache("data/cache/enka_data_cache") as enka_cache:
                enka_cache[uid] = cache
        namecard = data.player.namecard.banner
        result, success = await self.genshin_app.get_stats(
            member.id, namecard, member.display_avatar, i.locale
        )
        if not success:
            await i.followup.send(embed=result, ephemeral=True)
        else:
            fp = result["fp"]
            fp.seek(0)
            file = File(fp, "stat_card.jpeg")
            await i.followup.send(
                embed=result["embed"],
                ephemeral=False if not context_command else True,
                files=[file],
            )

    @app_commands.command(
        name="area",
        description=_("View exploration rates of different areas in genshin", hash=419),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(
        member=_("check other user's data", hash=416),
    )
    async def area(self, i: Interaction, member: User = None):
        check = await check_account_predicate(i, member or i.user)
        if not check:
            return
        await i.response.defer()
        member = member or i.user
        result, success = await self.genshin_app.get_area(member.id, i.locale)
        if not success:
            await i.followup.send(embed=result)
        else:
            fp = result["image"]
            fp.seek(0)
            image = File(fp, "area.jpeg")
            await i.followup.send(
                embed=result["embed"], ephemeral=not success, files=[image]
            )

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

    @app_commands.command(
        name="characters",
        description=_(
            "View all of your characters, useful for building abyss teams",
            hash=421,
        ),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(member=_("check other user's data", hash=416))
    async def characters(self, i: Interaction, member: User = None):
        await self.characters_comamnd(i, member, False)

    async def characters_ctx_menu(self, i: Interaction, member: User):
        await self.characters_comamnd(i, member)

    async def characters_comamnd(
        self, i: Interaction, member: User = None, ephemeral: bool = True
    ):
        member = member or i.user
        check = await check_cookie_predicate(i, member)
        if not check:
            return
        await i.response.defer()
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        result, success = await self.genshin_app.get_all_characters(member.id, i.locale)
        if not success:
            return await i.followup.send(embed=result)
        placeholder = text_map.get(142, i.locale, user_locale)
        await GeneralPaginator(
            i,
            result["embeds"],
            self.bot.db,
            [ShowAllCharacters.ElementSelect(result["options"], placeholder)],
        ).start(check=False, ephemeral=ephemeral, followup=True)

    @app_commands.command(
        name="diary",
        description=_(
            "View your traveler's diary: primo and mora income (needs /regsiter)",
            hash=422,
        ),
    )
    @app_commands.rename(month=_("month", hash=423), member=_("user", hash=415))
    @app_commands.describe(
        month=_("The month of the diary you're trying to view", hash=424),
        member=_("check other user's data", hash=416),
    )
    @app_commands.choices(
        month=[
            app_commands.Choice(name=_("This month", hash=425), value=0),
            app_commands.Choice(name=_("Last month", hash=64), value=-1),
            app_commands.Choice(
                name=_("The month before last month", hash=427), value=-2
            ),
        ]
    )
    async def diary(self, i: Interaction, month: int = 0, member: User = None):
        member = member or i.user
        check = await check_cookie_predicate(i, member)
        if not check:
            return
        await i.response.defer()
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        month = datetime.now().month + month
        month = month + 12 if month < 1 else month
        result, success = await self.genshin_app.get_diary(member.id, month, i.locale)
        if not success:
            await i.followup.send(embed=result)
        else:
            view = Diary.View(i.user, member, self.genshin_app, i.locale, user_locale)
            await i.followup.send(embed=result, view=view)
            view.message = await i.original_response()

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
        member=_("check other user's data", hash=416),
    )
    @app_commands.choices(
        previous=[
            Choice(name=_("Current season", hash=435), value=0),
            Choice(name=_("Last season", hash=436), value=1),
        ],
    )
    async def abyss(self, i: Interaction, previous: int = 0, member: User = None):
        member = member or i.user
        check = await check_cookie_predicate(i, member or i.user)
        if not check:
            return
        await i.response.defer()
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        previous = True if previous == 1 else False
        result, success = await self.genshin_app.get_abyss(
            member.id, previous, i.locale
        )
        if not success:
            return await i.followup.send(embed=result)
        else:
            view = Abyss.View(i.user, result, i.locale, user_locale, self.bot.db)
            fp = result["overview_card"]
            fp.seek(0)
            image = File(fp, "overview_card.jpeg")
            await i.followup.send(embed=result["overview"], view=view, files=[image])
            view.message = await i.original_response()

    @app_commands.command(name="stuck", description=_("Data not public?", hash=149))
    async def stuck(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        embed = default_embed(
            text_map.get(149, i.locale, user_locale),
            text_map.get(150, i.locale, user_locale),
        )
        embed.set_image(url="https://i.imgur.com/w6Q7WwJ.gif")
        await i.response.send_message(embed=embed, ephemeral=True)

    @check_account()
    @app_commands.command(name="remind", description=_("Set reminders", hash=438))
    async def remind(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, i.client.db)
        await return_notification_menu(i, user_locale or i.locale, True)

    @app_commands.command(
        name="farm", description=_("View today's farmable items", hash=446)
    )
    async def farm(self, i: Interaction):
        result = []
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        locale = user_locale or i.locale
        locale = to_ambr_top(locale)
        ambr = AmbrTopAPI(session=self.bot.session, lang=locale)
        domains = await ambr.get_domain()
        character_upgrades = await ambr.get_character_upgrade()
        weapon_upgrades = await ambr.get_weapon_upgrade()
        today_domains = []
        for domain in domains:
            if domain.weekday == datetime.today().weekday():
                today_domains.append(domain)
        for domain in today_domains:
            characters: Dict[int, Character] = {}
            for reward in domain.rewards:
                for upgrade in character_upgrades:
                    for item in upgrade.items:
                        if item.id == reward.id:
                            characters[upgrade.character_id] = (
                                await ambr.get_character(str(upgrade.character_id))
                            )[0]
            weapons: Dict[int, Weapon] = {}
            for reward in domain.rewards:
                for upgrade in weapon_upgrades:
                    for item in upgrade.items:
                        if item.id == reward.id:
                            [weapon] = await ambr.get_weapon(id=str(upgrade.weapon_id))
                            if not weapon.default_icon:
                                weapons[upgrade.weapon_id] = weapon
            # merge two dicts
            items = characters | weapons
            chunks = list(divide_dict(items, 12))
            for chunk in chunks:
                result.append({"domain": domain, "items": chunk})
        embeds = []
        options = []
        for index, items in enumerate(result):
            embed = default_embed(
                f"{text_map.get(2, i.locale, user_locale)} ({get_weekday_name(datetime.today().weekday(), i.locale, user_locale)}) {text_map.get(250, i.locale, user_locale)}"
            )
            embed.set_image(url=f"attachment://farm.jpeg")
            embeds.append(embed)
            domain = result[index]["domain"]
            current_len = 0
            for option in options:
                if domain.name in option.label:
                    current_len += 1
            options.append(
                SelectOption(
                    label=f"{domain.city.name} | {domain.name} #{current_len+1}",
                    value=index,
                    emoji=get_city_emoji(domain.city.id),
                )
            )

        class DomainSelect(Select):
            def __init__(self, placeholder: str, options: List[SelectOption], row: int):
                super().__init__(options=options, placeholder=placeholder, row=row)

            async def callback(self, i: Interaction):
                self.view.current_page = int(self.values[0])
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
        view = Build.View(i.user, self.bot.db)
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
        if i.guild is not None and i.guild.id == 916838066117824553:
            c = await self.bot.main_db.cursor()
            table_name = "genshin_accounts"
        else:
            c = await self.bot.db.cursor()
            table_name = "user_accounts"
        c: aiosqlite.Cursor
        if table_name == "user_accounts":
            await c.execute(
                f"SELECT uid FROM {table_name} WHERE user_id = ? AND current = 1",
                (player.id,),
            )
        else:
            await c.execute(
                f"SELECT uid FROM {table_name} WHERE user_id = ?",
                (player.id,),
            )
        uid = await c.fetchone()
        if uid is None:
            return await i.response.send_message(
                embed=error_embed(
                    message=text_map.get(165, i.locale, user_locale)
                ).set_author(
                    name=text_map.get(166, i.locale, user_locale),
                    icon_url=player.avatar,
                ),
                ephemeral=True,
            )
        uid = uid[0]
        embed = default_embed(uid)
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
        member=_("check other user's data", hash=416),
    )
    async def profile(self, i: Interaction, member: User = None):
        await self.profile_command(i, member, False)

    async def profile_ctx_menu(self, i: Interaction, member: User):
        await self.profile_command(i, member)

    async def profile_command(
        self,
        i: Interaction,
        member: User = None,
        ephemeral: bool = True,
    ):
        check = await check_account_predicate(i, member or i.user)
        if not check:
            return
        await i.response.defer(ephemeral=ephemeral)
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        enka_locale = to_enka(user_locale or i.locale)
        uid = await get_uid(member.id, self.bot.db)
        with FanoutCache("data/cache/enka_data_cache") as enka_cache:
            cache: EnkaNetworkResponse = enka_cache.get(uid)
        async with EnkaNetworkAPI(enka_locale) as enka:
            try:
                data = await enka.fetch_user(uid)
            except (UIDNotFounded, asyncio.exceptions.TimeoutError):
                if cache is None:
                    return await i.followup.send(
                        embed=error_embed(
                            message=text_map.get(519, i.locale, user_locale)
                        ).set_author(
                            name=text_map.get(286, i.locale, user_locale),
                            icon_url=i.user.display_avatar.url,
                        ),
                        ephemeral=True,
                    )
                else:
                    data = cache
        if data.characters is None:
            embed = (
                default_embed(message=text_map.get(287, i.locale, user_locale))
                .set_author(
                    name=text_map.get(141, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                )
                .set_image(url="https://i.imgur.com/frMsGHO.gif")
            )
            return await i.followup.send(embed=embed, ephemeral=True)
        if cache is None or cache.characters is None:
            cache = data
        c_dict = {}
        d_dict = {}
        new_dict = {}
        for c in cache.characters:
            c_dict[c.id] = c
        for d in data.characters:
            d_dict[d.id] = d
        new_dict = c_dict | d_dict
        cache.characters = []
        for character in list(new_dict.values()):
            cache.characters.append(character)
        cache.player = data.player
        with FanoutCache("data/cache/enka_data_cache") as enka_cache:
            enka_cache[uid] = cache
        from_cache = []
        for c in cache.characters:
            found = False
            for d in data.characters:
                if c.id == d.id:
                    found = True
                    break
            if not found:
                from_cache.append(c.id)
        data = cache
        with FanoutCache("data/cache/enka_eng_cache") as enka_eng_cache:
            eng_cache = enka_eng_cache.get(uid)
        async with EnkaNetworkAPI() as enka:
            try:
                eng_data = await enka.fetch_user(uid)
            except (UIDNotFounded, asyncio.exceptions.TimeoutError):
                pass
        if eng_cache is None:
            eng_cache = eng_data
        c_dict = {}
        d_dict = {}
        new_dict = {}
        for c in eng_cache.characters:
            c_dict[c.id] = c
        for d in eng_data.characters:
            d_dict[d.id] = d
        new_dict = c_dict | d_dict
        eng_cache.characters = []
        for character in list(new_dict.values()):
            eng_cache.characters.append(character)
        with FanoutCache("data/cache/enka_eng_cache") as enka_eng_cache:
            enka_eng_cache[uid] = eng_cache
        embeds = {}
        overview = default_embed(
            message=f"*{data.player.signature}*\n\n{text_map.get(288, i.locale, user_locale)}: Lvl. {data.player.level}\n{text_map.get(289, i.locale, user_locale)}: W{data.player.world_level}\n{text_map.get(290, i.locale, user_locale)}: {data.player.achievement}\n{text_map.get(291, i.locale, user_locale)}: {data.player.abyss_floor}-{data.player.abyss_room}"
        )
        overview.set_image(url=data.player.namecard.banner.url)
        overview.set_author(
            name=data.player.nickname, icon_url=data.player.icon.url.url
        )
        embeds["0"] = overview
        options = [
            SelectOption(
                label=text_map.get(43, i.locale, user_locale),
                value=0,
                emoji="<:SCORE:983948729293897779>",
            )
        ]
        artifact_embeds = {}
        for character in data.characters:
            options.append(
                SelectOption(
                    label=f"{character.name} | Lvl. {character.level}",
                    description=text_map.get(543, i.locale, user_locale)
                    if character.id in from_cache
                    else "",
                    value=character.id,
                    emoji=get_character(character.id)["emoji"],
                )
            )
            embed = default_embed(
                f"{character.name} C{character.constellations_unlocked}R{character.equipments[-1].refinement} | Lvl. {character.level}/{character.max_level}"
            )
            embed.add_field(
                name=text_map.get(301, i.locale, user_locale),
                value=f"<:HP:982068466410463272> {text_map.get(292, i.locale, user_locale)} - {character.stats.FIGHT_PROP_MAX_HP.to_rounded()}\n"
                f"<:ATTACK:982138214305390632> {text_map.get(260, i.locale, user_locale)} - {character.stats.FIGHT_PROP_CUR_ATTACK.to_rounded()}\n"
                f"<:DEFENSE:982068463566721064> {text_map.get(264, i.locale, user_locale)} - {character.stats.FIGHT_PROP_CUR_DEFENSE.to_rounded()}\n"
                f"<:ELEMENT_MASTERY:982068464938270730> {text_map.get(266, i.locale, user_locale)} - {character.stats.FIGHT_PROP_ELEMENT_MASTERY.to_rounded()}\n"
                f"<:CRITICAL:982068460731392040> {text_map.get(296, i.locale, user_locale)} - {character.stats.FIGHT_PROP_CRITICAL.to_percentage_symbol()}\n"
                f"<:CRITICAL_HURT:982068462081933352> {text_map.get(265, i.locale, user_locale)} - {character.stats.FIGHT_PROP_CRITICAL_HURT.to_percentage_symbol()}\n"
                f"<:CHARGE_EFFICIENCY:982068459179503646> {text_map.get(267, i.locale, user_locale)} - {character.stats.FIGHT_PROP_CHARGE_EFFICIENCY.to_percentage_symbol()}\n"
                f"<:FRIENDSHIP:982843487697379391> {text_map.get(299, i.locale, user_locale)} - {character.friendship_level}\n",
                inline=False,
            )
            # talents
            value = ""
            for skill in character.skills:
                value += f"{skill.name} | Lvl. {skill.level}\n"
            embed.add_field(name=text_map.get(94, i.locale, user_locale), value=value)
            # weapon
            weapon = character.equipments[-1]
            weapon_sub_stats = ""
            for substat in weapon.detail.substats:
                weapon_sub_stats += f"{get_fight_prop(substat.prop_id)['emoji']} {substat.name} {substat.value}{'%' if substat.type == DigitType.PERCENT else ''}\n"
            embed.add_field(
                name=text_map.get(91, i.locale, user_locale),
                value=f'{get_weapon(weapon.id)["emoji"]} {weapon.detail.name} | Lvl. {weapon.level}\n'
                f"{get_fight_prop(weapon.detail.mainstats.prop_id)['emoji']} {weapon.detail.mainstats.name} {weapon.detail.mainstats.value}{'%' if weapon.detail.mainstats.type == DigitType.PERCENT else ''}\n"
                f"{weapon_sub_stats}",
                inline=False,
            )
            embed.set_thumbnail(url=character.image.icon.url)
            embed.set_author(
                name=member.display_name, icon_url=member.display_avatar.url
            )
            embeds[str(character.id)] = embed
            # artifacts
            artifact_embed = default_embed(
                f"{character.name} | {text_map.get(92, i.locale, user_locale)}"
            )
            index = 0
            for artifact in filter(
                lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments
            ):
                artifact_sub_stats = f'**__{get_fight_prop(artifact.detail.mainstats.prop_id)["emoji"]} {text_map.get(fight_prop.get(artifact.detail.mainstats.prop_id)["text_map_hash"], i.locale, user_locale)}+{artifact.detail.mainstats.value}__**\n'
                artifact_sub_stat_dict = {}
                for substat in artifact.detail.substats:
                    artifact_sub_stat_dict[substat.prop_id] = substat.value
                    artifact_sub_stats += f'{get_fight_prop(substat.prop_id)["emoji"]} {text_map.get(fight_prop.get(substat.prop_id)["text_map_hash"], i.locale, user_locale)}+{substat.value}{"%" if substat.type == DigitType.PERCENT else ""}\n'
                if artifact.level == 20:
                    artifact_sub_stats += f"<:SCORE:983948729293897779> {int(calculate_artifact_score(artifact_sub_stat_dict))}"
                artifact_embed.add_field(
                    name=f"{list(equip_types.values())[index]}{artifact.detail.name} +{artifact.level}",
                    value=artifact_sub_stats,
                )
                artifact_embed.set_thumbnail(url=character.image.icon.url)
                artifact_embed.set_author(
                    name=member.display_name, icon_url=member.display_avatar.url
                )
                artifact_embed.set_footer(text=text_map.get(300, i.locale, user_locale))
                index += 1
            artifact_embeds[str(character.id)] = artifact_embed
        view = EnkaProfile.View(
            embeds,
            artifact_embeds,
            options,
            data,
            member,
            eng_cache,
            i.user,
            self.bot.db,
            i.locale,
            user_locale,
            data.characters,
            i.client.browser,
        )
        await i.followup.send(embed=embeds["0"], view=view, ephemeral=ephemeral)
        view.message = await i.original_response()

    @check_cookie()
    @app_commands.command(name="redeem", description=_("Redeem a gift code", hash=450))
    @app_commands.rename(code=_("code", hash=451))
    async def redeem(self, i: Interaction, code: str):
        await i.response.defer()
        result, success = await self.genshin_app.redeem_code(i.user.id, code, i.locale)
        await i.followup.send(embed=result, ephemeral=not success)

    @app_commands.command(
        name="events", description=_("View ongoing genshin events", hash=452)
    )
    async def events(self, i: Interaction):
        await i.response.defer()
        user_locale = (await get_user_locale(i.user.id, self.bot.db)) or i.locale
        genshin_py_locale = to_genshin_py(user_locale)
        event_overview_API = f"https://sg-hk4e-api.hoyoverse.com/common/hk4e_global/announcement/api/getAnnList?game=hk4e&game_biz=hk4e_global&lang={genshin_py_locale}&announcement_version=1.21&auth_appid=announcement&bundle_id=hk4e_global&channel_id=1&level=8&platform=pc&region=os_asia&sdk_presentation_style=fullscreen&sdk_screen_transparent=true&uid=901211014"
        event_details_API = f"https://sg-hk4e-api-static.hoyoverse.com/common/hk4e_global/announcement/api/getAnnContent?game=hk4e&game_biz=hk4e_global&lang={genshin_py_locale}&bundle_id=hk4e_global&platform=pc&region=os_asia&t=1659877813&level=7&channel_id=0"
        async with self.bot.session.get(event_overview_API) as r:
            overview: Dict = await r.json()
        async with self.bot.session.get(event_details_API) as r:
            details: Dict = await r.json()
        type_list = overview["data"]["type_list"]
        options = []
        for type in type_list:
            options.append(SelectOption(label=type["mi18n_name"], value=type["id"]))
        # get a dict of details
        detail_dict = {}
        for event in details["data"]["list"]:
            detail_dict[event["ann_id"]] = event["content"]
        first_id = None
        embeds = {}
        for event_list in overview["data"]["list"]:
            list = event_list["list"]
            if list[0]["type"] not in embeds:
                embeds[list[0]["type"]] = []
            if first_id is None:
                first_id = list[0]["type"]
            for event in list:
                embed = default_embed(event["title"])
                embed.set_author(name=event["type_label"], icon_url=event["tag_icon"])
                embed.set_image(url=event["banner"])
                embed.add_field(
                    name=text_map.get(406, i.locale, user_locale),
                    value=format_dt(parser.parse(event["start_time"]), "R"),
                )
                embed.add_field(
                    name=text_map.get(407, i.locale, user_locale),
                    value=format_dt(parser.parse(event["end_time"]), "R"),
                )
                embed.add_field(
                    name=text_map.get(408, i.locale, user_locale),
                    value=parse_HTML(detail_dict[event["ann_id"]])[:1021] + "...",
                    inline=False,
                )
                embeds[event["type"]].append(embed)
        await GeneralPaginator(
            i,
            embeds[first_id],
            self.bot.db,
            [EventTypeChooser.Select(options, embeds, i.locale, user_locale)],
        ).start(followup=True)

    @app_commands.guild_only()
    @app_commands.command(
        name="leaderboard", description=_("View different leaderbaords", hash=453)
    )
    @app_commands.rename(type=_("option", hash=429))
    @app_commands.choices(
        type=[
            Choice(name=_("Achievement leaderboard", hash=251), value=0),
            Choice(name=_("Artifact substat leaderboard", hash=455), value=1),
            Choice(name=_("Wish luck leaderboard", hash=456), value=2),
            Choice(name=_("Update self leaderboard position", hash=501), value=3),
        ]
    )
    async def leaderboard(self, i: Interaction, type: int):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        if type == 0:
            # fetch the leaderboard from database
            await c.execute("SELECT user_id, achievements FROM leaderboard")
            leaderboard = await c.fetchall()
            # sort the leaderboard
            leaderboard.sort(key=lambda tup: tup[1], reverse=True)
            # convert data into str
            str_list = []
            rank = 1
            user_rank = text_map.get(253, i.locale, user_locale)
            for index, tpl in enumerate(leaderboard):
                user_id = tpl[0]
                achievement_num = tpl[1]
                if i.guild is None:
                    member = i.client.get_user(user_id)
                else:
                    member = i.guild.get_member(user_id)
                if member is None:
                    continue
                if i.user.id == member.id:
                    user_rank = f"#{rank}"
                str_list.append(f"{rank}. {member.display_name} - {achievement_num}\n")
                rank += 1
            # 10 str per page
            str_list = list(divide_chunks(str_list, 10))
            # write the str into embed
            embeds = []
            for str_list in str_list:
                message = ""
                for string in str_list:
                    message += string
                embed = default_embed(
                    f"🏆 {text_map.get(251, i.locale, user_locale)} ({text_map.get(252, i.locale, user_locale)}: {user_rank})",
                    message,
                )
                embeds.append(embed)
            try:
                await GeneralPaginator(i, embeds, self.bot.db).start()
            except ValueError:
                await i.response.send_message(
                    embed=error_embed().set_author(
                        name=text_map.get(254, i.locale, user_locale),
                        icon_url=i.user.display_avatar.url,
                    ),
                    ephemeral=True,
                )
        elif type == 1:
            view = ArtifactLeaderboard.View(i.user, self.bot.db, i.locale, user_locale)
            await i.response.send_message(
                embed=default_embed().set_author(
                    name=text_map.get(255, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                view=view,
            )
            view.message = await i.original_response()
            await view.wait()
            if view.sub_stat is None:
                return
            await c.execute(
                "SELECT user_id, avatar_id, artifact_name, equip_type, sub_stat_value FROM substat_leaderboard WHERE sub_stat = ?",
                (view.sub_stat,),
            )
            leaderboard = await c.fetchall()
            leaderboard.sort(
                key=lambda tup: float(str(tup[4]).replace("%", "")), reverse=True
            )
            str_list = []
            rank = 1
            user_rank = text_map.get(253, i.locale, user_locale)
            for index, tpl in enumerate(leaderboard):
                user_id = tpl[0]
                avatar_id = tpl[1]
                artifact_name = tpl[2]
                equip_type = tpl[3]
                sub_stat_value = tpl[4]
                if i.guild is None:
                    member = i.client.get_user(user_id)
                else:
                    member = i.guild.get_member(user_id)
                if member is None:
                    continue
                if member.id == i.user.id:
                    user_rank = f"#{rank}"
                str_list.append(
                    f'{rank}. {get_character(avatar_id)["emoji"]} {get_artifact(name=artifact_name)["emoji"]} {equip_types.get(equip_type)} {member.display_name} | {sub_stat_value}\n\n'
                )
                rank += 1
            str_list = divide_chunks(str_list, 10)
            embeds = []
            for str_list in str_list:
                message = ""
                for string in str_list:
                    message += string
                embed = default_embed(
                    f'🏆 {text_map.get(256, i.locale, user_locale)} - {text_map.get(fight_prop.get(view.sub_stat)["text_map_hash"], i.locale, user_locale)} ({text_map.get(252, i.locale, user_locale)}: {user_rank})',
                    message,
                )
                embeds.append(embed)
            try:
                await GeneralPaginator(
                    i,
                    embeds,
                    self.bot.db,
                    [
                        ArtifactLeaderboard.GoBack(
                            text_map.get(282, i.locale, user_locale), self.bot.db
                        )
                    ],
                ).start(edit=True)
            except ValueError:
                await i.followup.send(
                    embed=error_embed().set_author(
                        name=text_map.get(254, i.locale, user_locale),
                        icon_url=i.user.display_avatar.url,
                    ),
                    ephemeral=True,
                )
        elif type == 2:
            await c.execute("SELECT DISTINCT user_id FROM wish_history")
            leaderboard = await c.fetchall()
            leaderboard_dict = {}
            for index, tpl in enumerate(leaderboard):
                member = i.guild.get_member(tpl[0])
                if member is not None:
                    (
                        get_num,
                        left_pull,
                        use_pull,
                        up_guarantee,
                        up_five_star_num,
                    ) = await get_user_event_wish(member.id, self.bot.db)
                    player = GGanalysislib.Up5starCharacter()
                    player_luck = round(
                        100
                        * player.luck_evaluate(
                            get_num=up_five_star_num,
                            use_pull=use_pull,
                            left_pull=left_pull,
                        ),
                        2,
                    )
                    if player_luck > 0:
                        leaderboard_dict[tpl[0]] = player_luck
            leaderboard_dict = dict(
                sorted(leaderboard_dict.items(), key=lambda item: item[1], reverse=True)
            )
            leaderboard_str_list = []
            rank = 1
            user_rank = text_map.get(253, i.locale, user_locale)
            for user_id, luck in leaderboard_dict.items():
                if i.guild is None:
                    member = i.client.get_user(user_id)
                else:
                    member = i.guild.get_member(user_id)
                if member is None:
                    continue
                if i.user.id == member.id:
                    user_rank = f"#{rank}"
                leaderboard_str_list.append(
                    f"{rank}. {member.display_name} - {luck}%\n"
                )
                rank += 1
            leaderboard_str_list = divide_chunks(leaderboard_str_list, 10)
            embeds = []
            for str_list in leaderboard_str_list:
                message = ""
                for string in str_list:
                    message += string
                embed = default_embed(
                    f"🏆 {text_map.get(257, i.locale, user_locale)} ({text_map.get(252, i.locale, user_locale)}: {user_rank})",
                    message,
                )
                embeds.append(embed)
            try:
                await GeneralPaginator(i, embeds, self.bot.db).start()
            except ValueError:
                await i.response.send_message(
                    embed=error_embed().set_author(
                        name=text_map.get(254, i.locale, user_locale),
                        icon_url=i.user.display_avatar.url,
                    ),
                    ephemeral=True,
                )
        elif type == 3:
            check = await check_account_predicate(i)
            if not check:
                return
            await i.response.defer(ephemeral=True)
            uid = await get_uid(i.user.id, self.bot.db)
            try:
                async with EnkaNetworkAPI("cht") as enka:
                    try:
                        data = await enka.fetch_user(uid)
                    except (UIDNotFounded, asyncio.exceptions.TimeoutError):
                        return await i.followup.send(
                            embed=error_embed(
                                message=text_map.get(519, i.locale, user_locale)
                            ).set_author(
                                name=text_map.get(286, i.locale, user_locale),
                                icon_url=i.user.display_avatar.url,
                            ),
                            ephemeral=True,
                        )
                achievement = data.player.achievement
                await c.execute(
                    "INSERT INTO leaderboard (user_id, achievements) VALUES (?, ?) ON CONFLICT (user_id) DO UPDATE SET user_id = ?, achievements = ?",
                    (i.user.id, achievement, i.user.id, achievement),
                )
                if data.characters is not None:
                    for character in data.characters:
                        for artifact in filter(
                            lambda x: x.type == EquipmentsType.ARTIFACT,
                            character.equipments,
                        ):
                            for substat in artifact.detail.substats:
                                await c.execute(
                                    "SELECT sub_stat_value FROM substat_leaderboard WHERE sub_stat = ? AND user_id = ?",
                                    (substat.prop_id, i.user.id),
                                )
                                sub_stat_value = await c.fetchone()
                                if (
                                    sub_stat_value is None
                                    or float(str(sub_stat_value[0]).replace("%", ""))
                                    < substat.value
                                ):
                                    await c.execute(
                                        "INSERT INTO substat_leaderboard (user_id, avatar_id, artifact_name, equip_type, sub_stat, sub_stat_value) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (user_id, sub_stat) DO UPDATE SET avatar_id = ?, artifact_name = ?, equip_type = ?, sub_stat_value = ? WHERE user_id = ? AND sub_stat = ?",
                                        (
                                            i.user.id,
                                            character.id,
                                            artifact.detail.name,
                                            artifact.detail.artifact_type,
                                            substat.prop_id,
                                            f"{substat.value}{'%' if substat.type == DigitType.PERCENT else ''}",
                                            character.id,
                                            artifact.detail.name,
                                            artifact.detail.artifact_type,
                                            f"{substat.value}{'%' if substat.type == DigitType.PERCENT else ''}",
                                            i.user.id,
                                            substat.prop_id,
                                        ),
                                    )
            except Exception as e:
                return await i.followup.send(
                    embed=error_embed(message=f"```py\n{e}\n```").set_author(
                        name=text_map.get(512, i.locale, user_locale),
                        icon_url=i.user.display_avatar.url,
                    ),
                    ephemeral=True,
                )
            else:
                await i.followup.send(
                    embed=default_embed().set_author(
                        name=text_map.get(502, i.locale, user_locale),
                        icon_url=i.user.display_avatar.url,
                    ),
                    ephemeral=True,
                )

    @app_commands.command(
        name="search", description=_("Search anything related to genshin", hash=508)
    )
    @app_commands.rename(query=_("query", hash=509))
    async def search(self, i: Interaction, query: str):
        await i.response.defer()
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        ambr_top_locale = to_ambr_top(user_locale or i.locale)
        names = ["avatar", "weapon", "material", "reliquary"]
        item_type = None
        client = AmbrTopAPI(self.bot.session, ambr_top_locale)
        for index, file in enumerate(self.text_map_files):
            if query in file:
                item_type = index
                break
        if item_type is None:
            return await i.followup.send(
                embed=error_embed().set_author(
                    name=text_map.get(542, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        if item_type == 0:
            async with self.bot.session.get(
                f"https://api.ambr.top/v2/{ambr_top_locale}/{names[item_type]}/{query}"
            ) as r:
                data = await r.json()
            embeds, material_embed, options = parse_character_wiki_embed(
                data, query, i.locale, user_locale
            )
            await GeneralPaginator(
                i,
                embeds,
                self.bot.db,
                [
                    CharacterWiki.ShowTalentMaterials(
                        material_embed, text_map.get(322, i.locale, user_locale)
                    ),
                    CharacterWiki.QuickNavigation(
                        options, text_map.get(315, i.locale, user_locale)
                    ),
                ],
            ).start(followup=True)
        elif item_type == 1:
            weapon = await client.get_weapon_detail(query)
            rarity_str = ""
            for _ in range(weapon.rarity):
                rarity_str += "<:white_star:982456919224615002>"
            embed = default_embed(weapon.name, f"{rarity_str}\n\n{weapon.description}")
            embed.add_field(
                name=text_map.get(529, i.locale, user_locale),
                value=weapon.type,
                inline=False,
            )
            embed.add_field(
                name=text_map.get(531, i.locale, user_locale),
                value=f"{weapon.effect.name}\n\n{weapon.effect.description}",
                inline=False,
            )
            main_stat = weapon.upgrade.stats[0].prop_id
            sub_stat = weapon.upgrade.stats[1].prop_id
            main_stat_hash = fight_prop.get(main_stat)["text_map_hash"]
            sub_stat_hash = fight_prop.get(sub_stat)["text_map_hash"]
            embed.add_field(
                name=text_map.get(301, i.locale, user_locale),
                value=f"{text_map.get(main_stat_hash, i.locale, user_locale)}\n{text_map.get(sub_stat_hash, i.locale, user_locale)}",
            )
            embed.set_thumbnail(url=weapon.icon)
            await i.followup.send(embed=embed)
        elif item_type == 2:
            material = await client.get_material_detail(query)
            rarity_str = ""
            for _ in range(material.rarity):
                rarity_str += "<:white_star:982456919224615002>"
            embed = default_embed(
                material.name, f"{rarity_str}\n\n{material.description}"
            )
            embed.add_field(
                name=text_map.get(529, i.locale, user_locale),
                value=material.type,
                inline=False,
            )
            source_str = ""
            for source in material.sources:
                day_str = ""
                if len(source.days) != 0:
                    day_list = [
                        get_weekday_name(
                            get_weekday_int_with_name(day), i.locale, user_locale
                        )
                        for day in source.days
                    ]
                    day_str = ", ".join(day_list)
                day_str = "" if len(source.days) == 0 else f"({day_str})"
                source_str += f"• {source.name} {day_str}\n"
            source_str = "❌" if source_str == "" else source_str
            embed.add_field(
                name=text_map.get(530, i.locale, user_locale),
                value=source_str,
                inline=False,
            )
            embed.set_thumbnail(url=material.icon)
            await i.followup.send(embed=embed)
        elif item_type == 3:
            artifact = await client.get_artifact_detail(query)
            embed = default_embed(
                artifact.name,
                f"2x: {artifact.effects.two_piece}\n\n4x: {artifact.effects.four_piece}",
            )
            embed.set_thumbnail(url=artifact.icon)
            await i.followup.send(embed=embed)

    @search.autocomplete("query")
    async def query_autocomplete(
        self, i: Interaction, current: str
    ) -> List[Choice[str]]:
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        ambr_top_locale = to_ambr_top(user_locale or i.locale)
        everything_dict = {}
        query_list = []
        for queries in self.text_map_files:
            for query_id, query_names in queries.items():
                everything_dict[query_names[ambr_top_locale]] = query_id
                query_list.append(query_names[ambr_top_locale])
        query_list = list(dict.fromkeys(query_list))
        result = [
            app_commands.Choice(name=query, value=everything_dict[query])
            for query in query_list
            if current.lower() in query.lower()
        ]
        random.shuffle(result)
        return result[:25]

    @app_commands.command(
        name="activity",
        description=_("View your past genshin activity stats", hash=459),
    )
    @app_commands.rename(member=_("user", hash=415))
    @app_commands.describe(
        member=_("check other user's data", hash=416),
    )
    async def activity(self, i: Interaction, member: User = None):
        check = await check_account_predicate(i, member or i.user)
        if not check:
            return
        member = member or i.user
        result, success = await self.genshin_app.get_activities(member.id, i.locale)
        if not success:
            return await i.response.send_message(embed=result, ephemeral=True)
        await GeneralPaginator(i, result, self.bot.db).start()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GenshinCog(bot))
