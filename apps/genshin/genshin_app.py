import ast
from datetime import datetime, timezone
from typing import Dict, Literal, Tuple

import aiosqlite
import sentry_sdk
from apps.genshin.user_model import ShenheUser
from yelan.draw import draw_stats_card
from apps.genshin.utils import get_area_emoji, get_character
from apps.text_map.convert_locale import to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_element_name, get_month_name, get_user_locale
from discord import Embed, Locale, User, SelectOption
from discord.ext import commands
from discord.utils import format_dt
from utility.utils import default_embed, error_embed, log
from data.game.elements import element_emojis

import genshin


class GenshinApp:
    def __init__(self, db: aiosqlite.Connection, bot: commands.Bot) -> None:
        self.db = db
        self.bot = bot

    async def set_cookie(
        self, user_id: int, cookie: str, locale: Locale, uid: int = None
    ):
        log.info(f"[Set Cookie][Start][{user_id}]: [Cookie]{cookie} [UID]{uid}")
        user = self.bot.get_user(user_id)
        if user is None:
            user = await self.bot.fetch_user(user_id)
        user_locale = await get_user_locale(user_id, self.db)
        user_id = int(user_id)
        try:
            cookie = dict(item.split("=") for item in cookie.split("; "))
        except (KeyError, ValueError):
            result = error_embed(
                message=text_map.get(35, locale, user_locale)
            ).set_author(
                name=text_map.get(36, locale, user_locale),
                icon_url=user.display_avatar.url,
            )
            return result, False
        except Exception as e:
            log.warning(f"[Set Cookie][Failed][{user_id}]: [type]{type(e)} [error]{e}")
            sentry_sdk.capture_exception(e)
            embed = error_embed().set_author(
                name=text_map.get(135, locale, user_locale),
                icon_url=user.display_avatar.url,
            )
            return embed, False

        client = genshin.Client()
        user_locale = user_locale or locale
        client.lang = to_genshin_py(user_locale)
        cookies = {"ltuid": int(cookie["ltuid"]), "ltoken": cookie["ltoken"]}
        client.set_cookies(cookies)
        if uid is None:
            try:
                accounts = await client.get_game_accounts()
            except genshin.InvalidCookies:
                try:
                    client.region = genshin.Region.CHINESE
                    accounts = await client.get_game_accounts()
                except genshin.errors.InvalidCookies:
                    result = error_embed(
                        message=text_map.get(35, locale, user_locale)
                    ).set_author(
                        name=text_map.get(36, locale, user_locale),
                        icon_url=user.display_avatar.url,
                    )
                    return result, False
            if len(accounts) == 0:
                result = error_embed(
                    message=text_map.get(37, locale, user_locale)
                ).set_author(
                    name=text_map.get(38, locale, user_locale),
                    icon_url=user.display_avatar.url,
                )
                return result, False
            elif len(accounts) == 1:
                uid = accounts[0].uid
            else:
                account_options = []
                for account in accounts:
                    account_options.append(
                        SelectOption(
                            label=f"{account.uid} | Lvl. {account.level} | {account.nickname}",
                            value=account.uid,
                        )
                    )
                return account_options, True
        first_number = uid // 100000000
        is_cn = True if first_number in [1, 2, 5] else False
        c = await self.db.cursor()
        await c.execute(
            "INSERT INTO genshin_accounts (user_id, ltuid, ltoken, cookie_token, uid, cn_region) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (user_id) DO UPDATE SET ltuid = ?, ltoken = ?, cookie_token = ?, uid = ?, cn_region = ? WHERE user_id = ?",
            (
                user_id,
                int(cookie["ltuid"]),
                cookie["ltoken"],
                cookie["cookie_token"],
                uid,
                1 if is_cn else 0,
                int(cookie["ltuid"]),
                cookie["ltoken"],
                cookie["cookie_token"],
                uid,
                1 if is_cn else 0,
                user_id,
            ),
        )
        result = default_embed().set_author(
            name=text_map.get(39, locale, user_locale),
            icon_url=user.display_avatar.url,
        )
        await self.db.commit()
        log.info(f"[Set Cookie][Success][{user_id}]")
        return result, True

    async def claim_daily_reward(self, user_id: int, locale: Locale):
        shenhe_user = await self.get_user_data(user_id, locale)
        try:
            reward = await shenhe_user.client.claim_daily_reward()
        except genshin.errors.AlreadyClaimed:
            return (
                error_embed().set_author(
                    name=text_map.get(40, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except genshin.errors.InvalidCookies:
            return (
                error_embed(message=text_map.get(35, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(36, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            log.warning(
                f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
            )
            return (
                error_embed().set_author(
                    name=text_map.get(23, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        else:
            return (
                default_embed(
                    message=f"{text_map.get(41, locale, shenhe_user.user_locale)} {reward.amount}x {reward.name}"
                ).set_author(
                    name=text_map.get(42, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                True,
            )

    async def get_real_time_notes(self, user_id: int, locale: Locale):
        shenhe_user = await self.get_user_data(user_id, locale)
        try:
            notes = await shenhe_user.client.get_notes(shenhe_user.uid)
        except genshin.errors.DataNotPublic:
            return (
                error_embed(message=text_map.get(21, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(22, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except genshin.errors.InvalidCookies:
            return (
                error_embed(message=text_map.get(35, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(36, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            log.warning(
                f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
            )
            return (
                error_embed().set_author(
                    name=text_map.get(23, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        else:
            return (
                (await self.parse_resin_embed(notes, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(24, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                True,
            )

    async def parse_resin_embed(
        self, notes: genshin.models.Notes, locale: Locale, user_locale: str
    ) -> Embed:
        now = datetime.now(timezone.utc)
        if notes.current_resin == notes.max_resin:
            resin_recover_time = text_map.get(1, locale, user_locale)
        else:
            resin_recover_time = format_dt(notes.resin_recovery_time, "R")

        if notes.current_realm_currency == notes.max_realm_currency:
            realm_recover_time = text_map.get(1, locale, user_locale)
        else:
            realm_recover_time = format_dt(notes.realm_currency_recovery_time, "R")
        if notes.transformer_recovery_time is not None:
            if (now - notes.transformer_recovery_time).total_seconds() < 60:
                transformer_recover_time = text_map.get(9, locale, user_locale)
            else:
                transformer_recover_time = format_dt(
                    notes.transformer_recovery_time, "R"
                )
        else:
            transformer_recover_time = text_map.get(10, locale, user_locale)
        result = default_embed(
            message=f"<:daily:1004648484877651978> {text_map.get(11, locale, user_locale)}: {notes.completed_commissions}/{notes.max_commissions}\n"
            f"<:transformer:1004648470981902427> {text_map.get(12, locale, user_locale)}: {transformer_recover_time}"
        )
        result.add_field(
            name=f"<:resin:1004648472995168326> {text_map.get(13, locale, user_locale)}",
            value=f"{text_map.get(14, locale, user_locale)}: {notes.current_resin}/{notes.max_resin}\n"
            f"{text_map.get(15, locale, user_locale)}: {resin_recover_time}\n"
            f"{text_map.get(16, locale, user_locale)}: {notes.remaining_resin_discounts}/3",
            inline=False,
        )
        result.add_field(
            name=f"<:realm:1004648474266062880> {text_map.get(17, locale, user_locale)}",
            value=f" {text_map.get(14, locale, user_locale)}: {notes.current_realm_currency}/{notes.max_realm_currency}\n"
            f"{text_map.get(15, locale, user_locale)}: {realm_recover_time}",
            inline=False,
        )
        exped_finished = 0
        exped_msg = ""
        total_exped = len(notes.expeditions)
        if not notes.expeditions:
            exped_msg = text_map.get(18, locale, user_locale)
        for expedition in notes.expeditions:
            exped_msg += f"• {expedition.character.name}"
            if expedition.finished:
                exped_finished += 1
                exped_msg += f": {text_map.get(19, locale, user_locale)}\n"
            else:
                exped_msg += f': {format_dt(expedition.completion_time, "R")}\n'
        result.add_field(
            name=f"<:ADVENTURERS_GUILD:998780550615679086> {text_map.get(20, locale, user_locale)} ({exped_finished}/{total_exped})",
            value=exped_msg,
            inline=False,
        )
        return result

    async def get_stats(
        self,
        user_id: int,
        custom_uid: int | None,
        locale: Locale,
        namecard: str,
        avatar_url: str,
    ) -> Tuple[Embed | Dict, bool]:
        shenhe_user = await self.get_user_data(user_id, locale)
        uid = custom_uid or shenhe_user.uid
        try:
            genshin_user = await shenhe_user.client.get_partial_genshin_user(uid)
            characters = await self.bot.genshin_client.get_calculator_characters(
                include_traveler=True
            )
        except genshin.errors.DataNotPublic:
            return (
                error_embed(message=text_map.get(21, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(22, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except genshin.errors.InvalidCookies:
            return (
                error_embed(message=text_map.get(35, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(36, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            log.warning(
                f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
            )
            return (
                error_embed().set_author(
                    name=text_map.get(23, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        else:
            embed = default_embed()
            embed.set_image(url="attachment://stat_card.jpeg")
            fp = self.bot.stats_card_cache.get(uid)
            if fp is None:
                fp = await draw_stats_card(
                    genshin_user.stats, namecard, avatar_url, len(characters)
                )
                self.bot.stats_card_cache[uid] = fp
            return {"embed": embed, "fp": fp}, True

    async def get_area(
        self, user_id: int, custom_uid: Literal["int", None], locale: Locale
    ):
        shenhe_user = await self.get_user_data(user_id, locale)
        uid = custom_uid or shenhe_user.uid
        try:
            genshinUser = await shenhe_user.client.get_partial_genshin_user(uid)
        except genshin.errors.DataNotPublic:
            return (
                error_embed(message=text_map.get(21, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(22, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except genshin.errors.InvalidCookies:
            return (
                error_embed(message=text_map.get(35, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(36, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            log.warning(
                f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
            )
            return (
                error_embed().set_author(
                    name=text_map.get(23, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        else:
            explorations = genshinUser.explorations
            explore_str = ""
            for exploration in reversed(explorations):
                level_str = (
                    ""
                    if exploration.id == 5 or exploration.id == 6
                    else f"Lvl. {exploration.offerings[0].level}"
                )
                emoji = get_area_emoji(exploration.id)
                explore_str += f"{emoji} {exploration.name} | {exploration.explored}% | {level_str}\n"
            result = default_embed(message=explore_str)
        return (
            result.set_author(
                name=text_map.get(58, locale, shenhe_user.user_locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            ),
            True,
        )

    async def get_diary(self, user_id: int, month: int, locale: Locale):
        shenhe_user = await self.get_user_data(user_id, locale)
        try:
            diary = await shenhe_user.client.get_diary(month=month)
        except genshin.errors.DataNotPublic:
            return (
                error_embed(message=text_map.get(21, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(22, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except genshin.errors.InvalidCookies:
            return (
                error_embed(message=text_map.get(35, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(36, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            log.warning(
                f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
            )
            return (
                error_embed().set_author(
                    name=text_map.get(23, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        else:
            d = diary.data
            result = default_embed(
                message=f"{text_map.get(59, locale, shenhe_user.user_locale)} {text_map.get(60, locale, shenhe_user.user_locale) if d.primogems_rate > 0 else text_map.get(61, locale, shenhe_user.user_locale)} {abs(d.primogems_rate)}%\n"
                f"{text_map.get(62, locale, shenhe_user.user_locale)} {text_map.get(60, locale, shenhe_user.user_locale) if d.mora_rate > 0 else text_map.get(61, locale, shenhe_user.user_locale)} {abs(d.mora_rate)}%"
            )
            result.add_field(
                name=text_map.get(63, locale, shenhe_user.user_locale),
                value=f"<:PRIMO:1010048703312171099> {d.current_primogems} ({int(d.current_primogems/160)} <:pink_ball:984652245851316254>) • {text_map.get(64, locale, shenhe_user.user_locale)}: {d.last_primogems} ({int(d.last_primogems/160)} <:pink_ball:984652245851316254>)\n"
                f"<:MORA:1010048704901828638> {d.current_mora} • {text_map.get(64, locale, shenhe_user.user_locale)}: {d.last_mora}",
                inline=False,
            )
            msg = ""
            for cat in d.categories:
                msg += f"{cat.name}: {cat.amount} | {cat.percentage}%\n"
            result.add_field(
                name=text_map.get(65, locale, shenhe_user.user_locale), value=msg, inline=False
            )
            result.add_field(
                name=text_map.get(66, locale, shenhe_user.user_locale),
                value=f"{text_map.get(67, locale, shenhe_user.user_locale)}\n{text_map.get(68, locale, shenhe_user.user_locale)}",
                inline=False,
            )
            result.set_author(
                name=f"{text_map.get(69, locale, shenhe_user.user_locale)} • {get_month_name(month, locale, shenhe_user.user_locale)}",
                icon_url=shenhe_user.discord_user.display_avatar.url,
            )
            return result, True

    async def get_diary_logs(self, user_id: int, locale: Locale):
        shenhe_user = await self.get_user_data(user_id, locale)
        try:
            _ = await shenhe_user.client.get_diary()
        except genshin.errors.DataNotPublic as e:
            return (
                error_embed(message=text_map.get(21, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(22, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except genshin.errors.InvalidCookies:
            return (
                error_embed(message=text_map.get(35, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(36, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            log.warning(
                f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
            )
            return (
                error_embed().set_author(
                    name=text_map.get(23, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        else:
            primoLog = ""
            result = []
            async for action in shenhe_user.client.diary_log(limit=30):
                primoLog = (
                    primoLog
                    + f"{action.action} - {action.amount} {text_map.get(71, locale, shenhe_user.user_locale)}"
                    + "\n"
                )
            embed = default_embed(message=f"{primoLog}")
            embed.set_author(
                name=text_map.get(70, locale, shenhe_user.user_locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            )
            result.append(embed)
            moraLog = ""
            async for action in shenhe_user.client.diary_log(
                limit=30, type=genshin.models.DiaryType.MORA
            ):
                moraLog = (
                    moraLog
                    + f"{action.action} - {action.amount} {text_map.get(73, locale, shenhe_user.user_locale)}"
                    + "\n"
                )
            embed = default_embed(message=f"{moraLog}")
            embed.set_author(
                name=text_map.get(72, locale, shenhe_user.user_locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            )
            result.append(embed)
        return result, True

    async def get_abyss(self, user_id: int, previous: bool, locale: Locale):
        shenhe_user = await self.get_user_data(user_id, locale)
        try:
            abyss = await shenhe_user.client.get_spiral_abyss(shenhe_user.uid, previous=previous)
        except genshin.errors.DataNotPublic:
            return (
                error_embed(message=text_map.get(21, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(22, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except genshin.errors.InvalidCookies:
            return (
                error_embed(message=text_map.get(35, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(36, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            log.warning(
                f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
            )
            return (
                error_embed().set_author(
                    name=text_map.get(23, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        else:
            result = []
            rank = abyss.ranks
            if len(rank.most_kills) == 0:
                result = error_embed(
                    message=f"{text_map.get(74, locale, shenhe_user.user_locale)}\n"
                    f"{text_map.get(75, locale, shenhe_user.user_locale)}"
                )
                result.set_author(
                    name=text_map.get(76, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                )
                return result, False
            overview = default_embed(
                f"{text_map.get(77, locale, shenhe_user.user_locale)} {abyss.season}",
                f"{text_map.get(78, locale, shenhe_user.user_locale)} {abyss.max_floor}\n"
                f"✦ {abyss.total_stars}",
            )
            overview.add_field(
                name=text_map.get(79, locale, shenhe_user.user_locale),
                value=f"{get_character(rank.strongest_strike[0].id)['emoji']} {text_map.get(80, locale, shenhe_user.user_locale)}: {rank.strongest_strike[0].value}\n"
                f"{get_character(rank.most_kills[0].id)['emoji']} {text_map.get(81, locale, shenhe_user.user_locale)}: {rank.most_kills[0].value}\n"
                f"{get_character(rank.most_damage_taken[0].id)['emoji']} {text_map.get(82, locale, shenhe_user.user_locale)}: {rank.most_damage_taken[0].value}\n"
                f"{get_character(rank.most_bursts_used[0].id)['emoji']} {text_map.get(83, locale, shenhe_user.user_locale)}: {rank.most_bursts_used[0].value}\n"
                f"{get_character(rank.most_skills_used[0].id)['emoji']} {text_map.get(84, locale, shenhe_user.user_locale)}: {rank.most_skills_used[0].value}",
            )
            overview.set_author(
                name=text_map.get(85, locale, shenhe_user.user_locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            )
            result.append(overview)

            for floor in abyss.floors:
                embed = default_embed(
                    f"{text_map.get(146, locale, shenhe_user.user_locale)} {floor.floor} {text_map.get(147, locale, shenhe_user.user_locale)} (✦ {floor.stars}/9)"
                )
                for chamber in floor.chambers:
                    name = f"{text_map.get(86, locale, shenhe_user.user_locale)} {chamber.chamber} {text_map.get(87, locale, shenhe_user.user_locale)} ✦ {chamber.stars}"
                    chara_list = [[], []]
                    for i, battle in enumerate(chamber.battles):
                        for chara in battle.characters:
                            chara_list[i].append(
                                f"{get_character(chara.id)['emoji']} **{chara.name}**"
                            )
                    topStr = ""
                    bottomStr = ""
                    for top_char in chara_list[0]:
                        topStr += f"| {top_char} "
                    for bottom_char in chara_list[1]:
                        bottomStr += f"| {bottom_char} "
                    embed.add_field(
                        name=name,
                        value=f"{text_map.get(88, locale, shenhe_user.user_locale)} {topStr}\n\n"
                        f"{text_map.get(89, locale, shenhe_user.user_locale)} {bottomStr}",
                        inline=False,
                    )
                result.append(embed)

            return result, True

    async def set_resin_notification(
        self,
        user_id: int,
        resin_notification_toggle: int,
        resin_threshold: int,
        max_notif: int,
        locale: Locale,
    ):
        c: aiosqlite.Cursor = await self.db.cursor()
        shenhe_user = await self.get_user_data(user_id, locale)
        try:
            await shenhe_user.client.get_notes(shenhe_user.uid)
        except genshin.errors.DataNotPublic:
            return (
                error_embed(message=text_map.get(21, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(22, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except genshin.errors.InvalidCookies:
            return (
                error_embed(message=text_map.get(35, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(36, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            log.warning(
                f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
            )
            return (
                error_embed().set_author(
                    name=text_map.get(23, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        else:
            if resin_notification_toggle == 0:
                await c.execute(
                    "UPDATE genshin_accounts SET resin_notification_toggle = 0 WHERE user_id = ?",
                    (user_id,),
                )
                result = default_embed().set_author(
                    name=text_map.get(98, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                )
            else:
                await c.execute(
                    "UPDATE genshin_accounts SET resin_notification_toggle = ?, resin_threshold = ? , max_notif = ? WHERE user_id = ?",
                    (resin_notification_toggle, resin_threshold, max_notif, user_id),
                )
                toggle_str = (
                    text_map.get(99, locale, shenhe_user.user_locale)
                    if resin_notification_toggle == 1
                    else text_map.get(100, locale, shenhe_user.user_locale)
                )
                result = default_embed(
                    message=f"{text_map.get(101, locale, shenhe_user.user_locale)}: {toggle_str}\n"
                    f"{text_map.get(102, locale, shenhe_user.user_locale)}: {resin_threshold}\n"
                    f"{text_map.get(103, locale, shenhe_user.user_locale)}: {max_notif}"
                )
                result.set_author(
                    name=text_map.get(104, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                )
            await self.db.commit()
        return result, True

    async def set_pot_nofitication(
        self,
        user_id: int,
        locale: Locale,
        toggle: int,
        threshold: int = None,
        max_notif: int = None,
    ):
        c: aiosqlite.Cursor = await self.db.cursor()
        shenhe_user = await self.get_user_data(user_id, locale)
        try:
            await shenhe_user.client.get_notes(shenhe_user.uid)
        except genshin.errors.DataNotPublic:
            return (
                error_embed(message=text_map.get(21, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(22, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except genshin.errors.InvalidCookies:
            return (
                error_embed(message=text_map.get(35, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(36, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            log.warning(
                f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
            )
            return (
                error_embed().set_author(
                    name=text_map.get(23, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        else:
            if toggle == 0:
                await c.execute(
                    "UPDATE genshin_accounts SET pot_notif_toggle = 0 WHERE user_id = ?",
                    (user_id,),
                )
                result = default_embed().set_author(
                    name=text_map.get(517, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                )
            else:
                await c.execute(
                    "UPDATE genshin_accounts SET pot_notif_toggle = 1, pot_threshold = ? , pot_max_notif = ? WHERE user_id = ?",
                    (threshold, max_notif, user_id),
                )
                result = default_embed(
                    message=f"{text_map.get(101, locale, shenhe_user.user_locale)}: {text_map.get(99, locale, shenhe_user.user_locale)}\n"
                    f"{text_map.get(516, locale, shenhe_user.user_locale)}: {threshold}\n"
                    f"{text_map.get(103, locale, shenhe_user.user_locale)}: {max_notif}"
                )
                result.set_author(
                    name=text_map.get(104, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                )
            await self.db.commit()

            return result, True

    async def get_all_characters(self, user_id: int, locale: Locale):
        shenhe_user = await self.get_user_data(user_id, locale)
        try:
            characters = await shenhe_user.client.get_genshin_characters(shenhe_user.uid)
        except genshin.errors.DataNotPublic:
            return (
                error_embed(message=text_map.get(21, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(22, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except genshin.errors.InvalidCookies:
            return (
                error_embed(message=text_map.get(35, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(36, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            log.warning(
                f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
            )
            return (
                error_embed().set_author(
                    name=text_map.get(23, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        else:
            # organize characters according to elements
            result = {"embeds": [], "options": []}
            organized_characters = {}
            for character in characters:
                if character.element not in organized_characters:
                    organized_characters[character.element] = []
                organized_characters[character.element].append(character)

            index = 0
            for element, characters in organized_characters.items():
                result["options"].append(
                    SelectOption(
                        emoji=element_emojis.get(element),
                        label=f"{get_element_name(element, locale, shenhe_user.user_locale)} {text_map.get(220, locale, shenhe_user.user_locale)}",
                        value=index,
                    )
                )
                message = ""
                for character in characters:
                    message += f'{get_character(character.id)["emoji"]} {character.name} | Lvl. {character.level} | C{character.constellation}R{character.weapon.refinement}\n\n'
                embed = default_embed(
                    f"{element_emojis.get(element)} {get_element_name(element, locale, shenhe_user.user_locale)} {text_map.get(220, locale, shenhe_user.user_locale)}",
                    message,
                ).set_author(
                    name=text_map.get(105, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                )
                result["embeds"].append(embed)
                index += 1
            return result, True

    async def redeem_code(self, user_id: int, code: str, locale: Locale):
        shenhe_user = await self.get_user_data(user_id, locale)
        try:
            await shenhe_user.client.redeem_code(code)
        except genshin.errors.RedemptionClaimed:
            return (
                error_embed().set_author(
                    name=text_map.get(106, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except genshin.errors.InvalidCookies:
            return (
                error_embed(message=text_map.get(35, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(36, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except genshin.errors.RedemptionInvalid:
            return (
                error_embed().set_author(
                    name=text_map.get(107, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            log.warning(
                f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
            )
            return (
                error_embed().set_author(
                    name=text_map.get(23, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        else:
            return (
                default_embed(
                    message=f"{text_map.get(108, locale, shenhe_user.user_locale)}: {code}"
                ).set_author(
                    name=text_map.get(109, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                True,
            )

    async def get_activities(self, user_id: int, custom_uid: int, locale: Locale):
        shenhe_user = await self.get_user_data(user_id, locale)
        uid = custom_uid or shenhe_user.uid
        try:
            activities = await shenhe_user.client.get_genshin_activities(uid)
        except genshin.errors.DataNotPublic:
            return (
                error_embed(message=text_map.get(21, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(22, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except genshin.errors.InvalidCookies:
            return (
                error_embed(message=text_map.get(35, locale, shenhe_user.user_locale)).set_author(
                    name=text_map.get(36, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            log.warning(
                f": [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}"
            )
            return (
                error_embed().set_author(
                    name=text_map.get(23, locale, shenhe_user.user_locale),
                    icon_url=shenhe_user.discord_user.display_avatar.url,
                ),
                False,
            )
        else:
            summer = activities.summertime_odyssey
            if summer is None:
                return (
                    error_embed().set_author(
                        name=text_map.get(110, locale, shenhe_user.user_locale),
                        icon_url=shenhe_user.discord_user.display_avatar.url,
                    ),
                    False,
                )
            result = await self.parse_summer_embed(
                summer, shenhe_user.discord_user, custom_uid, locale, shenhe_user.user_locale
            )
            return result, True

    async def parse_summer_embed(
        self,
        summer: genshin.models.Summer,
        user: User,
        custom_uid: int,
        locale: Locale,
        user_locale: Literal["str", None],
    ) -> list[Embed]:
        embeds = []
        embed = default_embed().set_author(
            name=text_map.get(111, locale, user_locale),
            icon_url=user.display_avatar.url,
        )
        embed.add_field(
            name=f"<:SCORE:983948729293897779> {text_map.get(43, locale, user_locale)}",
            value=f"{text_map.get(112, locale, user_locale)}: {summer.waverider_waypoints}/13\n"
            f"{text_map.get(113, locale, user_locale)}: {summer.waypoints}/10\n"
            f"{text_map.get(114, locale, user_locale)}: {summer.treasure_chests}",
        )
        embed.set_image(url="https://i.imgur.com/Zk1tqxA.png")
        embeds.append(embed)
        embed = default_embed().set_author(
            name=text_map.get(111, locale, user_locale),
            icon_url=user.display_avatar.url,
        )
        surfs = summer.surfpiercer
        value = ""
        for surf in surfs:
            if surf.finished:
                minutes, seconds = divmod(surf.time, 60)
                time_str = (
                    f"{minutes} {text_map.get(7, locale, user_locale)} {seconds} {text_map.get(8, locale, user_locale)}"
                    if minutes != 0
                    else f"{seconds}{text_map.get(8, locale, user_locale)}"
                )
                value += f"{surf.id}. {time_str}\n"
            else:
                value += f"{surf.id}. *{text_map.get(115, locale, user_locale)}* \n"
        embed.add_field(name=text_map.get(116, locale, user_locale), value=value)
        embed.set_thumbnail(url="https://i.imgur.com/Qt4Tez0.png")
        embeds.append(embed)
        memories = summer.memories
        for memory in memories:
            embed = default_embed().set_author(
                name=text_map.get(117, locale, user_locale),
                icon_url=user.display_avatar.url,
            )
            embed.set_thumbnail(url="https://i.imgur.com/yAbpUF8.png")
            embed.set_image(url=memory.icon)
            embed.add_field(
                name=memory.name,
                value=f"{text_map.get(119, locale, user_locale)}: {memory.finish_time}",
            )
            embeds.append(embed)
        realms = summer.realm_exploration
        for realm in realms:
            embed = default_embed().set_author(
                name=text_map.get(118, locale, user_locale),
                icon_url=user.display_avatar.url,
            )
            embed.set_thumbnail(url="https://i.imgur.com/0jyBciz.png")
            embed.set_image(url=realm.icon)
            embed.add_field(
                name=realm.name,
                value=f"{text_map.get(119, locale, user_locale)}: {realm.finish_time if realm.finished else text_map.get(115, locale, user_locale)}\n"
                f"{text_map.get(120, locale, user_locale)} {realm.success} {text_map.get(121, locale, user_locale)}\n"
                f"{text_map.get(122, locale, user_locale)} {realm.skills_used} {text_map.get(121, locale, user_locale)}",
            )
            embeds.append(embed)
        if custom_uid is not None:
            embed: Embed
            for embed in embeds:
                embed.set_footer(
                    text=f"{text_map.get(123, locale, user_locale)}: {custom_uid}"
                )
        return embeds

    async def get_user_data(self, user_id: int, locale: Locale = None):
        user = self.bot.get_user(user_id)
        if user is None:
            user = await self.bot.fetch_user(user_id)
        c: aiosqlite.Cursor = await self.db.cursor()
        await c.execute(
            "SELECT ltuid, ltoken, cookie_token, uid, cn_region FROM genshin_accounts WHERE user_id = ?",
            (user_id,),
        )
        user_data = await c.fetchone()
        is_cn = 0
        if user_data is None:
            client = self.bot.genshin_client
            uid = None
        else:
            uid = user_data[3]
            is_cn = user_data[4]
            client = genshin.Client()
            client.set_cookies(
                ltuid=user_data[0],
                ltoken=user_data[1],
                account_id=user_data[0],
                cookie_token=user_data[2],
            )
            client.uids[genshin.Game.GENSHIN] = uid

        user_locale = await get_user_locale(user_id, self.db)
        locale = user_locale or locale
        client_locale = to_genshin_py(locale) or "en-us"
        client.lang = client_locale
        client.default_game = genshin.Game.GENSHIN
        
        is_cn = True if is_cn == 1 else False

        try:
            await client.update_character_names(lang=client._lang)
        except genshin.errors.InvalidCookies:
            pass
        user_obj = ShenheUser(client=client, uid=uid, discord_user=user, user_locale=user_locale, is_cn=is_cn)
        return user_obj

    async def check_user_data(self, user_id: int):
        c: aiosqlite.Cursor = await self.db.cursor()
        await c.execute("SELECT * FROM genshin_accounts WHERE user_id = ?", (user_id,))
        user_data = await c.fetchone()
        if user_data is None:
            return False
        return True

    async def get_user_talent_notification_enabled_str(
        self, user_id: int, locale: Locale
    ) -> str:
        c: aiosqlite.Cursor = await self.db.cursor()
        user_locale = await get_user_locale(user_id, self.db)
        await c.execute(
            "SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?",
            (user_id,),
        )
        character_list: list = ast.literal_eval((await c.fetchone())[0])
        enabled_characters_str = ""
        if len(character_list) == 0:
            enabled_characters_str = text_map.get(158, locale, user_locale)
        else:
            for character_id in character_list:
                enabled_characters_str += f"• {text_map.get_character_name(character_id, locale, user_locale)}\n"
        return enabled_characters_str

    async def get_user_uid(self, user_id: int) -> int | None:
        c = await self.db.cursor()
        await c.execute(
            "SELECT uid FROM genshin_accounts WHERE user_id = ?", (user_id,)
        )
        uid = await c.fetchone()
        if uid is None:
            return None
        else:
            return uid[0]
