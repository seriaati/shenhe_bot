from datetime import datetime, timedelta
import genshin
import yaml
from utility.classes import Character
from utility.utils import errEmbed, defaultEmbed, log, getCharacterName, getWeekdayName


class GenshinApp:
    def __init__(self) -> None:
        try:
            with open('data/accounts.yaml', 'r', encoding="utf-8") as f:
                self.user_data = yaml.full_load(f)
        except:
            self.user_data = {}

    async def claimDailyReward(self, user_id:int):
        print(log(False, False, 'Claim', f'{user_id}'))
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client, nickname = self.getUserCookie(user_id)
        try:
            reward = await client.claim_daily_reward()
        except genshin.errors.AlreadyClaimed:
            result = errEmbed(f'你已經領過今天的獎勵了!','')
        except genshin.errors.GenshinException as e:
            print(log(False, True, 'Claim', e))
            result = errEmbed(f'簽到失敗: {e.original}','')
        except Exception as e:
            print(log(False, True, 'Claim', e))
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        else:
            result = defaultEmbed(
                f'{nickname}: 今日簽到成功',
                f'獲得 {reward.amount}x {reward.name}'
            )
        return result
    
    async def getRealTimeNotes(self, user_id: int):
        print(log(False, False, 'Notes', user_id))
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        uid = self.user_data[user_id]['uid']
        client, nickname = self.getUserCookie(user_id)
        try:
            notes = await client.get_notes(uid)
        except genshin.errors.DataNotPublic as e:
            print(log(False, True, 'Notes', f'{user_id}: {e}'))
            result = errEmbed('你的資料並不是公開的!', '請輸入`!stuck`來取得更多資訊')
        except genshin.errors.GenshinException as e:
            print(log(False, True, 'Notes', f'{user_id}: {e}'))
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        except Exception as e:
            print(log(False, True, 'Notes', e))
        else:
            if notes.current_resin == notes.max_resin:
                resin_recover_time = '已滿'
            else:
                day_msg = '今天' if notes.resin_recovery_time.day == datetime.now().day else '明天'
                resin_recover_time = f'{day_msg} {notes.resin_recovery_time.strftime("%H:%M")}'
            
            if notes.current_realm_currency == notes.max_realm_currency:
                realm_recover_time = '已滿'
            else:
                weekday_msg = getWeekdayName(notes.realm_currency_recovery_time.weekday())
                realm_recover_time = f'{weekday_msg} {notes.realm_currency_recovery_time.strftime("%H:%M")}'
            if notes.transformer_recovery_time != None:
                if notes.remaining_transformer_recovery_time < 10:
                    transformer_recovery_time = '已可使用'
                else:
                    t = timedelta(seconds=notes.remaining_transformer_recovery_time+10)
                    if t.days > 0:
                        transformer_recovery_time = f'{t.days} 天'
                    elif t.seconds > 3600:
                        transformer_recovery_time = f'{round(t.seconds/3600)} 小時'
                    else:
                        transformer_recovery_time = f'{round(t.seconds/60)} 分'
            else:
                transformer_recovery_time = '質變儀不存在'
            result = defaultEmbed(
                f"{nickname}: 即時便籤",
                f"<:daily:956383830070140938> 已完成的每日數量: {notes.completed_commissions}/{notes.max_commissions}\n"
                f"<:transformer:966156330089971732> 質變儀剩餘時間: {transformer_recovery_time}"
            )
            result.add_field(
                name='樹脂',
                value=
                f"<:resin:956377956115157022> 目前樹脂: {notes.current_resin}/{notes.max_resin}\n"
                f"樹脂回滿時間: {resin_recover_time}\n"
                f'週本樹脂減半: 剩餘 {notes.remaining_resin_discounts}/3 次',
                inline=False
            )
            result.add_field(
                name='塵歌壺',
                value=
                f"<:realm:956384011750613112> 目前洞天寶錢數量: {notes.current_realm_currency}/{notes.max_realm_currency}\n"
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

    async def getUserStats(self, user_id:int):
        print(log(False, False, 'Stats', user_id))
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        uid = self.user_data[user_id]['uid']
        client, nickname = self.getUserCookie(user_id)
        try:
            genshinUser = await client.get_partial_genshin_user(uid)
        except genshin.errors.GenshinException as e:
            print(log(False, True, 'Notes', f'{user_id}: {e}'))
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        except Exception as e:
            print(log(False, True, 'Notes', e))
        else:
            characters = await client.get_calculator_characters()
            result = defaultEmbed(f"{nickname}: 統計數據","")
            result.add_field(name='綜合',value=
                f"📅 活躍天數: {genshinUser.stats.days_active}\n"
                f"<:expedition:956385168757780631> 角色數量: {genshinUser.stats.characters}/{len(characters)}\n"
                f"📜 成就數量:{genshinUser.stats.achievements}/639\n"
                f"🌙 深淵已達: {genshinUser.stats.spiral_abyss}層"
            , inline = False)
            result.add_field(name='神瞳',value=
                f"<:anemo:956719995906322472> 風神瞳: {genshinUser.stats.anemoculi}/66\n"
                f"<:geo:956719995440730143> 岩神瞳: {genshinUser.stats.geoculi}/131\n"
                f"<:electro:956719996262821928> 雷神瞳: {genshinUser.stats.electroculi}/181"
            , inline = False)
            result.add_field(name='寶箱', value=
                f"一般寶箱: {genshinUser.stats.common_chests}\n"
                f"稀有寶箱: {genshinUser.stats.exquisite_chests}\n"
                f"珍貴寶箱: {genshinUser.stats.luxurious_chests}"
            , inline = False)
        return result

    async def getArea(self, user_id:int):
        print(log(False, False, 'Area', user_id))
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        uid = self.user_data[user_id]['uid']
        client, nickname = self.getUserCookie(user_id)
        try:
            genshinUser = await client.get_partial_genshin_user(uid)
        except genshin.errors.GenshinException as e:
            print(log(False, True, 'Area', f'{user_id}: {e}'))
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        except Exception as e:
            print(log(False, True, 'Area', e))
        else:
            explorations = genshinUser.explorations
            exploreStr = ""
            for exploration in explorations:
                exploreStr += f"{exploration.name}: {exploration.explored}% • Lvl.{exploration.level}\n"
            result = defaultEmbed(
                f"{nickname}: 探索度",
                exploreStr
            )
        return result

    async def getDiary(self, user_id:int, month:int):
        print(log(False, False, 'Diary', user_id))
        currentMonth = datetime.now().month
        if month > currentMonth:
            result = errEmbed('不可輸入大於目前時間的月份','')
            return result
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client, nickname = self.getUserCookie(user_id)
        try:
            diary = await client.get_diary(month=month)
        except genshin.errors.GenshinException as e:
            print(log(False, True, 'Diary', f'{user_id}: {e}'))
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        except Exception as e:
            print(log(False, True, 'Diary', e))
        else:
            d = diary.data 
            result = defaultEmbed(
                f'{nickname}: 旅行者日記  •  {month}月',
                f'<:primo:958555698596290570> 原石收入比上個月{"增加" if d.primogems_rate > 0 else "減少"}了{abs(d.primogems_rate)}%\n'
                f'<:mora:958577933650362468> 摩拉收入比上個月{"增加" if d.mora_rate > 0 else "減少"}了{abs(d.mora_rate)}%'
            )
            result.add_field(
                name='本月共獲得',
                value=
                f'<:primo:958555698596290570> {d.current_primogems} • 上個月: {d.last_primogems}\n'
                f'<:mora:958577933650362468> {d.current_mora} • 上個月: {d.last_mora}',
                inline=False
            )
            msg = ''
            for cat in d.categories:
                msg += f'{cat.name}: {cat.percentage}%\n'
            result.add_field(name=f'收入分類', value=msg, inline=False)
        return result

    async def getDiaryLog(self, user_id: int):
        print(log(False, False, 'Diary Log', user_id))
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client, nickname = self.getUserCookie(user_id)
        try:
            diary = await client.get_diary()
        except genshin.errors.DataNotPublic as e:
            print(log(False, True, 'Notes', f'{user_id}: {e}'))
            result = errEmbed('你的資料並不是公開的!', '請輸入`!stuck`來取得更多資訊')
        except genshin.errors.GenshinException as e:
            print(log(False, True, 'Notes', f'{user_id}: {e}'))
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        except Exception as e:
            print(log(False, True, 'Notes', e))
        else:
            primoLog = ''
            moraLog = ''
            result = []
            async for action in client.diary_log(limit=25):
                primoLog = primoLog+f"{action.action} - {action.amount} 原石"+"\n"
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
        print(log(False, False, 'Character', user_id))
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        uid = self.user_data[user_id]['uid']
        client, nickname = self.getUserCookie(user_id)
        try:
            char = await client.get_genshin_characters(uid)
        except genshin.errors.DataNotPublic as e:
            print(log(False, True, 'Character', f'{user_id}: {e}'))
            result = errEmbed('你的資料並不是公開的!', '請輸入`!stuck`來取得更多資訊')
        except genshin.errors.GenshinException as e:
            print(log(False, True, 'Character', f'{user_id}: {e}'))
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        except Exception as e:
            print(log(False, True, 'Character', e))
        else:
            characters = []
            result = []
            for character in char:
                weapon = character.weapon
                artifacts = character.artifacts
                artifactList = []
                artifactIconList = []
                for artifact in artifacts:
                    artifactList.append(artifact.name)
                    artifactIconList.append(artifact.icon)
                characters.append(Character(getCharacterName(character), character.level, character.constellation, character.icon, character.friendship, weapon.name, weapon.refinement, weapon.level, artifactList, artifactIconList))
            for character in characters:
                artifactStr = ""
                for artifact in character.artifacts:
                    artifactStr = artifactStr + "• " + artifact + "\n"
                embed = defaultEmbed(
                    f"{character.name}: C{character.constellation} R{character.refinement}",
                    f"Lvl {character.level}\n"
                    f"好感度 {character.friendship}\n"
                    f"武器 {character.weapon}, lvl{character.weaponLevel}\n"
                    f"{artifactStr}")
                embed.set_thumbnail(url=f"{character.iconUrl}")
                result.append(embed)
        return result

    async def getToday(self, user_id: int):
        print(log(False, False, 'Notes', user_id))
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client, nickname = self.getUserCookie(user_id)
        try:
            diary = await client.get_diary()
        except genshin.errors.DataNotPublic as e:
            print(log(False, True, 'Notes', f'{user_id}: {e}'))
            result = errEmbed('你的資料並不是公開的!', '請輸入`!stuck`來取得更多資訊')
        except genshin.errors.GenshinException as e:
            print(log(False, True, 'Notes', f'{user_id}: {e}'))
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        except Exception as e:
            print(log(False, True, 'Notes', e))
        else:
            result = defaultEmbed(
                f"{nickname}: 今日收入",
                f"<:primo:958555698596290570> {diary.day_data.current_primogems}原石\n"
                f"<:mora:958577933650362468> {diary.day_data.current_mora}摩拉"
            )
        return result

    async def getAbyss(self, user_id: int, previous: bool):
        print(log(False, False, 'Abyss', user_id))
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        uid = self.user_data[user_id]['uid']
        client, nickname = self.getUserCookie(user_id)
        try:
            abyss = await client.get_spiral_abyss(uid, previous=previous)
        except genshin.errors.DataNotPublic as e:
            print(log(False, True, 'Abyss', f'{user_id}: {e}'))
            result = errEmbed('你的資料並不是公開的!', '請輸入`!stuck`來取得更多資訊')
        except genshin.errors.GenshinException as e:
            print(log(False, True, 'Abyss', f'{user_id}: {e}'))
            result = errEmbed(
                '某個錯誤',
                '太神奇了! 恭喜你獲得這個神秘的錯誤, 快告訴小雪吧!\n'
                f'```{e}```'
            )
        except Exception as e:
            print(log(False, True, 'Abyss', e))
        else:
            rank = abyss.ranks
            print(rank)
            if not rank:
                return errEmbed('找不到深淵資料!','可能是因為你還沒打深淵, 請輸入`!stats`來確認')
            result = []
            embed = defaultEmbed(
                f"{nickname}: 第{abyss.season}期深淵",
                f"獲勝場次: {abyss.total_wins}/{abyss.total_battles}\n"
                f"達到{abyss.max_floor}層\n"
                f"共{abyss.total_stars}★"
            )
            embed.add_field(
                name="戰績",
                value=f"單次最高傷害: {getCharacterName(rank.strongest_strike[0])} • {rank.strongest_strike[0].value}\n"
                f"擊殺王 • {getCharacterName(rank.most_kills[0])} • {rank.most_kills[0].value}次擊殺\n"
                f"最常使用角色 • {getCharacterName(rank.most_played[0])} • {rank.most_played[0].value}次\n"
                f"最多Q使用角色 • {getCharacterName(rank.most_bursts_used[0])} • {rank.most_bursts_used[0].value}次\n"
                f"最多E使用角色 • {getCharacterName(rank.most_skills_used[0])} • {rank.most_skills_used[0].value}次"
            )
            result.append(embed)
            for floor in abyss.floors:
                embed = defaultEmbed(f"第{floor.floor}層 (共{floor.stars}★)", f" ")
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

    def checkUserData(self, user_id: int):
        with open(f'data/accounts.yaml', encoding='utf-8') as file:
            users = yaml.full_load(file)
        if user_id not in users:
            return False, errEmbed('找不到原神帳號!', '請輸入`!reg`來查看註冊方式')
        else:
            return True, None

    def getUserCookie(self, user_id: int):
        with open(f'data/accounts.yaml', encoding='utf-8') as f:
            users = yaml.full_load(f)
        cookies = {"ltuid": users[user_id]['ltuid'],
                    "ltoken": users[user_id]['ltoken']}
        uid = users[user_id]['uid']
        nickname = users[user_id]['name']
        client = genshin.Client(cookies)
        client.lang = "zh-tw"
        client.default_game = genshin.Game.GENSHIN
        client.uids[genshin.Game.GENSHIN] = uid
        return client, nickname

    def saveUserData(self):
        with open('data/accounts.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(self.user_data, f)


genshin_app = GenshinApp()
