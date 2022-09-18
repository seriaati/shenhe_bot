from typing import Dict, Literal, Tuple
import discord
import aiosqlite
import sentry_sdk
from apps.genshin.custom_model import ShenheUser
from apps.genshin.utils import get_character
from apps.text_map.convert_locale import to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_element_name, get_month_name, get_user_locale
from data.game.elements import element_emojis
from discord import Embed, Locale, SelectOption, User
from discord.ext import commands
from discord.utils import format_dt
from utility.utils import default_embed, error_embed, get_user_appearance_mode, log
from yelan.draw import draw_abyss_overview_card, draw_area_card, draw_stats_card

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
        user_locale = await get_user_locale(user_id, genshin_app.bot.db)
        locale = user_locale or locale
        try:
            return await func(*args, **kwargs)
        except genshin.errors.DataNotPublic:
            embed = error_embed(message=text_map.get(21, locale))
            embed.set_author(
                name=text_map.get(22, locale),
                icon_url=user.display_avatar.url,
            )
            return embed, False
        except genshin.errors.InvalidCookies:
            embed = error_embed(message=text_map.get(35, locale))
            embed.set_author(
                name=text_map.get(36, locale),
                icon_url=user.display_avatar.url,
            )
            return embed, False
        except Exception as e:
            log.warning(f"[Genshin App] Error in {func.__name__}: {e}")
            sentry_sdk.capture_exception(e)
            embed = error_embed(message=text_map.get(513, locale, user_locale))
            embed.set_author(
                name=text_map.get(135, locale), icon_url=user.display_avatar.url
            )
            embed.set_thumbnail(url="https://i.imgur.com/4XVfK4h.png")
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
        user = self.bot.get_user(user_id)
        if user is None:
            user = await self.bot.fetch_user(user_id)
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
            transformer_recover_time = text_map.get(10, locale, user_locale)
        else:
            if notes.remaining_transformer_recovery_time.total_seconds() <= 0:
                transformer_recover_time = text_map.get(9, locale, user_locale)
            else:
                transformer_recover_time = format_dt(
                    notes.transformer_recovery_time, "R"
                )
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

    @genshin_error_handler
    async def get_stats(
        self, user_id: int, namecard: str, avatar_url: str, locale: Locale
    ) -> Tuple[Embed | Dict, bool]:
        shenhe_user = await self.get_user_cookie(user_id, locale)
        uid = shenhe_user.uid
        embed = default_embed()
        embed.set_image(url="attachment://stat_card.jpeg")
        fp = self.bot.stats_card_cache.get(uid)
        if fp is not None:
            pass
        else:
            genshin_user = await shenhe_user.client.get_partial_genshin_user(uid)
            characters = await self.bot.genshin_client.get_calculator_characters(
                include_traveler=True
            )

            mode = await get_user_appearance_mode(user_id, self.db)
            fp = await draw_stats_card(
                genshin_user.stats,
                namecard,
                avatar_url,
                len(characters),
                mode,
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
            name=text_map.get(65, locale, shenhe_user.user_locale),
            value=msg,
            inline=False,
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
        abyss = await shenhe_user.client.get_spiral_abyss(
            shenhe_user.uid, previous=previous
        )
        locale = shenhe_user.user_locale or locale
        if not abyss.ranks.most_kills:
            embed = error_embed(message=f"{text_map.get(74, locale)}\n{text_map.get(75, locale)}")
            embed.set_author(name=text_map.get(76, locale), icon_url=shenhe_user.discord_user.display_avatar.url)
            return embed, False
        result = {}
        result['abyss'] = abyss
        overview = default_embed()
        overview.set_image(url="attachment://abyss.jpeg")
        result['overview'] = overview
        locale = shenhe_user.user_locale or locale
        dark_mode = await get_user_appearance_mode(user_id, self.db)
        fp = await draw_abyss_overview_card(locale, dark_mode, abyss)
        fp.seek(0)
        card = discord.File(fp, filename="abyss.jpeg")
        result['overview_card'] = card
        result['floors'] = []
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
            result['floors'].append(embed)

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

    @genshin_error_handler
    async def redeem_code(self, user_id: int, code: str, locale: Locale):
        shenhe_user = await self.get_user_cookie(user_id, locale)
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
        return embeds

    async def get_user_uid(self, user_id: int) -> int | None:
        c = await self.db.cursor()
        await c.execute(
            "SELECT uid FROM user_accounts WHERE user_id = ? AND current = 1",
            (user_id,),
        )
        uid = await c.fetchone()
        if uid is None:
            await c.execute(
                "SELECT uid FROM user_accounts WHERE user_id = ?",
                (user_id,),
            )
            uid = await c.fetchone()
            if uid is None:
                return None
            else:
                await c.execute(
                    "UPDATE user_accounts SET current = 1 WHERE user_id = ? AND uid = ?",
                    (user_id, uid[0]),
                )
                await self.db.commit()
        return uid[0]

    async def get_user_cookie(self, user_id: int, locale: Locale = None) -> ShenheUser:
        discord_user = self.bot.get_user(user_id)
        if discord_user is None:
            discord_user = await self.bot.fetch_user(user_id)
        c: aiosqlite.Cursor = await self.db.cursor()
        await c.execute(
            "SELECT ltuid, ltoken, cookie_token, uid, china FROM user_accounts WHERE user_id = ? AND current = 1",
            (user_id,),
        )
        user_data = await c.fetchone()
        if user_data is None:
            await c.execute(
                "SELECT ltuid, ltoken, cookie_token, uid, china FROM user_accounts WHERE user_id = ?",
                (user_id,),
            )
            user_data = await c.fetchone()
            if user_data is None:
                only_uid = True
            else:
                only_uid = False
                await c.execute('UPDATE user_accounts SET current = 1 WHERE user_id = ? AND uid = ?', (user_id, user_data[3]))
                await self.db.commit()
        else:
            only_uid = False
            
        if not only_uid:
            uid = user_data[3]
            client = genshin.Client()
            client.set_cookies(
                ltuid=user_data[0],
                ltoken=user_data[1],
                account_id=user_data[0],
                cookie_token=user_data[2],
            )
        else:
            client = self.bot.genshin_client
            uid = await self.get_user_uid(user_id)

        user_locale = await get_user_locale(user_id, self.db)
        genshin_locale = user_locale or locale
        client_locale = to_genshin_py(genshin_locale) or "en-us"
        client.lang = client_locale
        client.default_game = genshin.Game.GENSHIN
        client.uid = uid
        if uid is not None:
            china = True if int(str(uid)[0]) in [1, 2, 5] else False
        else:
            china = False
        if china:
            client.lang = 'zh-cn'

        try:
            await client.update_character_names(lang=client._lang)
        except genshin.errors.InvalidCookies:
            try:
                await self.bot.genshin_client.update_character_names(lang=client._lang)
            except Exception as e:
                sentry_sdk.capture_exception(e)

        user_obj = ShenheUser(
            client=client,
            uid=uid,
            discord_user=discord_user,
            user_locale=user_locale,
            china=china,
        )
        return user_obj
