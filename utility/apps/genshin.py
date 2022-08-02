import ast
from typing import Dict, List, Literal, Tuple, Union

import aiohttp
import aiosqlite
from data.game.elements import convert_elements
from discord import Embed, Locale, Member, SelectOption
from discord.ext import commands
from discord.utils import format_dt
from utility.apps.text_map.convert_locale import to_ambr_top, to_genshin_py
from utility.apps.text_map.TextMap import text_map
from utility.apps.text_map.utils import (get_element_name, get_month_name,
                                         get_user_locale)
from utility.utils import (default_embed, error_embed, get_dummy_client,
                           get_weekday_int_with_name, getAreaEmoji,
                           getCharacter, getElement, getWeapon, log,
                           trim_cookie)

import genshin


class GenshinApp:
    def __init__(self, db: aiosqlite.Connection, bot: commands.Bot) -> None:
        self.db = db
        self.bot = bot

    async def setCookie(self, user_id: int, cookie: str, locale: Locale, uid: int = None):
        log(False, False, 'setCookie', f'{user_id} ({cookie})')
        user = self.bot.get_user(user_id)
        user_locale = await get_user_locale(user_id, self.db)
        user_id = int(user_id)
        cookie = trim_cookie(cookie)
        if cookie is None:
            result = error_embed(
                message=text_map.get(35, locale, user_locale)).set_author(name=text_map.get(36, locale, user_locale), icon_url=user.avatar)
            return result, False
        client = genshin.Client()
        user_locale = user_locale or locale
        client.lang = to_genshin_py(user_locale)
        client.set_cookies(
            ltuid=cookie[0], ltoken=cookie[1], account_id=cookie[0], cookie_token=cookie[2])
        accounts = await client.get_game_accounts()
        if uid is None:
            if len(accounts) == 0:
                result = error_embed(message=text_map.get(37, locale, user_locale)).set_author(
                    name=text_map.get(38, locale, user_locale), icon_url=user.avatar)
                return result, False
            elif len(accounts) == 1:
                uid = accounts[0].uid
            else:
                account_options = []
                for account in accounts:
                    account_options.append(SelectOption(
                        label=f'{account.uid} | Lvl. {account.level} | {account.nickname}', value=account.uid))
                return account_options, True
        c = await self.db.cursor()
        await c.execute('INSERT INTO genshin_accounts (user_id, ltuid, ltoken, cookie_token, uid) VALUES (?, ?, ?, ?, ?) ON CONFLICT (user_id) DO UPDATE SET ltuid = ?, ltoken = ?, cookie_token = ?, uid = ? WHERE user_id = ?', (user_id, cookie[0], cookie[1], cookie[2], uid, cookie[0], cookie[1], cookie[2], uid, user_id))
        result = default_embed().set_author(name=text_map.get(
            39, locale, user_locale), icon_url=user.avatar)
        await self.db.commit()
        log(True, False, 'setCookie', f'{user_id} setCookie success')
        return result, True

    async def claimDailyReward(self, user_id: int, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            reward = await client.claim_daily_reward()
        except genshin.errors.AlreadyClaimed:
            return error_embed().set_author(name=text_map.get(40, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return error_embed(message=f'```{e}```').set_author(name=text_map.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            return default_embed(message=f'{text_map.get(41, locale, user_locale)} {reward.amount}x {reward.name}').set_author(name=text_map.get(42, locale, user_locale), icon_url=user.avatar), True

    async def getRealTimeNotes(self, user_id: int, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            notes = await client.get_notes(uid)
        except genshin.errors.DataNotPublic:
            return error_embed(message=text_map.get(21, locale, user_locale)).set_author(name=text_map.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return error_embed(message=f'```{e}```').set_author(name=text_map.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            return self.parseResinEmbed(notes, locale, user_locale).set_author(name=text_map.get(24, locale, user_locale), icon_url=user.avatar), True

    def parseResinEmbed(self, notes: genshin.models.Notes, locale: Locale, user_locale: str) -> Embed:
        if notes.current_resin == notes.max_resin:
            resin_recover_time = text_map.get(1, locale, user_locale)
        else:
            resin_recover_time = format_dt(notes.resin_recovery_time, 'R')

        if notes.current_realm_currency == notes.max_realm_currency:
            realm_recover_time = text_map.get(1, locale, user_locale)
        else:
            realm_recover_time = format_dt(
                notes.realm_currency_recovery_time, 'R')

        if notes.transformer_recovery_time != None:
            transformer_recover_time = format_dt(
                notes.transformer_recovery_time, 'R')
        else:
            transformer_recover_time = text_map.get(10, locale, user_locale)
        result = default_embed(
            f"",
            f"<:daily:956383830070140938> {text_map.get(11, locale, user_locale)}: {notes.completed_commissions}/{notes.max_commissions}\n"
            f"<:transformer:966156330089971732> {text_map.get(12, locale, user_locale)}: {transformer_recover_time}"
        )
        result.add_field(
            name=f'<:resin:956377956115157022> {text_map.get(13, locale, user_locale)}',
            value=f"{text_map.get(14, locale, user_locale)}: {notes.current_resin}/{notes.max_resin}\n"
            f"{text_map.get(15, locale, user_locale)}: {resin_recover_time}\n"
            f'{text_map.get(16, locale, user_locale)}: {notes.remaining_resin_discounts}/3',
            inline=False
        )
        result.add_field(
            name=f'<:realm:956384011750613112> {text_map.get(17, locale, user_locale)}',
            value=f" {text_map.get(14, locale, user_locale)}: {notes.current_realm_currency}/{notes.max_realm_currency}\n"
            f'{text_map.get(15, locale, user_locale)}: {realm_recover_time}',
            inline=False
        )
        exped_finished = 0
        exped_msg = ''
        total_exped = len(notes.expeditions)
        if not notes.expeditions:
            exped_msg = text_map.get(18, locale, user_locale)
        for expedition in notes.expeditions:
            exped_msg += f'• {expedition.character.name}'
            if expedition.finished:
                exped_finished += 1
                exped_msg += f': {text_map.get(19, locale, user_locale)}\n'
            else:
                exped_msg += f': {format_dt(expedition.completion_time, "R")}\n'
        result.add_field(
            name=f'<:ADVENTURERS_GUILD:998780550615679086> {text_map.get(20, locale, user_locale)} ({exped_finished}/{total_exped})',
            value=exped_msg,
            inline=False
        )
        return result

    async def getUserStats(self, user_id: int, custom_uid: Literal["int", None], locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        uid = custom_uid or uid
        try:
            genshinUser = await client.get_partial_genshin_user(uid)
        except genshin.errors.DataNotPublic:
            return error_embed(message=text_map.get(21, locale, user_locale)).set_author(name=text_map.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return error_embed(message=f'```{e}```').set_author(name=text_map.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            characters = await client.get_calculator_characters()
            result = default_embed()
            result.add_field(
                name=text_map.get(43, locale, user_locale),
                value=f"📅 {text_map.get(44, locale, user_locale)}: {genshinUser.stats.days_active}\n"
                f"<:expedition:956385168757780631> {text_map.get(45, locale, user_locale)}: {genshinUser.stats.characters}/{len(characters)}\n"
                f"📜 {text_map.get(46, locale, user_locale)}: {genshinUser.stats.achievements}\n"
                f"🌙 {text_map.get(47, locale, user_locale)}: {genshinUser.stats.spiral_abyss}",
                inline=False)
            result.add_field(
                name=text_map.get(48, locale, user_locale),
                value=f"<:anemo:956719995906322472> {text_map.get(49, locale, user_locale)}: {genshinUser.stats.anemoculi}/66\n"
                f"<:geo:956719995440730143> {text_map.get(50, locale, user_locale)}: {genshinUser.stats.geoculi}/131\n"
                f"<:electro:956719996262821928> {text_map.get(51, locale, user_locale)}: {genshinUser.stats.electroculi}/181",
                inline=False)
            result.add_field(
                name=text_map.get(52, locale, user_locale),
                value=f"{text_map.get(53, locale, user_locale)}: {genshinUser.stats.common_chests}\n"
                f"{text_map.get(54, locale, user_locale)}: {genshinUser.stats.exquisite_chests}\n"
                f"{text_map.get(57, locale, user_locale)}: {genshinUser.stats.precious_chests}\n"
                f"{text_map.get(55, locale, user_locale)}: {genshinUser.stats.luxurious_chests}",
                inline=False)
            result.set_author(name=text_map.get(
                56, locale, user_locale), icon_url=user.avatar)
            if custom_uid is not None:
                result.set_footer(
                    text=f'{text_map.get(123, locale, user_locale)}: {custom_uid}')
            return result, True

    async def getArea(self, user_id: int, custom_uid: Literal["int", None], locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        uid = custom_uid or uid
        try:
            genshinUser = await client.get_partial_genshin_user(uid)
        except genshin.errors.DataNotPublic:
            return error_embed(message=text_map.get(21, locale, user_locale)).set_author(name=text_map.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return error_embed(message=f'```{e}```').set_author(name=text_map.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            explorations = genshinUser.explorations
            explore_str = ""
            for exploration in reversed(explorations):
                level_str = "" if exploration.id == 5 or exploration.id == 6 else f"Lvl. {exploration.offerings[0].level}"
                emoji = getAreaEmoji(exploration.id)
                explore_str += f"{emoji} {exploration.name} | {exploration.explored}% | {level_str}\n"
            result = default_embed(message=explore_str)
        return result.set_author(name=text_map.get(58, locale, user_locale), icon_url=user.avatar), True

    async def getDiary(self, user_id: int, month: int, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            diary = await client.get_diary(month=month)
        except genshin.errors.DataNotPublic:
            return error_embed(message=text_map.get(21, locale, user_locale)).set_author(name=text_map.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return error_embed(message=f'```{e}```').set_author(name=text_map.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            d = diary.data
            result = default_embed(
                message=f'{text_map.get(59, locale, user_locale)} {text_map.get(60, locale, user_locale) if d.primogems_rate > 0 else text_map.get(61, locale, user_locale)} {abs(d.primogems_rate)}%\n'
                f'{text_map.get(62, locale, user_locale)} {text_map.get(60, locale, user_locale) if d.mora_rate > 0 else text_map.get(61, locale, user_locale)} {abs(d.mora_rate)}%'
            )
            result.add_field(
                name=text_map.get(63, locale, user_locale),
                value=f'<:primo:958555698596290570> {d.current_primogems} ({int(d.current_primogems/160)} <:pink_ball:984652245851316254>) • {text_map.get(64, locale, user_locale)}: {d.last_primogems} ({int(d.last_primogems/160)} <:pink_ball:984652245851316254>)\n'
                f'<:mora:958577933650362468> {d.current_mora} • {text_map.get(64, locale, user_locale)}: {d.last_mora}',
                inline=False
            )
            msg = ''
            for cat in d.categories:
                msg += f'{cat.name}: {cat.percentage}%\n'
            result.add_field(name=text_map.get(
                65, locale, user_locale), value=msg, inline=False)
            result.add_field(
                name=text_map.get(66, locale, user_locale),
                value=f'{text_map.get(67, locale, user_locale)}\n{text_map.get(68, locale, user_locale)}',
                inline=False
            )
            result.set_author(
                name=f'{text_map.get(69, locale, user_locale)} • {get_month_name(month, locale, user_locale)}', icon_url=user.avatar)
            return result, True

    async def getDiaryLog(self, user_id: int, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            diary = await client.get_diary()
        except genshin.errors.DataNotPublic as e:
            return error_embed(message=text_map.get(21, locale, user_locale)).set_author(name=text_map.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return error_embed(message=f'```{e}```').set_author(name=text_map.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            primoLog = ''
            result = []
            async for action in client.diary_log(limit=30):
                primoLog = primoLog + \
                    f"{action.action} - {action.amount} {text_map.get(71, locale, user_locale)}"+"\n"
            embed = default_embed(message=f"{primoLog}")
            embed.set_author(name=text_map.get(
                70, locale, user_locale), icon_url=user.avatar)
            result.append(embed)
            moraLog = ''
            async for action in client.diary_log(limit=30, type=genshin.models.DiaryType.MORA):
                moraLog = moraLog + \
                    f"{action.action} - {action.amount} {text_map.get(73, locale, user_locale)}"+"\n"
            embed = default_embed(message=f"{moraLog}")
            embed.set_author(name=text_map.get(
                72, locale, user_locale), icon_url=user.avatar)
            result.append(embed)
        return result, True

    async def getAbyss(self, user_id: int, previous: bool, overview: bool, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            abyss = await client.get_spiral_abyss(uid, previous=previous)
        except genshin.errors.DataNotPublic:
            return error_embed(message=text_map.get(21, locale, user_locale)).set_author(name=text_map.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return error_embed(message=f'```{e}```').set_author(name=text_map.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            rank = abyss.ranks
            if len(rank.most_kills) == 0:
                result = error_embed(message=f'{text_map.get(74, locale, user_locale)}\n'
                                     f'{text_map.get(75, locale, user_locale)}')
                result.set_author(name=text_map.get(
                    76, locale, user_locale), icon_url=user.avatar)
                return result, False
            result = default_embed(
                f"{text_map.get(77, locale, user_locale)} {abyss.season}",
                f"{text_map.get(78, locale, user_locale)} {abyss.max_floor}\n"
                f"✦ {abyss.total_stars}"
            )
            result.add_field(
                name=text_map.get(79, locale, user_locale),
                value=f"{getCharacter(rank.strongest_strike[0].id)['emoji']} {text_map.get(80, locale, user_locale)}: {rank.strongest_strike[0].value}\n"
                f"{getCharacter(rank.most_kills[0].id)['emoji']} {text_map.get(81, locale, user_locale)}: {rank.most_kills[0].value}\n"
                f"{getCharacter(rank.most_damage_taken[0].id)['emoji']} {text_map.get(82, locale, user_locale)}: {rank.most_damage_taken[0].value}\n"
                f"{getCharacter(rank.most_bursts_used[0].id)['emoji']} {text_map.get(83, locale, user_locale)}: {rank.most_bursts_used[0].value}\n"
                f"{getCharacter(rank.most_skills_used[0].id)['emoji']} {text_map.get(84, locale, user_locale)}: {rank.most_skills_used[0].value}"
            )
            result.set_author(name=text_map.get(
                85, locale, user_locale), icon_url=user.avatar)
            if overview:
                return result, True
            result = []
            for floor in abyss.floors:
                embed = default_embed().set_author(
                    name=f"{text_map.get(146, locale, user_locale)} {floor.floor} {text_map.get(147, locale, user_locale)} (✦ {floor.stars}/9)")
                for chamber in floor.chambers:
                    name = f'{text_map.get(86, locale, user_locale)} {chamber.chamber} {text_map.get(87, locale, user_locale)} ✦ {chamber.stars}'
                    chara_list = [[], []]
                    for i, battle in enumerate(chamber.battles):
                        for chara in battle.characters:
                            chara_list[i].append(
                                f"{getCharacter(chara.id)['emoji']} **{chara.name}**")
                    topStr = ''
                    bottomStr = ''
                    for top_char in chara_list[0]:
                        topStr += f"| {top_char} "
                    for bottom_char in chara_list[1]:
                        bottomStr += f"| {bottom_char} "
                    embed.add_field(
                        name=name,
                        value=f"{text_map.get(88, locale, user_locale)} {topStr}\n\n"
                        f"{text_map.get(89, locale, user_locale)} {bottomStr}",
                        inline=False
                    )
                result.append(embed)
            return result, True

    async def setResinNotification(self, user_id: int, resin_notification_toggle: int, resin_threshold: int, max_notif: int, locale: Locale):
        c: aiosqlite.Cursor = await self.db.cursor()
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            await client.get_notes(uid)
        except genshin.errors.DataNotPublic:
            return error_embed(message=text_map.get(21, locale, user_locale)).set_author(name=text_map.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return error_embed(message=f'```{e}```').set_author(name=text_map.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            if resin_notification_toggle == 0:
                await c.execute('UPDATE genshin_accounts SET resin_notification_toggle = 0 WHERE user_id = ?', (user_id,))
                result = default_embed().set_author(name=text_map.get(
                    98, locale, user_locale), icon_url=user.avatar)
            else:
                await c.execute('UPDATE genshin_accounts SET resin_notification_toggle = ?, resin_threshold = ? , max_notif = ? WHERE user_id = ?', (resin_notification_toggle, resin_threshold, max_notif, user_id))
                toggle_str = text_map.get(
                    99, locale, user_locale) if resin_notification_toggle == 1 else text_map.get(100, locale, user_locale)
                result = default_embed(
                    message=f'{text_map.get(101, locale, user_locale)}: {toggle_str}\n'
                    f'{text_map.get(102, locale, user_locale)}: {resin_threshold}\n'
                    f'{text_map.get(103, locale, user_locale)}: {max_notif}'
                )
                result.set_author(name=text_map.get(
                    104, locale, user_locale), icon_url=user.avatar)
            await self.db.commit()
        return result, True

    async def getUserCharacters(self, user_id: int, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            characters = await client.get_genshin_characters(uid)
        except genshin.errors.DataNotPublic:
            return error_embed(message=text_map.get(21, locale, user_locale)).set_author(name=text_map.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return error_embed(message=f'```{e}```').set_author(name=text_map.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            # organize characters according to elements
            result = {'embeds': [], 'options': []}
            organized_characters = {}
            for character in characters:
                if character.element not in organized_characters:
                    organized_characters[character.element] = []
                organized_characters[character.element].append(character)

            index = 0
            for element, characters in organized_characters.items():
                result['options'].append(SelectOption(emoji=getElement(
                    element)['emoji'], label=f'{get_element_name(element, locale, user_locale)} {text_map.get(220, locale, user_locale)}', value=index))
                message = ''
                for character in characters:
                    message += f'{getCharacter(character.id)["emoji"]} {character.name} | Lvl. {character.level} | C{character.constellation}R{character.weapon.refinement}\n\n'
                embed = default_embed(f'{getElement(element)["emoji"]} {get_element_name(element, locale, user_locale)} {text_map.get(220, locale, user_locale)}', message).set_author(
                    name=text_map.get(105, locale, user_locale), icon_url=user.avatar)
                result['embeds'].append(embed)
                index += 1
            return result, True

    async def redeemCode(self, user_id: int, code: str, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            await client.redeem_code(code)
        except genshin.errors.RedemptionClaimed:
            return error_embed().set_author(name=text_map.get(106, locale, user_locale), icon_url=user.avatar), False
        except genshin.errors.GenshinException:
            return error_embed().set_author(name=text_map.get(107, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return error_embed(message=f'```{e}```').set_author(name=text_map.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            return default_embed(message=f'{text_map.get(108, locale, user_locale)}: {code}').set_author(name=text_map.get(109, locale, user_locale), icon_url=user.avatar), True

    async def getActivities(self, user_id: int, custom_uid: int, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        uid = custom_uid or uid
        try:
            activities = await client.get_genshin_activities(uid)
        except genshin.errors.DataNotPublic:
            return error_embed(message=text_map.get(21, locale, user_locale)).set_author(name=text_map.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return error_embed(message=f'```{e}```').set_author(name=text_map.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            summer = activities.summertime_odyssey
            if summer is None:
                return error_embed().set_author(name=text_map.get(110, locale, user_locale), icon_url=user.avatar), False
            result = await self.parseSummerEmbed(summer, user, custom_uid, locale, user_locale)
            return result, True

    async def parseSummerEmbed(self, summer: genshin.models.Summer, user: Member, custom_uid: int, locale: Locale, user_locale: Literal["str", None]) -> list[Embed]:
        embeds = []
        embed = default_embed().set_author(name=text_map.get(
            111, locale, user_locale), icon_url=user.avatar)
        embed.add_field(
            name=f'<:SCORE:983948729293897779> {text_map.get(43, locale, user_locale)}',
            value=f'{text_map.get(112, locale, user_locale)}: {summer.waverider_waypoints}/13\n'
            f'{text_map.get(113, locale, user_locale)}: {summer.waypoints}/10\n'
            f'{text_map.get(114, locale, user_locale)}: {summer.treasure_chests}'
        )
        embed.set_image(url='https://i.imgur.com/Zk1tqxA.png')
        embeds.append(embed)
        embed = default_embed().set_author(name=text_map.get(
            111, locale, user_locale), icon_url=user.avatar)
        surfs = summer.surfpiercer
        value = ''
        for surf in surfs:
            if surf.finished:
                minutes, seconds = divmod(surf.time, 60)
                time_str = f'{minutes} {text_map.get(7, locale, user_locale)} {seconds} {text_map.get(8, locale, user_locale)}' if minutes != 0 else f'{seconds}{text_map.get(8, locale, user_locale)}'
                value += f'{surf.id}. {time_str}\n'
            else:
                value += f'{surf.id}. *{text_map.get(115, locale, user_locale)}* \n'
        embed.add_field(
            name=text_map.get(116, locale, user_locale),
            value=value
        )
        embed.set_thumbnail(url='https://i.imgur.com/Qt4Tez0.png')
        embeds.append(embed)
        memories = summer.memories
        for memory in memories:
            embed = default_embed().set_author(name=text_map.get(
                117, locale, user_locale), icon_url=user.avatar)
            embed.set_thumbnail(url='https://i.imgur.com/yAbpUF8.png')
            embed.set_image(url=memory.icon)
            embed.add_field(name=memory.name,
                            value=f'{text_map.get(119, locale, user_locale)}: {memory.finish_time}')
            embeds.append(embed)
        realms = summer.realm_exploration
        for realm in realms:
            embed = default_embed().set_author(name=text_map.get(
                118, locale, user_locale), icon_url=user.avatar)
            embed.set_thumbnail(url='https://i.imgur.com/0jyBciz.png')
            embed.set_image(url=realm.icon)
            embed.add_field(
                name=realm.name,
                value=f'{text_map.get(119, locale, user_locale)}: {realm.finish_time if realm.finished else text_map.get(115, locale, user_locale)}\n'
                f'{text_map.get(120, locale, user_locale)} {realm.success} {text_map.get(121, locale, user_locale)}\n'
                f'{text_map.get(122, locale, user_locale)} {realm.skills_used} {text_map.get(121, locale, user_locale)}'
            )
            embeds.append(embed)
        if custom_uid is not None:
            embed: Embed
            for embed in embeds:
                embed.set_footer(
                    text=f'{text_map.get(123, locale, user_locale)}: {custom_uid}')
        return embeds

    async def getUserCookie(self, user_id: int, locale: Locale = None):
        user = self.bot.get_user(user_id)
        c: aiosqlite.Cursor = await self.db.cursor()
        await c.execute('SELECT ltuid, ltoken, cookie_token, uid FROM genshin_accounts WHERE user_id = ?', (user_id,))
        user_data = await c.fetchone()
        if user_data is None:
            client = get_dummy_client()
            uid = None
        else:
            uid = user_data[3]
            client = genshin.Client()
            client.set_cookies(
                ltuid=user_data[0], ltoken=user_data[1], account_id=user_data[0], cookie_token=user_data[2])
            client.default_game = genshin.Game.GENSHIN
            client.uids[genshin.Game.GENSHIN] = uid
        locale = await get_user_locale(user_id, self.db) or locale
        client_locale = to_genshin_py(locale) or 'en-us'
        client.lang = client_locale
        await client.update_character_names(lang=client._lang)
        return client, uid, user, locale

    async def check_user_data(self, user_id: int):
        c: aiosqlite.Cursor = await self.db.cursor()
        await c.execute('SELECT * FROM genshin_accounts WHERE user_id = ?', (user_id,))
        user_data = await c.fetchone()
        if user_data is None:
            return False
        return True

    async def get_user_talent_notification_enabled_str(self, user_id: int, locale: Locale) -> str:
        c: aiosqlite.Cursor = await self.db.cursor()
        user_locale = await get_user_locale(user_id, self.db)
        await c.execute('SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?', (user_id,))
        character_list: list = ast.literal_eval((await c.fetchone())[0])
        enabled_characters_str = ''
        if len(character_list) == 0:
            enabled_characters_str = text_map.get(158, locale, user_locale)
        else:
            for character_id in character_list:
                enabled_characters_str += f'• {text_map.get_character_name(character_id, locale, user_locale)}\n'
        return enabled_characters_str


async def get_farm_dict(session: aiohttp.ClientSession, locale: str | Locale) -> dict:
    ambr_top_locale = to_ambr_top(locale)
    async with session.get(f'https://api.ambr.top/v2/{ambr_top_locale}/dailyDungeon?vh=28R6') as r:
        daily_dungeon = await r.json()
    async with session.get('https://api.ambr.top/v2/static/upgrade?vh=28R6') as r:
        upgrade = await r.json()
    upgrade = upgrade['data']
    daily_dungeon = daily_dungeon['data']

    # get a dict of rewards first
    rewards = {}
    for weekday, domains in daily_dungeon.items():
        for domain, domain_info in domains.items():
            for reward_id in domain_info['reward']:
                if len(str(reward_id)) == 6:  # exclude mora and other stuff
                    if str(reward_id) not in rewards:
                        rewards[str(reward_id)] = {
                            'domain_id': domain_info['id'], 'domain_city': domain_info['city'], 'weekday': []}
                    if get_weekday_int_with_name(weekday) not in rewards[str(reward_id)]['weekday']:
                        rewards[str(reward_id)]['weekday'].append(
                            get_weekday_int_with_name(weekday))

    result = {'avatar': {}, 'weapon': {}}

    # then, organize the rewards according to characters
    for avatar_id, avatar_info in upgrade['avatar'].items():
        if 'beta' in avatar_info:  # skip beta characters
            continue
        result['avatar'][avatar_id] = {}
        for item_id, item_rarity in avatar_info['items'].items():
            if avatar_id not in result['avatar']:
                result['avatar'][avatar_id] = {}
            if item_id in rewards:
                result['avatar'][avatar_id][item_id] = rewards[item_id]

    # as well as weapons
    for weapon_id, weapon_info in upgrade['weapon'].items():
        if 'beta' in weapon_info:  # skip beta weapons
            continue
        result['weapon'][weapon_id] = {}
        for item_id, item_rarity in weapon_info['items'].items():
            if item_id in rewards:
                result['weapon'][weapon_id][item_id] = rewards[item_id]

    # "15509": {
    #     "114029": {
    #         "domain_id": 4353,
    #         "domain_city": 3,
    #         "weekday": 6
    #     },
    #     "114030": {
    #         "domain_id": 4353,
    #         "domain_city": 3,
    #         "weekday": 6
    #     }
    # }

    return result, daily_dungeon


async def get_all_non_beta_characters(session: aiohttp.ClientSession, locale: Literal['Locale', 'str']) -> dict:
    """Returns all genshin non-beta characters in the given ambr.top locale, elements are converted (i.e. from ice to cryo)

    Args:
        session (aiohttp.ClientSession): the aiohttp session
        locale (Literal['Locale', 'str']): the ambr.top locale
        user_locale (str): used to override the default locale if needed

    Returns:
        dict: a dict of all characters with their rarity, element, and name (from the textMap using the given locale)
    """

    ambr_top_locale = to_ambr_top(locale)
    async with session.get(f'https://api.ambr.top/v2/{ambr_top_locale}/avatar') as r:
        avatars = await r.json()
    avatars = avatars['data']['items']

    result = {}
    for avatar_id, avatar_info in avatars.items():
        result[avatar_id] = {
            'rank': avatar_info['rank'], 'element': convert_elements.get(avatar_info['element']),
            'name': text_map.get_character_name(avatar_id, locale)
        }

    return result


def get_character_builds(character_id: int, element_builds_dict: dict, locale: Locale, user_locale: str) -> Tuple[List[Union[Embed, str, str]], bool]:
    """Gets a character's builds

    Args:
        character_id (int): the id of the character
        element_builds_dict (dict): the dictionary of all characters of a given element, this is stored in data/builds
        locale (Locale): the discord locale 
        user_locale (str): the user locale

    Returns:
        Tuple[List[Embed], bool]: returns a list of lists of embeds, weapons, and artifacts of different builds + a boolean that indicates whether the character has artifact thoughts
    """
    character_name = text_map.get_character_name(character_id, 'zh-TW', None)
    translated_character_name = text_map.get_character_name(
        character_id, locale, user_locale)
    count = 1
    has_thoughts = False
    result = []

    for build in element_builds_dict[character_name]['builds']:
        statStr = ''
        for stat, value in build['stats'].items():
            statStr += f'{stat} ➜ {value}\n'
        embed = default_embed(
            f'{translated_character_name} - {text_map.get(90, locale, user_locale)}{count}',
            f"{text_map.get(91, locale, user_locale)} • {getWeapon(name=build['weapon'])['emoji']} {build['weapon']}\n"
            f"{text_map.get(92, locale, user_locale)} • {build['artifacts']}\n"
            f"{text_map.get(93, locale, user_locale)} • {build['main_stats']}\n"
            f"{text_map.get(94, locale, user_locale)} • {build['talents']}\n"
            f"{build['move']} • {build['dmg']}\n\n"
        )
        embed.add_field(
            name=text_map.get(95, locale, user_locale),
            value=statStr
        )
        count += 1
        embed.set_thumbnail(
            url=getCharacter(character_id)["icon"])
        embed.set_footer(
            text=f'[{text_map.get(96, locale, user_locale)}](https://bbs.nga.cn/read.php?tid=25843014)')
        result.append([embed, build['weapon'], build['artifacts']])

    if 'thoughts' in element_builds_dict[character_name]:
        has_thoughts = True
        count = 1
        embed = default_embed(text_map.get(97, locale, user_locale))
        for thought in element_builds_dict[character_name]['thoughts']:
            embed.add_field(name=f'#{count}',
                            value=thought, inline=False)
            count += 1
        embed.set_thumbnail(
            url=getCharacter(character_id)["icon"])
        result.append([embed, text_map.get(97, locale, user_locale), ''])

    return result, has_thoughts


def check_level_validity(levels: Dict[str, str], locale: Literal['Locale', 'str']) -> Tuple[bool, str]:
    for level_type, level in levels.items():
        if not level.isnumeric():
            return False, text_map.get(187, locale)
        if (level_type == 'current' or level_type == 'target') and (int(level) > 90 or int(level) < 1):
            return False, text_map.get(188, locale)
        if (level_type == 'a' or level_type == 'e' or level_type == 'q') and (int(level) > 10 or int(level) < 1):
            return False, text_map.get(189, locale)
    return True, ''
