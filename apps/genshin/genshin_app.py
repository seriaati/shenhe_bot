from typing import Dict, List, Literal, Tuple
import aiosqlite
import sentry_sdk
from ambr.client import AmbrTopAPI
from apps.genshin.custom_model import ShenheUser
from apps.genshin.utils import get_character, get_shenhe_user, get_uid
from apps.text_map.convert_locale import to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_element_name, get_month_name, get_user_locale
from data.game.elements import element_emojis
from discord import Embed, Locale, SelectOption, User
from discord.ext import commands
from discord.utils import format_dt
from utility.utils import default_embed, error_embed, get_user_appearance_mode, log
from yelan.draw import (
    draw_abyss_overview_card,
    draw_area_card,
    draw_diary_card,
    draw_stats_card,
)

import genshin


class CookieInvalid(Exception):
    pass


def genshin_error_handler(func):
    async def inner_function(*args, **kwargs):
        genshin_app: GenshinApp = args[0]
        user_id = args[1]
        locale = args[-1]
        user = genshin_app.bot.get_user(user_id) or await genshin_app.bot.fetch_user(
            user_id
        )
        uid = await get_uid(user_id, genshin_app.bot.db)
        user_locale = await get_user_locale(user_id, genshin_app.bot.db)
        locale = user_locale or locale
        try:
            return await func(*args, **kwargs)
        except genshin.errors.DataNotPublic:
            embed = error_embed(message=f"{text_map.get(21, locale)}\nUID: {uid}")
            embed.set_author(
                name=text_map.get(22, locale),
                icon_url=user.display_avatar.url,
            )
            return embed, False
        except genshin.errors.InvalidCookies:
            embed = error_embed(message=f"{text_map.get(35, locale)}\nUID: {uid}")
            embed.set_author(
                name=text_map.get(36, locale),
                icon_url=user.display_avatar.url,
            )
            return embed, False
        except genshin.errors.GenshinException as e:
            log.warning(
                f"[Genshin App][GenshinException] in {func.__name__}: [e]{e} [code]{e.retcode} [msg]{e.msg}"
            )
            if e.retcode == -400005:
                embed = error_embed().set_author(name=text_map.get(14, locale))
                return embed, False
            else:
                sentry_sdk.capture_exception(e)
                embed = error_embed(message=f"```{e}```")
                embed.set_author(
                    name=text_map.get(10, locale),
                    icon_url=user.display_avatar.url,
                )
                return embed, False
        except Exception as e:
            log.warning(f"[Genshin App] Error in {func.__name__}: {e}")
            sentry_sdk.capture_exception(e)
            embed = error_embed(message=text_map.get(513, locale, user_locale))
            embed.description += f"\n```{e}```"
            embed.set_author(
                name=text_map.get(135, locale), icon_url=user.display_avatar.url
            )
            embed.set_thumbnail(url="https://i.imgur.com/Xi51hSe.gif")
            return embed, False

    return inner_function


class GenshinApp:
    def __init__(self, db: aiosqlite.Connection, bot: commands.Bot) -> None:
        self.db = db
        self.bot = bot

    async def set_cookie(
        self, user_id: int, cookie: str, locale: Locale, uid: int = None
    ):
        log.info(f"[Set Cookie][Start][{user_id}]: [Cookie]{cookie} [UID]{uid}")
        user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
        user_locale = await get_user_locale(user_id, self.db)
        user_id = int(user_id)
        try:
            try:
                cookie = dict(item.split("=") for item in cookie.split("; "))
            except (KeyError, ValueError):
                raise CookieInvalid
            except Exception as e:
                log.warning(
                    f"[Set Cookie][Failed][{user_id}]: [type]{type(e)} [error]{e}"
                )
                sentry_sdk.capture_exception(e)
                embed = error_embed().set_author(
                    name=text_map.get(135, locale, user_locale),
                    icon_url=user.display_avatar.url,
                )
                return embed, False
            required_keys = ["ltuid", "ltoken", "cookie_token"]
            for key in required_keys:
                if key not in cookie:
                    raise CookieInvalid

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
                        raise CookieInvalid
                if len(accounts) == 0:
                    result = error_embed(
                        message=text_map.get(37, locale, user_locale)
                    ).set_author(
                        name=text_map.get(38, locale, user_locale),
                        icon_url=user.display_avatar.url,
                    )
                    return result, False
                account_options: List[SelectOption] = []
                for account in accounts:
                    if account.game is not genshin.Game.GENSHIN:
                        continue
                    account_options.append(
                        SelectOption(
                            label=f"{account.uid} | Lvl. {account.level} | {account.nickname}",
                            value=account.uid,
                        )
                    )
                if len(account_options) == 1:
                    uid = account_options[0].value
                else:
                    return account_options, True
        except CookieInvalid:
            result = error_embed().set_author(
                name=text_map.get(36, locale, user_locale),
                icon_url=user.display_avatar.url,
            )
            return result, False
        china = 1 if str(uid)[0] in [1, 2, 5] else 0
        c = await self.db.cursor()
        await c.execute(
            "INSERT INTO user_accounts (uid, user_id, ltuid, ltoken, cookie_token, china) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (uid, user_id) DO UPDATE SET ltuid = ?, ltoken = ?, cookie_token = ? WHERE uid = ? AND user_id = ?",
            (
                uid,
                user_id,
                cookie["ltuid"],
                cookie["ltoken"],
                cookie["cookie_token"],
                china,
                cookie["ltuid"],
                cookie["ltoken"],
                cookie["cookie_token"],
                uid,
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

    @genshin_error_handler
    async def claim_daily_reward(self, user_id: int, locale: Locale):
        shenhe_user = await self.get_user_cookie(user_id, locale)
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

    @genshin_error_handler
    async def get_real_time_notes(self, user_id: int, locale: Locale):
        shenhe_user = await self.get_user_cookie(user_id, locale)
        notes = await shenhe_user.client.get_genshin_notes(shenhe_user.uid)
        embed = await self.parse_resin_embed(notes, locale, shenhe_user.user_locale)
        return (
            embed.set_author(
                name=text_map.get(24, locale, shenhe_user.user_locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            ),
            True,
        )

    async def parse_resin_embed(
        self, notes: genshin.models.Notes, locale: Locale, user_locale: str
    ) -> Embed:
        if notes.current_resin == notes.max_resin:
            resin_recover_time = text_map.get(1, locale, user_locale)
        else:
            resin_recover_time = format_dt(notes.resin_recovery_time, "R")

        if notes.current_realm_currency == notes.max_realm_currency:
            realm_recover_time = text_map.get(1, locale, user_locale)
        else:
            realm_recover_time = format_dt(notes.realm_currency_recovery_time, "R")
        if notes.transformer_recovery_time is None:
            transformer_recover_time = text_map.get(11, locale, user_locale)
        else:
            if notes.remaining_transformer_recovery_time.total_seconds() <= 0:
                transformer_recover_time = text_map.get(9, locale, user_locale)
            else:
                transformer_recover_time = format_dt(
                    notes.transformer_recovery_time, "R"
                )
        result = default_embed(
            message=f"<:daily:1004648484877651978> {text_map.get(6, locale, user_locale)}: {notes.completed_commissions}/{notes.max_commissions}\n"
            f"<:transformer:1004648470981902427> {text_map.get(8, locale, user_locale)}: {transformer_recover_time}"
        )
        result.add_field(
            name=f"<:resin:1004648472995168326> {text_map.get(4, locale, user_locale)}",
            value=f"{text_map.get(303, locale, user_locale)}: {notes.current_resin}/{notes.max_resin}\n"
            f"{text_map.get(15, locale, user_locale)}: {resin_recover_time}\n"
            f"{text_map.get(5, locale, user_locale)}: {notes.remaining_resin_discounts}/3",
            inline=False,
        )
        result.add_field(
            name=f"<:realm:1004648474266062880> {text_map.get(17, locale, user_locale)}",
            value=f" {text_map.get(2, locale, user_locale)}: {notes.current_realm_currency}/{notes.max_realm_currency}\n"
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

    @genshin_error_handler
    async def get_stats(
        self, user_id: int, namecard: str, avatar_url: str, locale: Locale
    ) -> Tuple[Embed | Dict, bool]:
        shenhe_user = await self.get_user_cookie(user_id, locale)
        uid = shenhe_user.uid
        embed = default_embed()
        embed.set_image(url="attachment://stat_card.jpeg")
        fp = self.bot.stats_card_cache.get(uid)
        if fp is None:
            genshin_user = await shenhe_user.client.get_partial_genshin_user(uid)
            ambr = AmbrTopAPI(self.bot.session)
            characters = await ambr.get_character(
                include_beta=False, include_traveler=False
            )

            mode = await get_user_appearance_mode(user_id, self.db)
            fp = await draw_stats_card(
                genshin_user.stats,
                namecard,
                avatar_url,
                len(characters) + 2,
                mode,
                self.bot.session,
            )
            self.bot.stats_card_cache[uid] = fp
        return {"embed": embed, "fp": fp}, True

    @genshin_error_handler
    async def get_area(self, user_id: int, locale: Locale):
        shenhe_user = await self.get_user_cookie(user_id, locale)
        uid = shenhe_user.uid
        embed = default_embed()
        embed.set_author(
            name=text_map.get(58, locale, shenhe_user.user_locale),
            icon_url=shenhe_user.discord_user.display_avatar.url,
        )
        embed.set_image(url="attachment://area.jpeg")
        genshin_user = await shenhe_user.client.get_partial_genshin_user(uid)
        explorations = genshin_user.explorations
        fp = self.bot.area_card_cache.get(uid)
        if fp is not None:
            pass
        else:
            mode = await get_user_appearance_mode(user_id, self.db)
            if fp is None:
                fp = await draw_area_card(explorations, mode)
            result = {
                "embed": embed,
                "image": fp,
            }
        return (
            result,
            True,
        )

    @genshin_error_handler
    async def get_diary(self, user_id: int, month: int, locale: Locale):
        shenhe_user = await self.get_user_cookie(user_id, locale)
        diary = await shenhe_user.client.get_diary(month=month)
        user = await shenhe_user.client.get_partial_genshin_user(shenhe_user.uid)
        result = {}
        embed = default_embed()
        fp = await draw_diary_card(
            diary,
            user,
            shenhe_user.user_locale or locale,
            await get_user_appearance_mode(user_id, self.db),
            month,
        )
        fp.seek(0)
        embed.set_image(url="attachment://diary.jpeg")
        embed.set_author(
            name=f"{text_map.get(69, locale, shenhe_user.user_locale)} • {get_month_name(month, locale, shenhe_user.user_locale)}",
            icon_url=shenhe_user.discord_user.display_avatar.url,
        )
        embed.set_footer(text=text_map.get(639, locale, shenhe_user.user_locale))
        result["embed"] = embed
        result["fp"] = fp
        return result, True

    @genshin_error_handler
    async def get_diary_logs(self, user_id: int, primo: bool, locale: Locale):
        shenhe_user = await self.get_user_cookie(user_id, locale)
        if primo:
            primo_log = ""
            async for action in shenhe_user.client.diary_log(limit=30):
                primo_log = (
                    primo_log
                    + f"{action.action} - {action.amount} {text_map.get(71, locale, shenhe_user.user_locale)}"
                    + "\n"
                )
            embed = default_embed(message=f"{primo_log}")
            embed.set_author(
                name=text_map.get(70, locale, shenhe_user.user_locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            )
        else:
            mora_log = ""
            async for action in shenhe_user.client.diary_log(
                limit=30, type=genshin.models.DiaryType.MORA
            ):
                mora_log = (
                    mora_log
                    + f"{action.action} - {action.amount} {text_map.get(73, locale, shenhe_user.user_locale)}"
                    + "\n"
                )
            embed = default_embed(message=f"{mora_log}")
            embed.set_author(
                name=text_map.get(72, locale, shenhe_user.user_locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            )
        return embed

    @genshin_error_handler
    async def get_abyss(self, user_id: int, previous: bool, locale: Locale):
        shenhe_user = await self.get_user_cookie(user_id, locale)
        user = await shenhe_user.client.get_partial_genshin_user(shenhe_user.uid)
        abyss = await shenhe_user.client.get_genshin_spiral_abyss(
            shenhe_user.uid, previous=previous
        )
        locale = shenhe_user.user_locale or locale
        if not abyss.ranks.most_kills:
            embed = error_embed(
                message=f"{text_map.get(74, locale)}\n{text_map.get(75, locale)}"
            )
            embed.set_author(
                name=text_map.get(76, locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            )
            return embed, False
        result = {}
        result["abyss"] = abyss
        result["user"] = user
        overview = default_embed()
        overview.set_image(url="attachment://overview_card.jpeg")
        overview.set_author(
            name=f"{text_map.get(85, locale)} | {text_map.get(77, locale)} {abyss.season}",
            icon_url=shenhe_user.discord_user.display_avatar.url,
        )
        result["title"] = f"{text_map.get(47, locale)} | {text_map.get(77, locale)} {abyss.season}"
        result["overview"] = overview
        locale = shenhe_user.user_locale or locale
        dark_mode = await get_user_appearance_mode(user_id, self.db)
        fp = await draw_abyss_overview_card(
            locale, dark_mode, abyss, user, self.bot.session
        )
        result["overview_card"] = fp
        result["floors"] = abyss.floors
        return result, True

    @genshin_error_handler
    async def get_all_characters(self, user_id: int, locale: Locale):
        shenhe_user = await self.get_user_cookie(user_id, locale)
        characters = await shenhe_user.client.get_genshin_characters(shenhe_user.uid)
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
                    label=f"{get_element_name(element, locale, shenhe_user.user_locale)} {text_map.get(45, locale, shenhe_user.user_locale)}",
                    value=index,
                )
            )
            message = ""
            for character in characters:
                message += f'{get_character(character.id)["emoji"]} {character.name} | Lvl. {character.level} | C{character.constellation}R{character.weapon.refinement}\n\n'
            embed = default_embed(
                f"{element_emojis.get(element)} {get_element_name(element, locale, shenhe_user.user_locale)} {text_map.get(45, locale, shenhe_user.user_locale)}",
                message,
            ).set_author(
                name=text_map.get(105, locale, shenhe_user.user_locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            )
            result["embeds"].append(embed)
            index += 1
        return result, True

    @genshin_error_handler
    async def redeem_code(self, user_id: int, code: str, locale: Locale):
        shenhe_user = await self.get_user_cookie(user_id, locale)
        try:
            await shenhe_user.client.redeem_code(code)
        except genshin.errors.RedemptionClaimed:
            return (
                error_embed().set_author(
                    name=text_map.get(45, locale, shenhe_user.user_locale),
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

    @genshin_error_handler
    async def get_activities(self, user_id: int, locale: Locale):
        shenhe_user = await self.get_user_cookie(user_id, locale)
        uid = shenhe_user.uid
        activities = await shenhe_user.client.get_genshin_activities(uid)
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
            summer,
            shenhe_user.discord_user,
            locale,
            shenhe_user.user_locale,
        )
        return result, True

    async def parse_summer_embed(
        self,
        summer: genshin.models.Summer,
        user: User,
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
                    else f"{seconds}{text_map.get(12, locale, user_locale)}"
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
        return embeds

    async def get_user_uid(self, user_id: int) -> int | None:
        uid = await get_uid(user_id, self.db)
        return uid

    async def get_user_cookie(self, user_id: int, locale: Locale = None) -> ShenheUser:
        shenhe_user = await get_shenhe_user(user_id, self.db, self.bot, locale)
        return shenhe_user
