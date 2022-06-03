import re
from datetime import datetime, timedelta

import aiosqlite
import genshin
from discord import Member

from utility.utils import (defaultEmbed, errEmbed, getCharacterName, getCharacterNameWithID,
                           getWeekdayName, log, trimCookie)


class GenshinApp:
    def __init__(self, db: aiosqlite.Connection, bot) -> None:
        self.db = db
        self.bot = bot

    async def setCookie(self, user_id: int, cookie: str) -> str:
        log(False, False, 'setCookie', f'{user_id} (cookie = {cookie})')
        user_id = int(user_id)
        cookie = trimCookie(cookie)
        if cookie == None:
            return f'無效的Cookie, 請重新輸入(輸入 `/cookie設定` 顯示說明)'
        client = genshin.Client(lang='zh-tw')
        client.set_cookies(cookie)
        accounts = await client.get_game_accounts()
        if len(accounts) == 0:
            result = '帳號內沒有任何角色, 取消設定Cookie'
        else:
            ltoken = re.search(
                '[0-9A-Za-z]{20,}', cookie).group()
            ltuid_str = re.search('ltuid=[0-9]{3,}', cookie).group()
            ltuid = int(
                re.search(r'\d+', ltuid_str).group())
            c: aiosqlite.Cursor = await self.db.cursor()
            await c.execute('UPDATE genshin_accounts SET ltuid = ?, ltoken = ? WHERE user_id = ?', (ltuid, ltoken, user_id))
            log(False, False, 'setCookie', f'{user_id} set cookie success')
            result = f'🍪 Cookie 設定完成'
            await self.db.commit()
        return result

    async def setUID(self, user_id: int, uid: int) -> str:
        log(False, False, 'setUID', f'{user_id}: (uid = {uid})')
        c: aiosqlite.Cursor = await self.db.cursor()
        if len(str(uid)) != 9:
            return errEmbed('請輸入長度為9的UID!'), False
        if uid//100000000 != 9:
            embed = errEmbed(
                '你似乎不是台港澳服玩家!',
                '非常抱歉, 「緣神有你」是一個台澳港服為主的群組\n'
                '為保群友的遊戲質量, 我們無法接受你的入群申請\n'
                '我們真心認為其他群組對你來說可能是個更好的去處 🙏')
            return embed, False
        await c.execute('SELECT * FROM genshin_accounts WHERE user_id = ?', (user_id,))
        result = await c.fetchone()
        if result is None:
            await c.execute('INSERT INTO genshin_accounts (user_id, uid) VALUES (?, ?)', (user_id, uid))
        else:
            await c.execute('UPDATE genshin_accounts SET uid = ? WHERE user_id = ?', (uid, user_id))
        await self.db.commit()
        return defaultEmbed('<:TICK:982124759070441492> UID設置成功', f'UID: {uid}'), True

    async def claimDailyReward(self, user_id: int):
        client, uid, only_uid = await self.getUserCookie(user_id)
        if only_uid:
            result = errEmbed('你不能使用這項功能!', '請使用`/cookie`的方式註冊後再來試試看')
            return result
        try:
            reward = await client.claim_daily_reward()
        except genshin.errors.AlreadyClaimed:
            result = errEmbed(f'你已經領過今天的獎勵了!', '')
        except genshin.errors.GenshinException as e:
            result = errEmbed(f'簽到失敗: {e.original}', '')
        except Exception as e:
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        else:
            result = defaultEmbed(
                f'<:TICK:982124759070441492> 今日簽到成功',
                f'獲得 {reward.amount}x {reward.name}'
            )
        return result

    async def getRealTimeNotes(self, user_id: int, check_resin_excess=False):
        client, uid, only_uid = await self.getUserCookie(user_id)
        if only_uid:
            result = errEmbed('你不能使用這項功能!', '請使用`/cookie`的方式註冊後再來試試看')
            return result
        try:
            notes = await client.get_notes(uid)
        except genshin.errors.DataNotPublic:
            result = errEmbed('你的資料並不是公開的!', '請輸入`/stuck`來取得更多資訊')
            return result
        except genshin.errors.GenshinException as e:
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
            return result
        except Exception as e:
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
            return result
        else:
            if check_resin_excess:
                return notes.current_resin
            else:
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
                    f"即時便籤",
                    f"<:daily:956383830070140938> 已完成的每日數量: {notes.completed_commissions}/{notes.max_commissions}\n"
                    f"<:transformer:966156330089971732> 質變儀剩餘時間: {recover_time}"
                )
                result.add_field(
                    name='樹脂',
                    value=f"<:resin:956377956115157022> 目前樹脂: {notes.current_resin}/{notes.max_resin}\n"
                    f"樹脂回滿時間: {resin_recover_time}\n"
                    f'週本樹脂減半: 剩餘 {notes.remaining_resin_discounts}/3 次',
                    inline=False
                )
                result.add_field(
                    name='塵歌壺',
                    value=f"<:realm:956384011750613112> 目前洞天寶錢數量: {notes.current_realm_currency}/{notes.max_realm_currency}\n"
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
                    exped_msg += f'• {getCharacterName(expedition.character)}'
                    if expedition.finished:
                        exped_finished += 1
                        exped_msg += ': 已完成\n'
                    else:
                        day_msg = '今天' if expedition.completion_time.day == datetime.now().day else '明天'
                        exped_msg += f' 完成時間: {day_msg} {expedition.completion_time.strftime("%H:%M")}\n'
                result.add_field(
                    name=f'探索派遣 ({exped_finished}/{total_exped})',
                    value=exped_msg,
                    inline=False
                )
                return result

    async def getUserStats(self, user_id: int):
        client, uid, only_uid = await self.getUserCookie(user_id)
        try:
            genshinUser = await client.get_partial_genshin_user(uid)
        except genshin.errors.DataNotPublic:
            result = errEmbed('你的資料並不是公開的!', '請輸入`/stuck`來取得更多資訊')
            return result
        except genshin.errors.GenshinException as e:
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        else:
            characters = await client.get_calculator_characters()
            result = defaultEmbed(f"統計數據", "")
            result.add_field(name='綜合', value=f"📅 活躍天數: {genshinUser.stats.days_active}\n"
                             f"<:expedition:956385168757780631> 角色數量: {genshinUser.stats.characters}/{len(characters)}\n"
                             f"📜 成就數量:{genshinUser.stats.achievements}/639\n"
                             f"🌙 深淵已達: {genshinUser.stats.spiral_abyss}層", inline=False)
            result.add_field(name='神瞳', value=f"<:anemo:956719995906322472> 風神瞳: {genshinUser.stats.anemoculi}/66\n"
                             f"<:geo:956719995440730143> 岩神瞳: {genshinUser.stats.geoculi}/131\n"
                             f"<:electro:956719996262821928> 雷神瞳: {genshinUser.stats.electroculi}/181", inline=False)
            result.add_field(name='寶箱', value=f"一般寶箱: {genshinUser.stats.common_chests}\n"
                             f"稀有寶箱: {genshinUser.stats.exquisite_chests}\n"
                             f"珍貴寶箱: {genshinUser.stats.luxurious_chests}", inline=False)
        return result

    async def getArea(self, user_id: int):
        client, uid, only_uid = await self.getUserCookie(user_id)
        try:
            genshinUser = await client.get_partial_genshin_user(uid)
        except genshin.errors.DataNotPublic:
            result = errEmbed('你的資料並不是公開的!', '請輸入`/stuck`來取得更多資訊')
            return result
        except genshin.errors.GenshinException as e:
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        else:
            explorations = genshinUser.explorations
            exploreStr = ""
            for exploration in explorations:
                exploreStr += f"{exploration.name}: {exploration.explored}% • Lvl.{exploration.level}\n"
            result = defaultEmbed(
                f"探索度",
                exploreStr
            )
        return result

    async def getDiary(self, user_id: int, month: int):
        currentMonth = datetime.now().month
        if int(month) > currentMonth:
            result = errEmbed('不可輸入大於目前時間的月份')
            return result
        client, uid, only_uid = await self.getUserCookie(user_id)
        try:
            diary = await client.get_diary(month=month)
        except genshin.errors.DataNotPublic:
            result = errEmbed('你的資料並不是公開的!', '請輸入`/stuck`來取得更多資訊')
            return result
        except genshin.errors.GenshinException as e:
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        else:
            d = diary.data
            result = defaultEmbed(
                f'旅行者日記  •  {month}月',
                f'<:primo:958555698596290570> 原石收入比上個月{"增加" if d.primogems_rate > 0 else "減少"}了{abs(d.primogems_rate)}%\n'
                f'<:mora:958577933650362468> 摩拉收入比上個月{"增加" if d.mora_rate > 0 else "減少"}了{abs(d.mora_rate)}%'
            )
            result.add_field(
                name='本月共獲得',
                value=f'<:primo:958555698596290570> {d.current_primogems} • 上個月: {d.last_primogems}\n'
                f'<:mora:958577933650362468> {d.current_mora} • 上個月: {d.last_mora}',
                inline=False
            )
            msg = ''
            for cat in d.categories:
                msg += f'{cat.name}: {cat.percentage}%\n'
            result.add_field(name=f'收入分類', value=msg, inline=False)
        return result

    async def getDiaryLog(self, user_id: int):
        client, uid, only_uid = await self.getUserCookie(user_id)
        try:
            diary = await client.get_diary()
        except genshin.errors.DataNotPublic as e:
            result = errEmbed('你的資料並不是公開的!', '請輸入`/stuck`來取得更多資訊')
        except genshin.errors.GenshinException as e:
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        else:
            primoLog = ''
            moraLog = ''
            result = []
            async for action in client.diary_log(limit=25):
                primoLog = primoLog + \
                    f"{action.action} - {action.amount} 原石"+"\n"
            async for action in client.diary_log(limit=25, type=genshin.models.DiaryType.MORA):
                moraLog = moraLog+f"{action.action} - {action.amount} 摩拉"+"\n"
            embed = defaultEmbed(
                f"<:primo:958555698596290570> 最近25筆原石紀錄",
                f"{primoLog}"
            )
            result.append(embed)
            embed = defaultEmbed(
                f"<:mora:958577933650362468> 最近25筆摩拉紀錄",
                f"{moraLog}"
            )
            result.append(embed)
        return result

    async def getUserCharacters(self, user_id: int):
        client, uid, only_uid = await self.getUserCookie(user_id)
        try:
            result = await client.get_genshin_characters(uid)
        except genshin.errors.DataNotPublic:
            result = errEmbed('你的資料並不是公開的!', '請輸入`/stuck`來取得更多資訊')
            return result
        except genshin.errors.GenshinException as e:
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        else:
            return result

    def parseCharacter(self, user_characters: dict, character_name: str, user: Member):
        found = False
        for character in user_characters:
            if character.name == character_name:
                found = True
                const = character.constellation
                refinement = character.weapon.refinement
                character_level = character.level
                character_rarity = character.rarity
                friendship = character.friendship
                weapon = character.weapon.name
                weapon_level = character.weapon.level
                weapon_rarity = character.weapon.rarity
                icon = character.icon
                artifact_str = '該角色沒有裝配任何聖遺物'
                if len(character.artifacts) > 0:
                    artifact_str = ''
                    for artifact in character.artifacts:
                        artifact_str += f'{artifact.pos_name}: {artifact.name} ({artifact.set.name})\n'
                embed = defaultEmbed(
                    f'C{const}R{refinement} {character_name}', '')
                embed.add_field(
                    name='角色',
                    value=f'{character_rarity}☆\n'
                    f'Lvl. {character_level}\n'
                    f'好感度: {friendship}'
                )
                embed.add_field(
                    name='武器',
                    value=f'{weapon_rarity}☆\n'
                    f'{weapon}\n'
                    f'Lvl. {weapon_level}\n',
                    inline=False)
                embed.add_field(
                    name='聖遺物',
                    value=artifact_str
                )
                embed.set_thumbnail(url=icon)
                embed.set_author(name=user, icon_url=user.avatar)
                return embed
        if not found:
            return errEmbed('你似乎不擁有該角色!', '這有點奇怪, 請告訴小雪這個狀況')

    async def getToday(self, user_id: int):
        client, uid, only_uid = await self.getUserCookie(user_id)
        try:
            diary = await client.get_diary()
        except genshin.errors.DataNotPublic:
            result = errEmbed('你的資料並不是公開的!', '請輸入`/stuck`來取得更多資訊')
            return result
        except genshin.errors.GenshinException as e:
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        else:
            result = defaultEmbed(
                f"今日收入",
                f"<:primo:958555698596290570> {diary.day_data.current_primogems}原石\n"
                f"<:mora:958577933650362468> {diary.day_data.current_mora}摩拉"
            )
        return result

    async def getAbyss(self, user_id: int, previous: bool):
        client, uid, only_uid = await self.getUserCookie(user_id)
        if only_uid:
            result = errEmbed('你不能使用這項功能!', '請使用`/cookie`的方式註冊後再來試試看')
            return result
        try:
            abyss = await client.get_spiral_abyss(uid, previous=previous)
        except genshin.errors.DataNotPublic:
            result = errEmbed('你的資料並不是公開的!', '請輸入`/stuck`來取得更多資訊')
            return result
        except genshin.errors.GenshinException as e:
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        else:
            rank = abyss.ranks
            if not rank.most_played:
                result = errEmbed(
                    '找不到深淵資料!', '可能是因為你還沒打本期的深淵, 請輸入`/stats`來確認\n深淵資料需最多1小時來接收, 剛打完就來看的得稍等一會')
                return result
            result = []
            embed = defaultEmbed(
                f"第{abyss.season}期深淵",
                f"獲勝場次: {abyss.total_wins}/{abyss.total_battles}\n"
                f"達到{abyss.max_floor}層\n"
                f"共{abyss.total_stars}★"
            )
            embed.add_field(
                name="戰績",
                value=f"單次最高傷害 • {getCharacterName(rank.strongest_strike[0])} • {rank.strongest_strike[0].value}\n"
                f"擊殺王 • {getCharacterName(rank.most_kills[0])} • {rank.most_kills[0].value}次擊殺\n"
                f"最常使用角色 • {getCharacterName(rank.most_played[0])} • {rank.most_played[0].value}次\n"
                f"最多Q使用角色 • {getCharacterName(rank.most_bursts_used[0])} • {rank.most_bursts_used[0].value}次\n"
                f"最多E使用角色 • {getCharacterName(rank.most_skills_used[0])} • {rank.most_skills_used[0].value}次"
            )
            result.append(embed)
            for floor in abyss.floors:
                embed = defaultEmbed(
                    f"第{floor.floor}層 (共{floor.stars}★)", f" ")
                for chamber in floor.chambers:
                    name = f'第{chamber.chamber}間 {chamber.stars}★'
                    chara_list = [[], []]
                    for i, battle in enumerate(chamber.battles):
                        for chara in battle.characters:
                            chara_list[i].append(getCharacterName(chara))
                    topStr = ''
                    bottomStr = ''
                    for top_char in chara_list[0]:
                        topStr += f"• {top_char} "
                    for bottom_char in chara_list[1]:
                        bottomStr += f"• {bottom_char} "
                    embed.add_field(
                        name=name,
                        value=f"【上半】{topStr}\n\n"
                        f"【下半】{bottomStr}",
                        inline=False
                    )
                result.append(embed)
        return result

    async def getBuild(self, element_dict: dict, chara_name: str):
        charas = dict(element_dict)
        if chara_name not in charas:
            return errEmbed('找不到該角色的配置', '')
        else:
            result = []
            name = chara_name
            count = 1
            for build in charas[chara_name]['builds']:
                statStr = ''
                for stat, value in build['stats'].items():
                    statStr += f'{stat} ➜ {value}\n'
                embed = defaultEmbed(
                    f'{name} - 配置{count}',
                    f"武器 • {build['weapon']}\n"
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
                    url=f"https://upload-os-bbs.mihoyo.com/game_record/genshin/character_icon/UI_AvatarIcon_{charas[chara_name]['icon']}.png")
                embed.set_footer(
                    text='[來源](https://bbs.nga.cn/read.php?tid=25843014)')
                result.append([embed, build['weapon']])
            return result

    async def setResinNotification(self, user_id: int, resin_notification_toggle: int, resin_threshold: int, max_notif: int):
        c: aiosqlite.Cursor = await self.db.cursor()
        client, uid, only_uid = await self.getUserCookie(user_id)
        if only_uid:
            result = errEmbed('你不能使用這項功能!', '請使用`/cookie`的方式註冊後再來試試看')
            return result
        try:
            notes = await client.get_notes(uid)
        except genshin.errors.DataNotPublic:
            result = errEmbed('你的資料並不是公開的!', '請輸入`/stuck`來取得更多資訊')
            return result
        except genshin.errors.GenshinException as e:
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        await c.execute('UPDATE genshin_accounts SET resin_notification_toggle = ?, resin_threshold = ? , max_notif = ? WHERE user_id = ?', (resin_notification_toggle, resin_threshold, max_notif, user_id))
        await self.db.commit()
        toggle_str = '開' if resin_notification_toggle == 1 else '關'
        embed = defaultEmbed(
            '🌙 樹脂提醒設定更新成功',
            f'目前開關: {toggle_str}\n'
            f'樹脂提醒閥值: {resin_threshold}\n'
            f'最大提醒數量: {max_notif}'
        )
        return embed

    async def getUserCookie(self, user_id: int):
        c: aiosqlite.Cursor = await self.db.cursor()
        seria_id = 224441463897849856
        await c.execute('SELECT ltuid FROM genshin_accounts WHERE user_id = ?', (user_id,))
        result = await c.fetchone()
        if result[0] is None or result is None:
            await c.execute('SELECT ltuid FROM genshin_accounts WHERE user_id = ?', (seria_id,))
            ltuid = await c.fetchone()
            ltuid = ltuid[0]
            await c.execute('SELECT ltoken FROM genshin_accounts WHERE user_id = ?', (seria_id,))
            ltoken = await c.fetchone()
            ltoken = ltoken[0]
            cookies = {"ltuid": ltuid,
                       "ltoken": ltoken}
            await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (user_id,))
            uid = await c.fetchone()
            uid = uid[0]
            client = genshin.Client(cookies)
            client.lang = "zh-tw"
            client.default_game = genshin.Game.GENSHIN
            client.uids[genshin.Game.GENSHIN] = uid
            only_uid = True
        else:
            await c.execute('SELECT ltoken FROM genshin_accounts WHERE user_id = ?', (user_id,))
            ltoken = await c.fetchone()
            cookies = {"ltuid": result[0],
                       "ltoken": ltoken[0]}
            await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (user_id,))
            uid = await c.fetchone()
            uid = uid[0]
            client = genshin.Client(cookies)
            client.lang = "zh-tw"
            client.default_game = genshin.Game.GENSHIN
            client.uids[genshin.Game.GENSHIN] = uid
            only_uid = False
        return client, uid, only_uid
