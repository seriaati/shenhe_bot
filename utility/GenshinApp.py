from datetime import datetime, timedelta
import genshin
import yaml
from utility.utils import errEmbed, defaultEmbed, log
from typing import Union, Tuple


class GenshinApp:
    def __init__(self) -> None:
        try:
            with open('data/accounts.yaml', 'r', encoding="utf-8") as f:
                self.user_data = yaml.full_load(f)
        except:
            self.user_data = {}

    async def getRealTimeNotes(self, user_id: int):
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
            result = errEmbed('太快了!', '目前原神API請求次數過多, 請稍後再試')
        except Exception as e:
            print(log(False, True, 'Notes', e))
        else:
            if not notes.expeditions:
                hr = 0
                mn = 0
                exTime = 0
            else:
                unfinExp = []
                for expedition in notes.expeditions:
                    if(expedition.status == "Ongoing"):
                        unfinExp.append(expedition.remaining_time)
                if not unfinExp:
                    hr = 0
                    mn = 0
                else:
                    exTime = min(unfinExp, default="EMPTY")
                    hr, mn = divmod(exTime // 60, 60)
            time = notes.remaining_resin_recovery_time
            hours, minutes = divmod(time // 60, 60)
            fullTime = datetime.now() + timedelta(hours=hours)
            transDelta = notes.transformer_recovery_time.replace(
                tzinfo=None) - datetime.now()
            transDeltaSec = transDelta.total_seconds()
            transDay = transDeltaSec // (24 * 3600)
            transDeltaSec = transDeltaSec % (24 * 3600)
            transHour = transDeltaSec // 3600
            transDeltaSec %= 3600
            transMin = transDeltaSec // 60
            transStr = f"{int(transDay)}天 {int(transHour)}小時 {int(transMin)}分鐘"
            if transDeltaSec <= 0:
                transStr = "質變儀已準備就緒"
            printTime = '{:%H:%M}'.format(fullTime)
            result = defaultEmbed(
                f"{nickname}: 即時便籤",
                f"<:resin:956377956115157022> 目前樹脂: {notes.current_resin}/{notes.max_resin}\n"
                f"於 {hours:.0f} 小時 {minutes:.0f} 分鐘後填滿(即{printTime})\n"
                f"<:daily:956383830070140938> 已完成的每日數量: {notes.completed_commissions}/{notes.max_commissions}\n"
                f"<:realm:956384011750613112> 目前塵歌壺幣數量: {notes.current_realm_currency}/{notes.max_realm_currency}\n"
                f"<:expedition:956385168757780631> 已結束的探索派遣數量: {sum(expedition.finished for expedition in notes.expeditions)}/{len(notes.expeditions)}\n"
                f"最快結束的派遣時間: {hr:.0f}小時 {mn:.0f}分鐘"
                f"\n<:transformer:966156330089971732> 質變儀剩餘冷卻時間: {transStr}"
            )
        return result

    async def getUserStats(self, user_id:int):
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        uid = self.user_data[user_id]['uid']
        client, nickname = self.getUserCookie(user_id)
        try:
            genshinUser = await client.get_partial_genshin_user(uid)
        except genshin.errors.GenshinException as e:
            print(log(False, True, 'Notes', f'{user_id}: {e}'))
            result = errEmbed('太快了!', '目前原神API請求次數過多, 請稍後再試')
        except Exception as e:
            print(log(False, True, 'Notes', e))
        else:
            days = genshinUser.stats.days_active
            char = genshinUser.stats.characters
            achieve = genshinUser.stats.achievements
            anemo = genshinUser.stats.anemoculi
            geo = genshinUser.stats.geoculi
            electro = genshinUser.stats.electroculi
            comChest = genshinUser.stats.common_chests
            exChest = genshinUser.stats.exquisite_chests
            luxChest = genshinUser.stats.luxurious_chests
            abyss = genshinUser.stats.spiral_abyss
            result = defaultEmbed(f"{nickname}: 統計數據","")
            result.add_field(name='綜合',value=
                f"📅 活躍天數: {days}\n"
                f"<:expedition:956385168757780631> 角色數量: {char}/50\n"
                f"📜 成就數量:{achieve}/639\n"
                f"🌙 深淵已達: {abyss}層"
            , inline = False)
            result.add_field(name='神瞳',value=
                f"<:anemo:956719995906322472> 風神瞳: {anemo}/66\n"
                f"<:geo:956719995440730143> 岩神瞳: {geo}/131\n"
                f"<:electro:956719996262821928> 雷神瞳: {electro}/181"
            , inline = False)
            result.add_field(name='寶箱', value=
                f"一般寶箱: {comChest}\n"
                f"稀有寶箱: {exChest}\n"
                f"珍貴寶箱: {luxChest}"
            , inline = False)
        return result

    def checkUserData(self, user_id: int):
        with open(f'data/accounts.yaml', encoding='utf-8') as file:
            users = yaml.full_load(file)
        if user_id not in users:
            return False, errEmbed('找不到原神帳號!', '請輸入`!reg`來查看註冊方式')
        else:
            return True, None

    def getUserCookie(self, user_id: int):
        with open(f'data/accounts.yaml', encoding='utf-8') as file:
            users = yaml.full_load(file)
        cookies = {"ltuid": users[user_id]['ltuid'],
                    "ltoken": users[user_id]['ltoken']}
        uid = users[user_id]['uid']
        nickname = users[user_id]['name']
        client = genshin.Client(cookies)
        client.lang = "zh-tw"
        client.default_game = genshin.Game.GENSHIN
        client.uids[genshin.Game.GENSHIN] = uid
        return client, nickname


genshin_app = GenshinApp()
