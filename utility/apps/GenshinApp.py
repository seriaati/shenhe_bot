import re
from datetime import datetime

import aiosqlite
import genshin
from discord import Embed, SelectOption
from discord.ext import commands
from utility.utils import (defaultEmbed, errEmbed, getAreaEmoji, getCharacter,
                           getWeapon, getWeekdayName, log, trimCookie)


class GenshinApp:
    def __init__(self, db: aiosqlite.Connection, bot: commands.Bot) -> None:
        self.db = db
        self.bot = bot

    async def setCookie(self, user_id: int, cookie: str, uid: int = None):
        log(False, False, 'setCookie', f'{user_id} (cookie = {cookie})')
        user = self.bot.get_user(user_id)
        user_id = int(user_id)
        cookie = trimCookie(cookie)
        if cookie is None:
            result = errEmbed(
                message='輸入 `/register` 來查看設定方式').set_author(name='無效的 cookie', icon_url=user.avatar)
            return result, False
        client = genshin.Client(lang='zh-tw')
        client.set_cookies(
            ltuid=cookie[0], ltoken=cookie[1], account_id=cookie[0], cookie_token=cookie[2])
        accounts = await client.get_game_accounts()
        if uid is None:
            if len(accounts) == 0:
                result = errEmbed(message='已取消設定帳號').set_author(
                    name='帳號內沒有任何角色', icon_url=user.avatar)
                return result, False
            elif len(accounts) == 1:
                uid = accounts[0].uid
            else:
                account_options = []
                for account in accounts:
                    account_options.append(SelectOption(
                        label=f'{account.uid} | Lvl. {account.level} | {account.nickname}', value=account.uid))
                return account_options, True
        else:
            c = await self.db.cursor()
            await c.execute('INSERT INTO genshin_accounts (user_id, ltuid, ltoken, cookie_token, uid) VALUES (?, ?, ?, ?, ?) ON CONFLICT (user_id) DO UPDATE SET ltuid = ?, ltoken = ?, cookie_token = ?, uid = ? WHERE user_id = ?', (user_id, cookie[0], cookie[1], cookie[2], uid, cookie[0], cookie[1], cookie[2], uid, user_id))
            result = defaultEmbed().set_author(name='帳號設定成功', icon_url=user.avatar)
            await self.db.commit()
            return result, True

    async def claimDailyReward(self, user_id: int):
        client, uid, user = await self.getUserCookie(user_id)
        try:
            reward = await client.claim_daily_reward()
        except genshin.errors.AlreadyClaimed:
            return errEmbed().set_author(name='你已經領過今天的獎勵了!', icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(f'```{e}```').set_author(name='錯誤', icon_url=user.avatar), False
        else:
            return defaultEmbed(message=f'獲得 {reward.amount}x {reward.name}').set_author(name='簽到成功', icon_url=user.avatar), True

    async def getRealTimeNotes(self, user_id: int):
        client, uid, user = await self.getUserCookie(user_id)
        try:
            notes = await client.get_notes(uid)
        except genshin.errors.DataNotPublic:
            return errEmbed(
                '輸入 `/stuck` 來獲取更多資訊').set_author(name='資料不公開', icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(f'```{e}```').set_author(name='錯誤', icon_url=user.avatar), False
        else:
            return self.parseResinEmbed(notes).set_author(name='即時便籤', icon_url=user.avatar), True

    def parseResinEmbed(self, notes) -> Embed:
        if notes.current_resin == notes.max_resin:
            resin_recover_time = '已滿'
        else:
            day_msg = '今天' if notes.resin_recovery_time.day == datetime.now().day else '明天'
            resin_recover_time = f'{day_msg} {notes.resin_recovery_time.strftime("%H:%M")}'

        if notes.current_realm_currency == notes.max_realm_currency:
            realm_recover_time = '已滿'
        else:
            weekday_msg = getWeekdayName(
                notes.realm_currency_recovery_time.weekday())
            realm_recover_time = f'{weekday_msg} {notes.realm_currency_recovery_time.strftime("%H:%M")}'
        if notes.transformer_recovery_time != None:
            t = notes.remaining_transformer_recovery_time
            if t.days > 0:
                recover_time = f'剩餘 {t.days} 天'
            elif t.hours > 0:
                recover_time = f'剩餘 {t.hours} 小時'
            elif t.minutes > 0:
                recover_time = f'剩餘 {t.minutes} 分'
            elif t.seconds > 0:
                recover_time = f'剩餘 {t.seconds} 秒'
            else:
                recover_time = '可使用'
        else:
            recover_time = '質變儀不存在'
        result = defaultEmbed(
            f"",
            f"<:daily:956383830070140938> 已完成的每日數量: {notes.completed_commissions}/{notes.max_commissions}\n"
            f"<:transformer:966156330089971732> 質變儀剩餘時間: {recover_time}"
        )
        result.add_field(
            name='<:resin:956377956115157022> 樹脂',
            value=f" 目前樹脂: {notes.current_resin}/{notes.max_resin}\n"
            f"樹脂回滿時間: {resin_recover_time}\n"
            f'週本樹脂減半: 剩餘 {notes.remaining_resin_discounts}/3 次',
            inline=False
        )
        result.add_field(
            name='<:realm:956384011750613112> 塵歌壺',
            value=f" 目前洞天寶錢數量: {notes.current_realm_currency}/{notes.max_realm_currency}\n"
            f'寶錢全部恢復時間: {realm_recover_time}',
            inline=False
        )
        exped_finished = 0
        exped_msg = ''
        if not notes.expeditions:
            exped_msg = '沒有探索派遣'
            total_exped = 0
        for expedition in notes.expeditions:
            total_exped = len(notes.expeditions)
            exped_msg += f'• {getCharacter(expedition.character.id)["name"]}'
            if expedition.finished:
                exped_finished += 1
                exped_msg += ': 已完成\n'
            else:
                day_msg = '今天' if expedition.completion_time.day == datetime.now().day else '明天'
                exped_msg += f' 完成時間: {day_msg} {expedition.completion_time.strftime("%H:%M")}\n'
        result.add_field(
            name=f'<:ADVENTURERS_GUILD:998780550615679086> 探索派遣 ({exped_finished}/{total_exped})',
            value=exped_msg,
            inline=False
        )
        return result

    async def getUserStats(self, user_id: int):
        client, uid, user = await self.getUserCookie(user_id)
        try:
            genshinUser = await client.get_partial_genshin_user(uid)
        except genshin.errors.DataNotPublic:
            return errEmbed(
                '輸入 `/stuck` 來獲取更多資訊').set_author(name='資料不公開', icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(f'```{e}```').set_author(name='錯誤', icon_url=user.avatar), False
        else:
            characters = await client.get_calculator_characters()
            result = defaultEmbed()
            result.add_field(
                name='綜合',
                value=f"📅 活躍天數: {genshinUser.stats.days_active}\n"
                f"<:expedition:956385168757780631> 角色數量: {genshinUser.stats.characters}/{len(characters)}\n"
                f"📜 成就數量:{genshinUser.stats.achievements}/639\n"
                f"🌙 深淵已達: {genshinUser.stats.spiral_abyss}層",
                inline=False)
            result.add_field(
                name='神瞳',
                value=f"<:anemo:956719995906322472> 風神瞳: {genshinUser.stats.anemoculi}/66\n"
                f"<:geo:956719995440730143> 岩神瞳: {genshinUser.stats.geoculi}/131\n"
                f"<:electro:956719996262821928> 雷神瞳: {genshinUser.stats.electroculi}/181", inline=False)
            result.add_field(
                name='寶箱',
                value=f"一般寶箱: {genshinUser.stats.common_chests}\n"
                f"稀有寶箱: {genshinUser.stats.exquisite_chests}\n"
                f"珍貴寶箱: {genshinUser.stats.luxurious_chests}",
                inline=False)
        return result.set_author(name='原神數據', icon_url=user.avatar), True

    async def getArea(self, user_id: int):
        client, uid, user = await self.getUserCookie(user_id)
        try:
            genshinUser = await client.get_partial_genshin_user(uid)
        except genshin.errors.DataNotPublic:
            return errEmbed(
                '輸入 `/stuck` 來獲取更多資訊').set_author(name='資料不公開', icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(f'```{e}```').set_author(name='錯誤', icon_url=user.avatar), False
        else:
            explorations = genshinUser.explorations
            explore_str = ""
            for exploration in reversed(explorations):
                level_str = '' if exploration.name == '淵下宮' or exploration.name == '層岩巨淵' else f'- Lvl. {exploration.level}'
                emoji_name = getAreaEmoji(exploration.name)
                explore_str += f"{emoji_name} {exploration.name} {exploration.explored}% {level_str}\n"
            result = defaultEmbed(message=explore_str)
        return result.set_author(name='區域探索度', icon_url=user.avatar), True

    async def getDiary(self, user_id: int, month: int):
        client, uid, user = await self.getUserCookie(user_id)
        try:
            diary = await client.get_diary(month=month)
        except genshin.errors.DataNotPublic:
            return errEmbed(
                '輸入 `/stuck` 來獲取更多資訊').set_author(name='資料不公開', icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(f'```{e}```').set_author(name='錯誤', icon_url=user.avatar), False
        else:
            d = diary.data
            result = defaultEmbed(message=f'原石收入比上個月{"增加" if d.primogems_rate > 0 else "減少"}了{abs(d.primogems_rate)}%\n'
                                  f'摩拉收入比上個月{"增加" if d.mora_rate > 0 else "減少"}了{abs(d.mora_rate)}%'
                                  )
            result.add_field(
                name='本月共獲得',
                value=f'<:primo:958555698596290570> {d.current_primogems} ({int(d.current_primogems/160)} <:pink_ball:984652245851316254>) • 上個月: {d.last_primogems} ({int(d.last_primogems/160)} <:pink_ball:984652245851316254>)\n'
                f'<:mora:958577933650362468> {d.current_mora} • 上個月: {d.last_mora}',
                inline=False
            )
            msg = ''
            for cat in d.categories:
                msg += f'{cat.name}: {cat.percentage}%\n'
            result.add_field(name=f'原石收入分類', value=msg, inline=False)
            result.add_field(
                name='獲取紀錄',
                value='點按下方的按鈕可以\n查看本月近30筆的摩拉或原石獲取紀錄',
                inline=False
            )
            return result.set_author(name=f'旅行者日記 • {month}月', icon_url=user.avatar), True

    async def getDiaryLog(self, user_id: int):
        client, uid, user = await self.getUserCookie(user_id)
        try:
            diary = await client.get_diary()
        except genshin.errors.DataNotPublic as e:
            return errEmbed(
                '輸入 `/stuck` 來獲取更多資訊').set_author(name='資料不公開', icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(f'```{e}```').set_author(name='錯誤', icon_url=user.avatar), False
        else:
            primoLog = ''
            result = []
            async for action in client.diary_log(limit=35):
                primoLog = primoLog + \
                    f"{action.action} - {action.amount} 原石"+"\n"
            embed = defaultEmbed(message=f"{primoLog}")
            embed.set_author(name='原石獲取紀錄', icon_url=user.avatar)
            result.append(embed)
            moraLog = ''
            async for action in client.diary_log(limit=25, type=genshin.models.DiaryType.MORA):
                moraLog = moraLog+f"{action.action} - {action.amount} 摩拉"+"\n"
            embed = defaultEmbed(message=f"{moraLog}")
            embed.set_author(name='摩拉獲取紀錄', icon_url=user.avatar)
            result.append(embed)
        return result, True

    async def getAbyss(self, user_id: int, previous: bool, overview: bool):
        client, uid, user = await self.getUserCookie(user_id)
        try:
            abyss = await client.get_spiral_abyss(uid, previous=previous)
        except genshin.errors.DataNotPublic:
            return errEmbed(
                '輸入 `/stuck` 來獲取更多資訊').set_author(name='資料不公開', icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(f'```{e}```').set_author(name='錯誤', icon_url=user.avatar), False
        else:
            rank = abyss.ranks
            if len(rank.most_kills) == 0:
                result = errEmbed(message='請輸入 `/stats` 來刷新資料\n'
                                  '(深淵資料需最多1小時來接收)\n'
                                  '/abyss 只支持第9層以上的戰績').set_author(name='找不到深淵資料', icon_url=user.avatar)
                return result, False
            result = defaultEmbed(
                f"第{abyss.season}期深淵",
                f"獲勝場次: {abyss.total_wins}/{abyss.total_battles}\n"
                f"達到{abyss.max_floor}層\n"
                f"共{abyss.total_stars} ✦"
            )
            result.add_field(
                name="戰績",
                value=f"單次最高傷害 • {getCharacter(rank.strongest_strike[0].id)['name']} • {rank.strongest_strike[0].value}\n"
                f"擊殺王 • {getCharacter(rank.most_kills[0].id)['name']} • {rank.most_kills[0].value}次擊殺\n"
                f"最常使用角色 • {getCharacter(rank.most_played[0].id)['name']} • {rank.most_played[0].value}次\n"
                f"最多Q使用角色 • {getCharacter(rank.most_bursts_used[0].id)['name']} • {rank.most_bursts_used[0].value}次\n"
                f"最多E使用角色 • {getCharacter(rank.most_skills_used[0].id)['name']} • {rank.most_skills_used[0].value}次"
            )
            result.set_author(name='深淵總覽', icon_url=user.avatar)
            if overview:
                return result, True
            result = []
            for floor in abyss.floors:
                embed = defaultEmbed().set_author(
                    name=f"第{floor.floor}層 (共{floor.stars} ✦)")
                for chamber in floor.chambers:
                    name = f'第{chamber.chamber}間 {chamber.stars} ✦'
                    chara_list = [[], []]
                    for i, battle in enumerate(chamber.battles):
                        for chara in battle.characters:
                            chara_list[i].append(
                                getCharacter(chara.id)['name'])
                    topStr = ''
                    bottomStr = ''
                    for top_char in chara_list[0]:
                        topStr += f"• {top_char} "
                    for bottom_char in chara_list[1]:
                        bottomStr += f"• {bottom_char} "
                    embed.add_field(
                        name=name,
                        value=f"[上半] {topStr}\n\n"
                        f"[下半] {bottomStr}",
                        inline=False
                    )
                result.append(embed)
            return result, True

    async def getBuild(self, element_dict: dict, chara_name: str):
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
                f'{name} - 配置{count}',
                f"武器 • {getWeapon(name=build['weapon'])['emoji']} {build['weapon']}\n"
                f"聖遺物 • {build['artifacts']}\n"
                f"主詞條 • {build['main_stats']}\n"
                f"天賦 • {build['talents']}\n"
                f"{build['move']} • {build['dmg']}\n\n"
            )
            embed.add_field(
                name=f"屬性面版",
                value=statStr
            )
            count += 1
            embed.set_thumbnail(
                url=getCharacter(name=name)["icon"])
            embed.set_footer(
                text='[來源](https://bbs.nga.cn/read.php?tid=25843014)')
            result.append([embed, build['weapon'], build['artifacts']])
        if 'thoughts' in charas[chara_name]:
            has_thoughts = True
            count = 1
            embed = defaultEmbed(f'聖遺物思路')
            for thought in charas[chara_name]['thoughts']:
                embed.add_field(name=f'思路{count}',
                                value=thought, inline=False)
                count += 1
            embed.set_thumbnail(
                url=getCharacter(name=name)["icon"])
            result.append([embed, '', ''])
        return result, has_thoughts

    async def setResinNotification(self, user_id: int, resin_notification_toggle: int, resin_threshold: int, max_notif: int):
        c: aiosqlite.Cursor = await self.db.cursor()
        client, uid, user = await self.getUserCookie(user_id)
        try:
            notes = await client.get_notes(uid)
        except genshin.errors.DataNotPublic:
            return errEmbed(
                '輸入 `/stuck` 來獲取更多資訊').set_author(name='資料不公開', icon_url=user.avatar), False
        except Exception as e:
            return errEmbed(f'```{e}```').set_author(name='錯誤', icon_url=user.avatar), False
        else:
            if resin_notification_toggle == 0:
                await c.execute('UPDATE genshin_accounts SET resin_notification_toggle = 0 WHERE user_id = ?', (user_id,))
                result = defaultEmbed().set_author(name='樹脂提醒功能已關閉', icon_url=user.avatar)
            else:
                await c.execute('UPDATE genshin_accounts SET resin_notification_toggle = ?, resin_threshold = ? , max_notif = ? WHERE user_id = ?', (resin_notification_toggle, resin_threshold, max_notif, user_id))
                toggle_str = '開' if resin_notification_toggle == 1 else '關'
                result = defaultEmbed(
                    message=f'目前開關: {toggle_str}\n'
                    f'樹脂提醒閥值: {resin_threshold}\n'
                    f'最大提醒數量: {max_notif}'
                )
                result.set_author(name='設置成功', icon_url=user.avatar)
            await self.db.commit()
        return result, True

    async def redeemCode(self, user_id: int, code: str):
        client, uid, user = await self.getUserCookie(user_id)
        try:
            await client.redeem_code(code)
        except genshin.errors.RedemptionClaimed:
            return errEmbed().set_author(name='你已經兌換過這個兌換碼了!', icon_url=user.avatar), False
        except genshin.errors.GenshinException:
            return errEmbed().set_author(name='兌換碼無效', icon_url=user.avatar), False
        else:
            return defaultEmbed(message=f'兌換碼: {code}').set_author(name='兌換成功', icon_url=user.avatar), True

    async def getUserCookie(self, user_id: int):
        user = self.bot.get_user(user_id)
        c: aiosqlite.Cursor = await self.db.cursor()
        await c.execute('SELECT ltuid, ltoken, cookie_token, uid FROM genshin_accounts WHERE user_id = ?', (user_id,))
        user_data = await c.fetchone()
        client = genshin.Client()
        client.set_cookies(
            ltuid=user_data[0], ltoken=user_data[1], account_id=user_data[0], cookie_token=user_data[2])
        client.lang = "zh-tw"
        client.default_game = genshin.Game.GENSHIN
        client.uids[genshin.Game.GENSHIN] = user_data[3]
        return client, user_data[3], user
    
    async def userDataExists(self, user_id: int):
        c: aiosqlite.Cursor = await self.db.cursor()
        await c.execute('SELECT * FROM genshin_accounts WHERE user_id = ?', (user_id,))
        user_data = await c.fetchone()
        if user_data is None:
            return False
        return True
