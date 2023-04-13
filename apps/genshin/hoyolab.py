import calendar
from datetime import timedelta
from typing import Dict, List, Optional

import discord
import enkanetwork
import genshin
from dateutil.relativedelta import relativedelta
from discord.utils import format_dt

from ambr import AmbrTopAPI
from apps.db.json import read_json
from apps.draw import main_funcs
from apps.text_map import get_month_name, text_map
from dev.base_ui import get_error_handle_embed
from dev.exceptions import UIDNotFound
from dev.models import (BotModel, DefaultEmbed, DrawInput, ErrorEmbed,
                        ShenheAccount)
from utils import (get_character_emoji, get_dt_now, get_shenhe_account,
                   get_uid, get_uid_tz, get_user_lang, get_user_theme, log,
                   update_talents_json)

from .models import *


def genshin_error_handler(func):
    async def inner_function(*args, **kwargs):
        genshin_app: GenshinApp = args[0]
        user_id = args[1]
        author_id = args[2]
        locale = args[-1]
        user = genshin_app.bot.get_user(user_id) or await genshin_app.bot.fetch_user(
            user_id
        )
        uid = await get_uid(user_id, genshin_app.bot.pool)
        author_locale = await get_user_lang(author_id, genshin_app.bot.pool)
        locale = author_locale or locale
        try:
            return await func(*args, **kwargs)
        except genshin.errors.DataNotPublic:
            embed = ErrorEmbed(description=f"{text_map.get(21, locale)}\nUID: {uid}")
            embed.set_author(
                name=text_map.get(22, locale),
                icon_url=user.display_avatar.url,
            )
            return GenshinAppResult(result=embed, success=False)
        except genshin.errors.InvalidCookies:
            embed = ErrorEmbed(description=text_map.get(767, locale))
            embed.set_author(
                name=text_map.get(36, locale),
                icon_url=user.display_avatar.url,
            )
            embed.set_footer(text=f"UID: {uid}")
            return GenshinAppResult(result=embed, success=False)
        except genshin.errors.GenshinException as e:
            log.warning(
                f"[Genshin App][GenshinException] in {func.__name__}: [e]{e} [code]{e.retcode} [msg]{e.msg}"
            )
            if e.retcode == -400005:
                embed = ErrorEmbed().set_author(name=text_map.get(14, locale))
                return GenshinAppResult(result=embed, success=False)
            embed = get_error_handle_embed(user, e, locale)
            return GenshinAppResult(result=embed, success=False)
        except Exception as e:  # skipcq: PYL-W0703
            log.warning(f"[Genshin App] Error in {func.__name__}: {e}", exc_info=e)
            embed = get_error_handle_embed(user, e, locale)
            return GenshinAppResult(result=embed, success=False)

    return inner_function


class GenshinApp:
    def __init__(self, bot) -> None:
        self.bot: BotModel = bot

    @genshin_error_handler
    async def claim_daily_reward(
        self, user_id: int, author_id: int, locale: discord.Locale
    ) -> GenshinAppResult[DefaultEmbed]:
        shenhe_user = await self.get_user_cookie(user_id, author_id, locale)
        try:
            reward = await shenhe_user.client.claim_daily_reward(
                game=genshin.Game.GENSHIN
            )
        except genshin.errors.AlreadyClaimed:
            embed = ErrorEmbed().set_author(
                name=text_map.get(40, locale, shenhe_user.user_locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            )
            return GenshinAppResult(success=False, result=embed)
        else:
            reward_str = f"{reward.amount}x {reward.name}"
            embed = DefaultEmbed(
                description=text_map.get(41, locale, shenhe_user.user_locale).format(
                    reward=reward_str
                )
            )
            embed.set_author(
                name=text_map.get(42, locale, shenhe_user.user_locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            )
            embed.set_thumbnail(url=reward.icon)
            return GenshinAppResult(success=True, result=embed)

    @genshin_error_handler
    async def get_real_time_notes(
        self, user_id: int, author_id: int, locale: discord.Locale
    ) -> GenshinAppResult[RealtimeNoteResult]:
        shenhe_user = await self.get_user_cookie(user_id, author_id, locale)
        notes = await shenhe_user.client.get_genshin_notes(shenhe_user.uid)
        draw_input = DrawInput(
            loop=self.bot.loop,
            session=self.bot.session,
            locale=shenhe_user.user_locale or str(locale),
            dark_mode=await get_user_theme(author_id, self.bot.pool),
        )
        embed = await self.parse_resin_embed(notes, locale, shenhe_user.user_locale)
        return GenshinAppResult(
            success=True,
            result=RealtimeNoteResult(embed=embed, draw_input=draw_input, notes=notes),
        )

    @staticmethod
    async def parse_resin_embed(
        notes: genshin.models.Notes,
        locale: discord.Locale,
        user_locale: Optional[str] = None,
    ) -> discord.Embed:
        if notes.current_resin == notes.max_resin:
            resin_recover_time = text_map.get(1, locale, user_locale)
        else:
            resin_recover_time = format_dt(notes.resin_recovery_time, "R")

        if notes.current_realm_currency == notes.max_realm_currency:
            realm_recover_time = text_map.get(1, locale, user_locale)
        else:
            realm_recover_time = format_dt(notes.realm_currency_recovery_time, "R")
        if (
            notes.remaining_transformer_recovery_time is None
            or notes.transformer_recovery_time is None
        ):
            transformer_recover_time = text_map.get(11, locale, user_locale)
        else:
            if notes.remaining_transformer_recovery_time.total_seconds() <= 0:
                transformer_recover_time = text_map.get(9, locale, user_locale)
            else:
                transformer_recover_time = format_dt(
                    notes.transformer_recovery_time, "R"
                )
        result = DefaultEmbed(
            text_map.get(24, locale, user_locale),
            f"""
                <:resin:1004648472995168326> {text_map.get(15, locale, user_locale)}: {resin_recover_time}
                <:realm:1004648474266062880> {text_map.get(15, locale, user_locale)}: {realm_recover_time}
                <:transformer:1004648470981902427> {text_map.get(8, locale, user_locale)}: {transformer_recover_time}
            """,
        )
        if notes.expeditions:
            expedition_str = ""
            for expedition in notes.expeditions:
                if expedition.remaining_time.total_seconds() > 0:
                    expedition_str += f'{get_character_emoji(str(expedition.character.id))} {expedition.character.name} | {format_dt(expedition.completion_time, "R")}\n'
            if expedition_str:
                result.add_field(
                    name=text_map.get(20, locale, user_locale),
                    value=expedition_str,
                    inline=False,
                )
        result.set_image(url="attachment://realtime_notes.jpeg")
        return result

    @genshin_error_handler
    async def get_stats(
        self,
        user_id: int,
        author_id: int,
        namecard: enkanetwork.model.assets.NamecardAsset,
        avatar_asset: discord.Asset,
        locale: discord.Locale,
    ) -> GenshinAppResult[StatsResult]:
        shenhe_user = await self.get_user_cookie(user_id, author_id, locale)
        uid = shenhe_user.uid
        if uid is None:
            raise UIDNotFound

        embed = DefaultEmbed()
        embed.set_image(url="attachment://stat_card.jpeg")
        fp = self.bot.stats_card_cache.get(uid)
        if fp is None:
            genshin_user = await shenhe_user.client.get_partial_genshin_user(uid)
            ambr = AmbrTopAPI(self.bot.session)
            characters = await ambr.get_character(
                include_beta=False, include_traveler=False
            )
            if not isinstance(characters, List):
                raise TypeError("Characters is not a list")

            mode = await get_user_theme(author_id, self.bot.pool)
            fp = await main_funcs.draw_stats_card(
                DrawInput(loop=self.bot.loop, session=self.bot.session, dark_mode=mode),
                namecard,
                genshin_user.stats,
                avatar_asset,
                len(characters),
            )
            self.bot.stats_card_cache[uid] = fp

        return GenshinAppResult(success=True, result=StatsResult(embed=embed, file=fp))

    @genshin_error_handler
    async def get_area(
        self, user_id: int, author_id: int, locale: discord.Locale
    ) -> GenshinAppResult[AreaResult]:
        shenhe_user = await self.get_user_cookie(user_id, author_id, locale)
        uid = shenhe_user.uid
        if uid is None:
            raise UIDNotFound
        embed = DefaultEmbed()
        embed.set_author(
            name=text_map.get(58, locale, shenhe_user.user_locale),
            icon_url=shenhe_user.discord_user.display_avatar.url,
        )
        embed.set_image(url="attachment://area.jpeg")
        genshin_user = await shenhe_user.client.get_partial_genshin_user(uid)
        explorations = genshin_user.explorations
        fp = self.bot.area_card_cache.get(uid)
        if fp is None:
            mode = await get_user_theme(author_id, self.bot.pool)
            fp = await main_funcs.draw_area_card(
                DrawInput(loop=self.bot.loop, session=self.bot.session, dark_mode=mode),
                list(explorations),
            )
        result = {
            "embed": embed,
            "file": fp,
        }
        return GenshinAppResult(success=True, result=AreaResult(**result))

    @genshin_error_handler
    async def get_diary(
        self,
        user_id: int,
        author_id: int,
        locale: discord.Locale,
        month: Optional[int] = None,
    ) -> GenshinAppResult[DiaryResult]:
        shenhe_user = await self.get_user_cookie(user_id, author_id, locale)
        if shenhe_user.china:
            shenhe_user.client.region = genshin.Region.CHINESE
        user_timezone = get_uid_tz(shenhe_user.uid)
        now = get_dt_now() + timedelta(hours=user_timezone)
        if month is not None:
            now = now + relativedelta(months=month)
        diary = await shenhe_user.client.get_diary(month=now.month)
        if shenhe_user.uid is None:
            raise UIDNotFound
        user = await shenhe_user.client.get_partial_genshin_user(shenhe_user.uid)
        result = {}
        embed = DefaultEmbed()
        fp = await main_funcs.draw_diary_card(
            DrawInput(
                loop=self.bot.loop,
                session=self.bot.session,
                locale=shenhe_user.user_locale or locale,
                dark_mode=await get_user_theme(author_id, self.bot.pool),
            ),
            diary,
            user,
            now.month,
        )
        embed.set_image(url="attachment://diary.jpeg")
        embed.set_author(
            name=f"{text_map.get(69, locale, shenhe_user.user_locale)} • {get_month_name(now.month, locale, shenhe_user.user_locale)}",
            icon_url=shenhe_user.discord_user.display_avatar.url,
        )
        result["embed"] = embed
        result["file"] = fp
        return GenshinAppResult(success=True, result=DiaryResult(**result))

    @genshin_error_handler
    async def get_diary_logs(
        self, user_id: int, author_id: int, primo: bool, locale: discord.Locale
    ) -> GenshinAppResult[DiaryLogsResult]:
        shenhe_user = await self.get_user_cookie(user_id, author_id, locale)
        if shenhe_user.china:
            shenhe_user.client.region = genshin.Region.CHINESE

        now = get_dt_now()
        primo_per_day: Dict[int, int] = {}

        async for action in shenhe_user.client.diary_log(
            uid=shenhe_user.uid,
            month=now.month,
            type=genshin.models.DiaryType.PRIMOGEMS
            if primo
            else genshin.models.DiaryType.MORA,
        ):
            if action.time.day not in primo_per_day:
                primo_per_day[action.time.day] = 0
            primo_per_day[action.time.day] += action.amount

        before_adding: Dict[int, int] = primo_per_day.copy()
        before_adding = dict(sorted(before_adding.items()))

        for i in range(1, calendar.monthrange(now.year, now.month)[1] + 1):
            if i not in primo_per_day:
                primo_per_day[i] = 0

        primo_per_day = dict(sorted(primo_per_day.items()))

        return GenshinAppResult(
            success=True,
            result=DiaryLogsResult(
                primo_per_day=primo_per_day,
                before_adding=before_adding,
            ),
        )

    @genshin_error_handler
    async def get_abyss(
        self, user_id: int, author_id: int, previous: bool, locale: discord.Locale
    ) -> GenshinAppResult[AbyssResult]:
        shenhe_user = await self.get_user_cookie(user_id, author_id, locale)
        if shenhe_user.uid is None:
            raise UIDNotFound

        user = await shenhe_user.client.get_partial_genshin_user(shenhe_user.uid)
        abyss = await shenhe_user.client.get_genshin_spiral_abyss(
            shenhe_user.uid, previous=previous
        )
        characters = await shenhe_user.client.get_genshin_characters(shenhe_user.uid)

        new_locale = shenhe_user.user_locale or locale
        if not abyss.ranks.most_kills:
            embed = ErrorEmbed(description=text_map.get(74, new_locale))
            embed.set_author(
                name=text_map.get(76, new_locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            )
            return GenshinAppResult(result=embed, success=False)
        result = {
            "abyss": abyss,
            "user": user,
            "discord_user": shenhe_user.discord_user,
            "characters": list(characters),
        }

        overview = DefaultEmbed()
        overview.set_image(url="attachment://overview_card.jpeg")
        overview.set_author(
            name=f"{text_map.get(85, new_locale)} | {text_map.get(77, new_locale)} {abyss.season}",
            icon_url=shenhe_user.discord_user.display_avatar.url,
        )
        overview.set_footer(text=text_map.get(254, new_locale))

        dark_mode = await get_user_theme(author_id, self.bot.pool)
        cache = self.bot.abyss_overview_card_cache
        fp = cache.get(shenhe_user.uid)
        if fp is None:
            fp = await main_funcs.draw_abyss_overview_card(
                DrawInput(
                    loop=self.bot.loop,
                    session=self.bot.session,
                    locale=new_locale,
                    dark_mode=dark_mode,
                ),
                abyss,
                user,
            )
            cache[shenhe_user.uid] = fp

        result[
            "title"
        ] = f"{text_map.get(47, new_locale)} | {text_map.get(77, new_locale)} {abyss.season}"
        result["overview"] = overview
        result["overview_card"] = fp
        result["floors"] = [floor for floor in abyss.floors if floor.floor >= 9]
        result["uid"] = shenhe_user.uid
        result = AbyssResult(**result)
        return GenshinAppResult(result=result, success=True)

    @genshin_error_handler
    async def get_all_characters(
        self, user_id: int, author_id: int, locale: discord.Locale
    ) -> GenshinAppResult[CharacterResult]:
        shenhe_user = await self.get_user_cookie(user_id, author_id, locale)
        client = shenhe_user.client
        characters = await client.get_genshin_characters(shenhe_user.uid)
        characters = list(characters)

        talents = await read_json(self.bot.pool, f"talents/{shenhe_user.uid}.json")
        if talents is None:
            await update_talents_json(
                characters, client, self.bot.pool, shenhe_user.uid, self.bot.session
            )

        return GenshinAppResult(
            success=True, result=CharacterResult(characters=characters)
        )

    @genshin_error_handler
    async def redeem_code(
        self, user_id: int, author_id: int, code: str, locale: discord.Locale
    ) -> GenshinAppResult[discord.Embed]:
        shenhe_user = await self.get_user_cookie(user_id, author_id, locale)
        try:
            await shenhe_user.client.redeem_code(code)
        except genshin.errors.RedemptionClaimed:
            return GenshinAppResult(
                result=ErrorEmbed(
                    description=f"{text_map.get(108, locale, shenhe_user.user_locale)}: {code}"
                ).set_author(
                    name=text_map.get(106, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                success=False,
            )
        except genshin.errors.RedemptionInvalid:
            return GenshinAppResult(
                result=ErrorEmbed(
                    description=f"{text_map.get(108, locale, shenhe_user.user_locale)}: {code}"
                ).set_author(
                    name=text_map.get(107, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                success=False,
            )
        except genshin.errors.RedemptionCooldown:
            return GenshinAppResult(
                result=ErrorEmbed(
                    description=f"{text_map.get(108, locale, shenhe_user.user_locale)}: {code}"
                ).set_author(
                    name=text_map.get(133, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                success=False,
            )
        else:
            return GenshinAppResult(
                result=DefaultEmbed(
                    description=f"{text_map.get(108, locale, shenhe_user.user_locale)}: {code}"
                ).set_author(
                    name=text_map.get(109, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                success=True,
            )

    @genshin_error_handler
    async def get_activities(
        self, user_id: int, author_id: int, locale: discord.Locale
    ) -> GenshinAppResult[List[discord.Embed]]:
        shenhe_user = await self.get_user_cookie(user_id, author_id, locale)
        uid = shenhe_user.uid
        if uid is None:
            raise UIDNotFound
        activities = await shenhe_user.client.get_genshin_activities(uid)
        summer = activities.summertime_odyssey
        if summer is None:
            return GenshinAppResult(
                success=False,
                result=ErrorEmbed().set_author(
                    name=text_map.get(110, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
            )
        result = await self.parse_summer_embed(
            summer,
            shenhe_user.discord_user,
            shenhe_user.user_locale or str(locale),
        )
        return GenshinAppResult(result=result, success=True)

    @staticmethod
    async def parse_summer_embed(
        summer: genshin.models.Summer,
        user: discord.User | discord.Member | discord.ClientUser,
        locale: discord.Locale | str,
    ) -> List[discord.Embed]:
        embeds: List[discord.Embed] = []

        embed = DefaultEmbed().set_author(
            name=text_map.get(111, locale),
            icon_url=user.display_avatar.url,
        )
        embed.add_field(
            name=f"<:SCORE:983948729293897779> {text_map.get(43, locale)}",
            value=f"{text_map.get(112, locale)}: {summer.waverider_waypoints}/13\n"
            f"{text_map.get(113, locale)}: {summer.waypoints}/10\n"
            f"{text_map.get(114, locale)}: {summer.treasure_chests}",
        )
        embed.set_image(url="https://i.imgur.com/Zk1tqxA.png")
        embeds.append(embed)
        embed = DefaultEmbed().set_author(
            name=text_map.get(111, locale),
            icon_url=user.display_avatar.url,
        )

        surfs = summer.surfpiercer
        value = ""
        for surf in surfs:
            if surf.finished:
                minutes, seconds = divmod(surf.time, 60)
                time_str = (
                    f"{minutes} {text_map.get(7, locale)} {seconds} sec."
                    if minutes != 0
                    else f"{seconds}{text_map.get(12, locale)}"
                )
                value += f"{surf.id}. {time_str}\n"
            else:
                value += f"{surf.id}. *{text_map.get(115, locale)}* \n"
        embed.add_field(name=text_map.get(116, locale), value=value)
        embed.set_thumbnail(url="https://i.imgur.com/Qt4Tez0.png")
        embeds.append(embed)

        memories = summer.memories
        for memory in memories:
            embed = DefaultEmbed().set_author(
                name=text_map.get(117, locale),
                icon_url=user.display_avatar.url,
            )
            embed.set_thumbnail(url="https://i.imgur.com/yAbpUF8.png")
            embed.set_image(url=memory.icon)
            embed.add_field(
                name=memory.name,
                value=f"{text_map.get(119, locale)}: {memory.finish_time}",
            )
            embeds.append(embed)

        realms = summer.realm_exploration
        for realm in realms:
            embed = DefaultEmbed().set_author(
                name=text_map.get(118, locale),
                icon_url=user.display_avatar.url,
            )
            embed.set_thumbnail(url="https://i.imgur.com/0jyBciz.png")
            embed.set_image(url=realm.icon)
            embed.add_field(
                name=realm.name,
                value=f"{text_map.get(119, locale)}: {realm.finish_time if realm.finished else text_map.get(115, locale)}\n"
                f"{text_map.get(120, locale)} {realm.success} {text_map.get(121, locale)}\n"
                f"{text_map.get(122, locale)} {realm.skills_used} {text_map.get(121, locale)}",
            )
            embeds.append(embed)

        return embeds

    async def get_user_uid(self, user_id: int) -> int | None:
        uid = await get_uid(user_id, self.bot.pool)
        return uid

    async def get_user_cookie(
        self, user_id: int, author_id: int, locale: discord.Locale
    ) -> ShenheAccount:
        author_locale = await get_user_lang(author_id, self.bot.pool)
        shenhe_user = await get_shenhe_account(
            user_id, self.bot, locale=author_locale or locale
        )
        return shenhe_user
