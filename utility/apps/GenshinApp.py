from datetime import datetime
from typing import Literal

import aiosqlite
import genshin
from data.textMap.dc_local_to_genshin_py import DLGP
from discord import Embed, Locale, Member, SelectOption
from discord.ext import commands
from utility.utils import (TextMap, defaultEmbed, errEmbed, getAreaEmoji,
                           getCharacter, getClient, getElement, getWeapon,
                           getWeekdayName, log, trimCookie)


class GenshinApp:
    def __init__(self, db: aiosqlite.Connection, bot: commands.Bot) -> None:
        self.db = db
        self.bot = bot
        self.textMap = TextMap(self.db)

    async def setCookie(self, user_id: int, cookie: str, locale: Locale, uid: int = None):
        log(False, False, 'setCookie', f'{user_id} ({cookie})')
        user = self.bot.get_user(user_id)
        user_locale = await self.textMap.getUserLocale(user_id)
        user_id = int(user_id)
        cookie = trimCookie(cookie)
        if cookie is None:
            result = errEmbed(
                message=self.textMap.get(35, locale, user_locale)).set_author(name=self.textMap.get(36, locale, user_locale), icon_url=user.avatar)
            return result, False
        client = genshin.Client()
        client.lang = user_locale or locale
        client.set_cookies(
            ltuid=cookie[0], ltoken=cookie[1], account_id=cookie[0], cookie_token=cookie[2])
        accounts = await client.get_game_accounts()
        if uid is None:
            if len(accounts) == 0:
                result = errEmbed(message=self.textMap.get(37, locale, user_locale)).set_author(
                    name=self.textMap.get(38, locale, user_locale), icon_url=user.avatar)
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
        result = defaultEmbed().set_author(name=self.textMap.get(
            39, locale, user_locale), icon_url=user.avatar)
        await self.db.commit()
        log(True, False, 'setCookie', f'{user_id} setCookie success')
        return result, True

    async def claimDailyReward(self, user_id: int, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            reward = await client.claim_daily_reward()
        except genshin.errors.AlreadyClaimed:
            return errEmbed().set_author(name=self.textMap.get(40, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(message=f'```{e}```').set_author(name=self.textMap.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            return defaultEmbed(message=f'{self.textMap.get(41, locale, user_locale)} {reward.amount}x {reward.name}').set_author(name=self.textMap.get(42, locale, user_locale), icon_url=user.avatar), True

    async def getRealTimeNotes(self, user_id: int, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            notes = await client.get_notes(uid)
        except genshin.errors.DataNotPublic:
            return errEmbed(message=self.textMap.get(21, locale, user_locale)).set_author(name=self.textMap.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(message=f'```{e}```').set_author(name=self.textMap.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            return self.parseResinEmbed(notes, locale, user_locale).set_author(name=self.textMap.get(24, locale, user_locale), icon_url=user.avatar), True

    def parseResinEmbed(self, notes, locale: Locale, user_locale: str) -> Embed:
        if notes.current_resin == notes.max_resin:
            resin_recover_time = self.textMap.get(1, locale, user_locale)
        else:
            day_msg = self.textMap.get(2, locale, user_locale) if notes.resin_recovery_time.day == datetime.now(
            ).day else self.textMap.get(3, locale, user_locale)
            resin_recover_time = f'{day_msg} {notes.resin_recovery_time.strftime("%H:%M")}'

        if notes.current_realm_currency == notes.max_realm_currency:
            realm_recover_time = self.textMap.get(1, locale, user_locale)
        else:
            weekday_msg = getWeekdayName(
                notes.realm_currency_recovery_time.weekday(), self.textMap, locale, user_locale)
            realm_recover_time = f'{weekday_msg} {notes.realm_currency_recovery_time.strftime("%H:%M")}'
        if notes.transformer_recovery_time != None:
            t = notes.remaining_transformer_recovery_time
            if t.days > 0:
                recover_time = f'{t.days} {self.textMap.get(5, locale, user_locale)}'
            elif t.hours > 0:
                recover_time = f'{t.hours} {self.textMap.get(6, locale, user_locale)}'
            elif t.minutes > 0:
                recover_time = f'{t.minutes} {self.textMap.get(7, locale, user_locale)}'
            elif t.seconds > 0:
                recover_time = f'{t.seconds} {self.textMap.get(8, locale, user_locale)}'
            else:
                recover_time = f'{self.textMap.get(9, locale, user_locale)}'
        else:
            recover_time = self.textMap.get(10, locale, user_locale)
        result = defaultEmbed(
            f"",
            f"<:daily:956383830070140938> {self.textMap.get(11, locale, user_locale)}: {notes.completed_commissions}/{notes.max_commissions}\n"
            f"<:transformer:966156330089971732> {self.textMap.get(12, locale, user_locale)}: {recover_time}"
        )
        result.add_field(
            name=f'<:resin:956377956115157022> {self.textMap.get(13, locale, user_locale)}',
            value=f" {self.textMap.get(14, locale, user_locale)}: {notes.current_resin}/{notes.max_resin}\n"
            f"{self.textMap.get(15, locale, user_locale)} {resin_recover_time}\n"
            f'{self.textMap.get(16, locale, user_locale)}: {notes.remaining_resin_discounts}/3',
            inline=False
        )
        result.add_field(
            name=f'<:realm:956384011750613112> {self.textMap.get(17, locale, user_locale)}',
            value=f" {self.textMap.get(14, locale, user_locale)}: {notes.current_realm_currency}/{notes.max_realm_currency}\n"
            f'{self.textMap.get(15, locale, user_locale)}: {realm_recover_time}',
            inline=False
        )
        exped_finished = 0
        exped_msg = ''
        total_exped = len(notes.expeditions)
        if not notes.expeditions:
            exped_msg = self.textMap.get(18, locale, user_locale)
        for expedition in notes.expeditions:
            exped_msg += f'• {expedition.character.name}'
            if expedition.finished:
                exped_finished += 1
                exped_msg += f': {self.textMap.get(19, locale, user_locale)}\n'
            else:
                day_msg = self.textMap.get(2, locale, user_locale) if expedition.completion_time.day == datetime.now(
                ).day else self.textMap.get(3, locale, user_locale)
                exped_msg += f': {day_msg} {expedition.completion_time.strftime("%H:%M")}\n'
        result.add_field(
            name=f'<:ADVENTURERS_GUILD:998780550615679086> {self.textMap.get(20, locale, user_locale)} ({exped_finished}/{total_exped})',
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
            return errEmbed(message=self.textMap.get(21, locale, user_locale)).set_author(name=self.textMap.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(message=f'```{e}```').set_author(name=self.textMap.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            characters = await client.get_calculator_characters()
            result = defaultEmbed()
            result.add_field(
                name=self.textMap.get(43, locale, user_locale),
                value=f"📅 {self.textMap.get(44, locale, user_locale)}: {genshinUser.stats.days_active}\n"
                f"<:expedition:956385168757780631> {self.textMap.get(45, locale, user_locale)}: {genshinUser.stats.characters}/{len(characters)}\n"
                f"📜 {self.textMap.get(46, locale, user_locale)}: {genshinUser.stats.achievements}\n"
                f"🌙 {self.textMap.get(47, locale, user_locale)}: {genshinUser.stats.spiral_abyss}",
                inline=False)
            result.add_field(
                name=self.textMap.get(48, locale, user_locale),
                value=f"<:anemo:956719995906322472> {self.textMap.get(49, locale, user_locale)}: {genshinUser.stats.anemoculi}/66\n"
                f"<:geo:956719995440730143> {self.textMap.get(50, locale, user_locale)}: {genshinUser.stats.geoculi}/131\n"
                f"<:electro:956719996262821928> {self.textMap.get(51, locale, user_locale)}: {genshinUser.stats.electroculi}/181",
                inline=False)
            result.add_field(
                name=self.textMap.get(52, locale, user_locale),
                value=f"{self.textMap.get(53, locale, user_locale)}: {genshinUser.stats.common_chests}\n"
                f"{self.textMap.get(54, locale, user_locale)}: {genshinUser.stats.exquisite_chests}\n"
                f"{self.textMap.get(57, locale, user_locale)}: {genshinUser.stats.precious_chests}\n"
                f"{self.textMap.get(55, locale, user_locale)}: {genshinUser.stats.luxurious_chests}",
                inline=False)
            result.set_author(name=self.textMap.get(
                56, locale, user_locale), icon_url=user.avatar)
            if custom_uid is not None:
                result.set_footer(text=f'{self.textMap.get(123, locale, user_locale)}: {custom_uid}')
            return result, True

    async def getArea(self, user_id: int, custom_uid: Literal["int", None], locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        uid = custom_uid or uid
        try:
            genshinUser = await client.get_partial_genshin_user(uid)
        except genshin.errors.DataNotPublic:
            return errEmbed(message=self.textMap.get(21, locale, user_locale)).set_author(name=self.textMap.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(message=f'```{e}```').set_author(name=self.textMap.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            explorations = genshinUser.explorations
            explore_str = ""
            for exploration in reversed(explorations):
                level_str = "" if exploration.id == 5 or exploration.id == 6 else f"Lvl. {exploration.offerings[0].level}"
                emoji = getAreaEmoji(exploration.id)
                explore_str += f"{emoji} {exploration.name} | {exploration.explored}% | {level_str}\n"
            result = defaultEmbed(message=explore_str)
        return result.set_author(name=self.textMap.get(58, locale, user_locale), icon_url=user.avatar), True

    async def getDiary(self, user_id: int, month: int, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            diary = await client.get_diary(month=month)
        except genshin.errors.DataNotPublic:
            return errEmbed(message=self.textMap.get(21, locale, user_locale)).set_author(name=self.textMap.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(message=f'```{e}```').set_author(name=self.textMap.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            d = diary.data
            result = defaultEmbed(
                message=f'{self.textMap.get(59, locale, user_locale)} {self.textMap.get(60, locale, user_locale) if d.primogems_rate > 0 else self.textMap.get(61, locale, user_locale)} {abs(d.primogems_rate)}%\n'
                f'{self.textMap.get(62, locale, user_locale)} {self.textMap.get(60, locale, user_locale) if d.mora_rate > 0 else self.textMap.get(61, locale, user_locale)} {abs(d.mora_rate)}%'
            )
            result.add_field(
                name=self.textMap.get(63, locale, user_locale),
                value=f'<:primo:958555698596290570> {d.current_primogems} ({int(d.current_primogems/160)} <:pink_ball:984652245851316254>) • {self.textMap.get(64, locale, user_locale)}: {d.last_primogems} ({int(d.last_primogems/160)} <:pink_ball:984652245851316254>)\n'
                f'<:mora:958577933650362468> {d.current_mora} • {self.textMap.get(64, locale, user_locale)}: {d.last_mora}',
                inline=False
            )
            msg = ''
            for cat in d.categories:
                msg += f'{cat.name}: {cat.percentage}%\n'
            result.add_field(name=self.textMap.get(
                65, locale, user_locale), value=msg, inline=False)
            result.add_field(
                name=self.textMap.get(66, locale, user_locale),
                value=f'{self.textMap.get(67, locale, user_locale)}\n{self.textMap.get(68, locale, user_locale)}',
                inline=False
            )
            return result.set_author(name=f'{self.textMap.get(69, locale, user_locale)} • {month}', icon_url=user.avatar), True

    async def getDiaryLog(self, user_id: int, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            diary = await client.get_diary()
        except genshin.errors.DataNotPublic as e:
            return errEmbed(message=self.textMap.get(21, locale, user_locale)).set_author(name=self.textMap.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(message=f'```{e}```').set_author(name=self.textMap.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            primoLog = ''
            result = []
            async for action in client.diary_log(limit=30):
                primoLog = primoLog + \
                    f"{action.action} - {action.amount} {self.textMap.get(71, locale, user_locale)}"+"\n"
            embed = defaultEmbed(message=f"{primoLog}")
            embed.set_author(name=self.textMap.get(
                70, locale, user_locale), icon_url=user.avatar)
            result.append(embed)
            moraLog = ''
            async for action in client.diary_log(limit=30, type=genshin.models.DiaryType.MORA):
                moraLog = moraLog + \
                    f"{action.action} - {action.amount} {self.textMap.get(73, locale, user_locale)}"+"\n"
            embed = defaultEmbed(message=f"{moraLog}")
            embed.set_author(name=self.textMap.get(
                72, locale, user_locale), icon_url=user.avatar)
            result.append(embed)
        return result, True

    async def getAbyss(self, user_id: int, previous: bool, overview: bool, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            abyss = await client.get_spiral_abyss(uid, previous=previous)
        except genshin.errors.DataNotPublic:
            return errEmbed(message=self.textMap.get(21, locale, user_locale)).set_author(name=self.textMap.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(message=f'```{e}```').set_author(name=self.textMap.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            rank = abyss.ranks
            if len(rank.most_kills) == 0:
                result = errEmbed(message=f'{self.textMap.get(74, locale, user_locale)}\n'
                                  f'{self.textMap.get(75, locale, user_locale)}')
                result.set_author(name=self.textMap.get(
                    76, locale, user_locale), icon_url=user.avatar)
                return result, False
            result = defaultEmbed(
                f"{self.textMap.get(77, locale, user_locale)} {abyss.season}",
                f"{self.textMap.get(78, locale, user_locale)} {abyss.max_floor}\n"
                f"✦ {abyss.total_stars}"
            )
            result.add_field(
                name=self.textMap.get(79, locale, user_locale),
                value=f"{getCharacter(rank.strongest_strike[0].id)['emoji']} {self.textMap.get(80, locale, user_locale)}: {rank.strongest_strike[0].value}\n"
                f"{getCharacter(rank.most_kills[0].id)['emoji']} {self.textMap.get(81, locale, user_locale)}: {rank.most_kills[0].value}\n"
                f"{getCharacter(rank.most_damage_taken[0].id)['emoji']} {self.textMap.get(82, locale, user_locale)}: {rank.most_damage_taken[0].value}\n"
                f"{getCharacter(rank.most_bursts_used[0].id)['emoji']} {self.textMap.get(83, locale, user_locale)}: {rank.most_bursts_used[0].value}\n"
                f"{getCharacter(rank.most_skills_used[0].id)['emoji']} {self.textMap.get(84, locale, user_locale)}: {rank.most_skills_used[0].value}"
            )
            result.set_author(name=self.textMap.get(85, locale, user_locale), icon_url=user.avatar)
            if overview:
                return result, True
            result = []
            for floor in abyss.floors:
                embed = defaultEmbed().set_author(
                    name=f"F{floor.floor} (✦ {floor.stars}/9)")
                for chamber in floor.chambers:
                    name = f'{self.textMap.get(86, locale, user_locale)} {chamber.chamber} {self.textMap.get(87, locale, user_locale)} ✦ {chamber.stars}'
                    chara_list = [[], []]
                    for i, battle in enumerate(chamber.battles):
                        for chara in battle.characters:
                            chara_list[i].append(chara.name)
                    topStr = ''
                    bottomStr = ''
                    for top_char in chara_list[0]:
                        topStr += f"• {top_char} "
                    for bottom_char in chara_list[1]:
                        bottomStr += f"• {bottom_char} "
                    embed.add_field(
                        name=name,
                        value=f"{self.textMap.get(88, locale, user_locale)} {topStr}\n\n"
                        f"{self.textMap.get(89, locale, user_locale)} {bottomStr}",
                        inline=False
                    )
                result.append(embed)
            return result, True

    async def getBuild(self, element_dict: dict, chara_name: str, locale: Locale, user_locale: Literal["str", None]):
        charas = dict(element_dict)
        result = []
        name = chara_name
        count = 1
        has_thoughts = False
        for build in charas[chara_name]['builds']:
            statStr = ''
            for stat, value in build['stats'].items():
                statStr += f'{stat} ➜ {value}\n'
            embed = defaultEmbed(
                f'{name} - {self.textMap.get(90, locale, user_locale)}{count}',
                f"{self.textMap.get(91, locale, user_locale)} • {getWeapon(name=build['weapon'])['emoji']} {build['weapon']}\n"
                f"{self.textMap.get(92, locale, user_locale)} • {build['artifacts']}\n"
                f"{self.textMap.get(93, locale, user_locale)} • {build['main_stats']}\n"
                f"{self.textMap.get(94, locale, user_locale)} • {build['talents']}\n"
                f"{build['move']} • {build['dmg']}\n\n"
            )
            embed.add_field(
                name=self.textMap.get(95, locale, user_locale),
                value=statStr
            )
            count += 1
            embed.set_thumbnail(
                url=getCharacter(name=name)["icon"])
            embed.set_footer(
                text=f'[{self.textMap.get(96, locale, user_locale)}](https://bbs.nga.cn/read.php?tid=25843014)')
            result.append([embed, build['weapon'], build['artifacts']])
        if 'thoughts' in charas[chara_name]:
            has_thoughts = True
            count = 1
            embed = defaultEmbed(self.textMap.get(97, locale, user_locale))
            for thought in charas[chara_name]['thoughts']:
                embed.add_field(name=f'#{count}',
                                value=thought, inline=False)
                count += 1
            embed.set_thumbnail(
                url=getCharacter(name=name)["icon"])
            result.append([embed, '', ''])
        return result, has_thoughts

    async def setResinNotification(self, user_id: int, resin_notification_toggle: int, resin_threshold: int, max_notif: int, locale: Locale):
        c: aiosqlite.Cursor = await self.db.cursor()
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            await client.get_notes(uid)
        except genshin.errors.DataNotPublic:
            return errEmbed(message=self.textMap.get(21, locale, user_locale)).set_author(name=self.textMap.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(message=f'```{e}```').set_author(name=self.textMap.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            if resin_notification_toggle == 0:
                await c.execute('UPDATE genshin_accounts SET resin_notification_toggle = 0 WHERE user_id = ?', (user_id,))
                result = defaultEmbed().set_author(name=self.textMap.get(98, locale, user_locale), icon_url=user.avatar)
            else:
                await c.execute('UPDATE genshin_accounts SET resin_notification_toggle = ?, resin_threshold = ? , max_notif = ? WHERE user_id = ?', (resin_notification_toggle, resin_threshold, max_notif, user_id))
                toggle_str = self.textMap.get(99, locale, user_locale) if resin_notification_toggle == 1 else self.textMap.get(100, locale, user_locale)
                result = defaultEmbed(
                    message=f'{self.textMap.get(101, locale, user_locale)}: {toggle_str}\n'
                    f'{self.textMap.get(102, locale, user_locale)}: {resin_threshold}\n'
                    f'{self.textMap.get(103, locale, user_locale)}: {max_notif}'
                )
                result.set_author(name=self.textMap.get(104, locale, user_locale), icon_url=user.avatar)
            await self.db.commit()
        return result, True

    async def getUserCharacters(self, user_id: int, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            characters = await client.get_genshin_characters(uid)
        except genshin.errors.DataNotPublic:
            return errEmbed(message=self.textMap.get(21, locale, user_locale)).set_author(name=self.textMap.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(message=f'```{e}```').set_author(name=self.textMap.get(23, locale, user_locale), icon_url=user.avatar), False
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
                    element)['emoji'], label=f"{getElement(element)['name']}元素角色", value=index))
                message = ''
                for character in characters:
                    message += f'{getCharacter(character.id)["emoji"]} {character.name} | Lvl. {character.level} | C{character.constellation}R{character.weapon.refinement}\n\n'
                embed = defaultEmbed(f'{getElement(element)["emoji"]} {getElement(element)["name"]}元素角色', message).set_author(
                    name=self.textMap.get(105, locale, user_locale), icon_url=user.avatar)
                result['embeds'].append(embed)
                index += 1
            return result, True

    async def redeemCode(self, user_id: int, code: str, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        try:
            await client.redeem_code(code)
        except genshin.errors.RedemptionClaimed:
            return errEmbed().set_author(name=self.textMap.get(106, locale, user_locale), icon_url=user.avatar), False
        except genshin.errors.GenshinException:
            return errEmbed().set_author(name=self.textMap.get(107, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(message=f'```{e}```').set_author(name=self.textMap.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            return defaultEmbed(message=f'{self.textMap.get(108, locale, user_locale)}: {code}').set_author(name=self.textMap.get(109, locale, user_locale), icon_url=user.avatar), True

    async def getActivities(self, user_id: int, custom_uid: int, locale: Locale):
        client, uid, user, user_locale = await self.getUserCookie(user_id, locale)
        uid = custom_uid or uid
        try:
            activities = await client.get_genshin_activities(uid)
        except genshin.errors.DataNotPublic:
            return errEmbed(message=self.textMap.get(21, locale, user_locale)).set_author(name=self.textMap.get(22, locale, user_locale), icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(message=f'```{e}```').set_author(name=self.textMap.get(23, locale, user_locale), icon_url=user.avatar), False
        else:
            summer = activities.summertime_odyssey
            if summer is None:
                return errEmbed().set_author(name=self.textMap.get(110, locale, user_locale), icon_url=user.avatar), False
            result = await self.parseSummerEmbed(summer, user, custom_uid, locale, user_locale)
            return result, True

    async def parseSummerEmbed(self, summer: genshin.models.Summer, user: Member, custom_uid: int, locale: Locale, user_locale: Literal["str", None]) -> list[Embed]:
        embeds = []
        embed = defaultEmbed().set_author(name=self.textMap.get(111, locale, user_locale), icon_url=user.avatar)
        embed.add_field(
            name=f'<:SCORE:983948729293897779> {self.textMap.get(43, locale, user_locale)}',
            value=f'{self.textMap.get(112, locale, user_locale)}: {summer.waverider_waypoints}/13\n'
            f'{self.textMap.get(113, locale, user_locale)}: {summer.waypoints}/10\n'
            f'{self.textMap.get(114, locale, user_locale)}: {summer.treasure_chests}'
        )
        embeds.append(embed)
        embed = defaultEmbed().set_author(name=self.textMap.get(111, locale, user_locale), icon_url=user.avatar)
        surfs = summer.surfpiercer
        value = ''
        for surf in surfs:
            if surf.finished:
                minutes, seconds = divmod(surf.time, 60)
                time_str = f'{minutes}{self.textMap.get(7, locale, user_locale)} {seconds}{self.textMap.get(8, locale, user_locale)}' if minutes != 0 else f'{seconds}{self.textMap.get(8, locale, user_locale)}'
                value += f'{surf.id}. {time_str}\n'
            else:
                value += f'{surf.id}. *{self.textMap.get(115, locale, user_locale)}* \n'
        embed.add_field(
            name=self.textMap.get(116, locale, user_locale),
            value=value
        )
        embed.set_thumbnail(url='https://i.imgur.com/Qt4Tez0.png')
        embeds.append(embed)
        memories = summer.memories
        for memory in memories:
            embed = defaultEmbed().set_author(name=self.textMap.get(117, locale, user_locale), icon_url=user.avatar)
            embed.set_thumbnail(url='https://i.imgur.com/yAbpUF8.png')
            embed.set_image(url=memory.icon)
            embed.add_field(name=memory.name,
                            value=f'{self.textMap.get(119, locale, user_locale)}: {memory.finish_time}')
            embeds.append(embed)
        realms = summer.realm_exploration
        for realm in realms:
            embed = defaultEmbed().set_author(name=self.textMap.get(118, locale, user_locale), icon_url=user.avatar)
            embed.set_thumbnail(url='https://i.imgur.com/0jyBciz.png')
            embed.set_image(url=realm.icon)
            embed.add_field(
                name=realm.name,
                value=f'{self.textMap.get(119, locale, user_locale)}: {realm.finish_time if realm.finished else self.textMap.get(115, locale, user_locale)}\n'
                f'{self.textMap.get(120, locale, user_locale)} {realm.success} {self.textMap.get(121, locale, user_locale)}\n'
                f'{self.textMap.get(122, locale, user_locale)} {realm.skills_used} {self.textMap.get(121, locale, user_locale)}'
            )
            embeds.append(embed)
        if custom_uid is not None:
            embed: Embed
            for embed in embeds:
                embed.set_footer(text=f'{self.textMap.get(123, locale, user_locale)}: {custom_uid}')
        return embeds

    async def getUserCookie(self, user_id: int, locale: Locale=None):
        user = self.bot.get_user(user_id)
        c: aiosqlite.Cursor = await self.db.cursor()
        await c.execute('SELECT ltuid, ltoken, cookie_token, uid FROM genshin_accounts WHERE user_id = ?', (user_id,))
        user_data = await c.fetchone()
        if user_data is None:
            client = getClient()
            uid = None
        else:
            uid = user_data[3]
            client = genshin.Client()
            client.set_cookies(
                ltuid=user_data[0], ltoken=user_data[1], account_id=user_data[0], cookie_token=user_data[2])
            client.default_game = genshin.Game.GENSHIN
            client.uids[genshin.Game.GENSHIN] = uid
        user_locale = await self.textMap.getUserLocale(user_id)
        if user_locale is not None:
            locale = user_locale
        client_locale = DLGP.get(str(locale)) or 'en-us'
        client.lang = client_locale
        await client.update_character_names(lang=client._lang)
        return client, uid, user, user_locale

    async def userDataExists(self, user_id: int):
        c: aiosqlite.Cursor = await self.db.cursor()
        await c.execute('SELECT * FROM genshin_accounts WHERE user_id = ?', (user_id,))
        user_data = await c.fetchone()
        if user_data is None:
            return False
        return True
