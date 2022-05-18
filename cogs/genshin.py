import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional

import discord
import yaml
from discord import (ButtonStyle, Interaction, Member, SelectOption,
                     app_commands)
from discord.app_commands import Choice
from discord.ext import commands, tasks
from discord.ui import Button, Select, View
from utility.AbyssPaginator import AbyssPaginator
from utility.GenshinApp import genshin_app
from utility.utils import defaultEmbed, errEmbed, getWeekdayName, log, openFile, saveFile


class GenshinCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.claim_reward.start()

    def cog_unload(self):
        self.claim_reward.cancel()

    @tasks.loop(hours=24)
    async def claim_reward(self):
        print(log(True, False, 'Schedule', 'Auto claim started'))
        users = openFile('accounts')
        count = 0
        for user_id, value in users.items():
            if 'ltuid' not in value:
                continue
            check, msg = genshin_app.checkUserData(user_id)
            if check == False:
                del users[user_id]
                continue
            await genshin_app.claimDailyReward(user_id)
            count += 1
            await asyncio.sleep(2.0)
        saveFile(users, 'accounts')
        print(log(True, False, 'Schedule',
              f'Auto claim finished, {count} in total'))

    @claim_reward.before_loop
    async def before_claiming_reward(self):
        now = datetime.now().astimezone()
        next_run = now.replace(hour=1, minute=0, second=0)  # 等待到早上1點
        if next_run < now:
            next_run += timedelta(days=1)
        await discord.utils.sleep_until(next_run)

# cookie

    class CookieModal(discord.ui.Modal, title='提交Cookie'):
        cookie = discord.ui.TextInput(
            label='Cookie',
            placeholder='請貼上從網頁上取得的Cookie, 取得方式請使用指令 "/cookie"',
            style=discord.TextStyle.long,
            required=True,
            min_length=100,
            max_length=1500
        )

        async def on_submit(self, interaction: Interaction):
            result = await genshin_app.setCookie(interaction.user.id, self.cookie.value)
            await interaction.response.send_message(result, ephemeral=True)

        async def on_error(self, error: Exception, interaction: Interaction):
            await interaction.response.send_message('發生未知錯誤', ephemeral=True)
            print(error)
# Cookie Submission

    @app_commands.command(
        name='cookie',
        description='設定Cookie')
    @app_commands.rename(option='選項')
    @app_commands.choices(option=[
        Choice(name='1. 顯示說明如何取得Cookie', value=0),
        Choice(name='2. 提交已取得的Cookie', value=1)])
    async def slash_cookie(self, interaction: Interaction, option: int):
        if option == 0:
            embed = defaultEmbed(
                'Cookie設置流程',
                "1.先複製底下的整段程式碼\n"
                "2.電腦或手機使用Chrome開啟Hoyolab並登入帳號 <https://www.hoyolab.com>\n"
                "3.按瀏覽器上面網址的部分, 並確保選取了全部網址\n"
                "4.在網址列先輸入 `java`, 然後貼上程式碼, 確保網址開頭變成 `javascript:`\n"
                "5.按Enter, 網頁會變成顯示你的Cookie, 全選然後複製\n"
                "6.在這裡提交結果, 使用：`/cookie 提交已取得的Cookie`\n"
                "無法理解嗎? 跟著下面的圖示操作吧!")
            embed.set_image(url="https://i.imgur.com/OQ8arx0.gif")
            code_msg = "```script:d=document.cookie; c=d.includes('account_id') || alert('過期或無效的Cookie,請先登出帳號再重新登入!'); c && document.write(d)```"
            await interaction.response.send_message(embed=embed)
            await interaction.followup.send(content=code_msg)
        elif option == 1:
            await interaction.response.send_modal(self.CookieModal())
# /setuid

    @app_commands.command(
        name='setuid',
        description='設定原神UID')
    @app_commands.describe(uid='請輸入要保存的原神UID')
    async def slash_uid(self, interaction: Interaction, uid: int):
        await interaction.response.defer()
        if len(str(uid))!=9:
            await interaction.followup.send(embed=errEmbed('請輸入長度為9的UID!'))
            return
        result = await genshin_app.setUID(interaction.user.id, int(uid))
        await interaction.followup.send(embed=result)

    @app_commands.command(
        name='check',
        description='查看即時便籤, 例如樹脂、洞天寶錢、探索派遣'
    )
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def check(self, interaction: Interaction,
                    member: Optional[Member] = None
                    ):
        member = member or interaction.user
        result = await genshin_app.getRealTimeNotes(member.id, False)
        result.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.response.send_message(embed=result)
# /stats

    @app_commands.command(
        name='stats',
        description='查看原神資料, 如活躍時間、神瞳數量、寶箱數量'
    )
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def stats(self, interaction: Interaction,
                    member: Optional[Member] = None
                    ):
        member = member or interaction.user
        result = await genshin_app.getUserStats(member.id)
        result.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.response.send_message(embed=result)
# /area

    @app_commands.command(
        name='area',
        description='查看區域探索度'
    )
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def area(self, interaction: Interaction,
                   member: Optional[Member] = None
                   ):
        member = member or interaction.user
        result = await genshin_app.getArea(member.id)
        result.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.response.send_message(embed=result)
# /claim

    @app_commands.command(
        name='claim',
        description='領取hoyolab登入獎勵'
    )
    @app_commands.rename(all='全部人', member='其他人')
    @app_commands.describe(all='是否要幫全部已註冊的使用者領取獎勵', member='查看其他群友的資料')
    @app_commands.choices(all=[
        Choice(name='是', value=1),
        Choice(name='否', value=0)])
    async def claim(self, interaction: Interaction, all: Optional[int] = 0, member: Optional[Member] = None):
        if all == 1:
            await interaction.response.send_message(embed=defaultEmbed('⏳ 全員簽到中'))
            users = openFile('accounts')
            for user in users:
                await genshin_app.claimDailyReward(user)
                await asyncio.sleep(1)
            await interaction.followup.send(embed=defaultEmbed('✅ 全員簽到完成'))
        else:
            member = member or interaction.user
            result = await genshin_app.claimDailyReward(member.id)
            result.set_author(name=self.bot.get_user(member.id),
                              icon_url=self.bot.get_user(member.id).avatar)
            await interaction.response.send_message(embed=result)
# /diary

    @app_commands.command(
        name='diary',
        description='查看旅行者日記'
    )
    @app_commands.rename(month='月份', member='其他人')
    @app_commands.describe(month='要查詢的月份', member='查看其他群友的資料')
    @app_commands.choices(month=[
        app_commands.Choice(name='這個月', value=0),
        app_commands.Choice(name='上個月', value=-1),
        app_commands.Choice(name='上上個月', value=-2)]
    )
    async def diary(self, interaction: Interaction,
                    month: int, member: Optional[Member] = None
                    ):
        member = member or interaction.user
        month = datetime.now().month + month
        month = month + 12 if month < 1 else month
        result = await genshin_app.getDiary(member.id, month)
        result.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.response.send_message(embed=result)
# /log

    @app_commands.command(
        name='log',
        description='查看最近25筆原石或摩拉收入紀錄'
    )
    @app_commands.choices(
        type=[app_commands.Choice(name='原石', value=0),
              app_commands.Choice(name='摩拉', value=1)]
    )
    @app_commands.rename(type='類別', member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def log(self, interaction: Interaction, type: int,
                  member: Optional[Member] = None
                  ):
        member = member or interaction.user
        result = await genshin_app.getDiaryLog(member.id)
        if type(result) is discord.Embed:
            await interaction.response.send_message(embed=result)
            return
        embed = result[type]
        embed.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.response.send_message(embed=embed)
# /users

    @app_commands.command(
        name='users',
        description='查看所有已註冊原神帳號'
    )
    async def users(self, interaction: Interaction):
        print(log(False, False, 'Users', interaction.user.id))
        user_dict = genshin_app.getUserData()
        userStr = ""
        count = 0
        for user_id, value in user_dict.items():
            count += 1
            name = self.bot.get_user(user_id)
            userStr = userStr + \
                f"{count}. {name} - {value['uid']}\n"
        embed = defaultEmbed("所有帳號", userStr)
        await interaction.response.send_message(embed=embed)
# /today

    @app_commands.command(
        name='today',
        description='查看今日原石與摩拉收入'
    )
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def today(self, interaction: Interaction,
                    member: Optional[Member] = None
                    ):
        member = member or interaction.user
        result = await genshin_app.getToday(member.id)
        result.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.response.send_message(embed=result)
# /abyss

    @app_commands.command(name='abyss', description='深淵資料查詢')
    @app_commands.rename(check_type='類別', season='期別', floor='層數', member='其他人')
    @app_commands.describe(check_type='想要查看的資料類別',
                           season='這期還是上期?', floor='欲查閱的層數', member='查看其他群友的資料')
    @app_commands.choices(
        check_type=[Choice(name='總覽', value=0),
                    Choice(name='詳細', value=1)],
        season=[Choice(name='上期紀錄', value=0),
                Choice(name='本期紀錄', value=1)],
        floor=[Choice(name='所有樓層', value=0),
               Choice(name='最後一層', value=1)]
    )
    async def abyss(self, interaction: Interaction, check_type: int, season: int = 1, floor: int = 0, member: Optional[Member] = None):
        member = member or interaction.user
        previous = True if season == 0 else False
        result = await genshin_app.getAbyss(member.id, previous)
        if type(result) is not list:
            result.set_author(name=self.bot.get_user(
                member.id), icon_url=self.bot.get_user(member.id).avatar)
        else:
            for embed in result:
                embed.set_author(name=self.bot.get_user(
                    member.id), icon_url=self.bot.get_user(member.id).avatar)
        if type(result) == discord.Embed:
            await interaction.response.send_message(embed=result)
            return
        if check_type == 0:
            await interaction.response.send_message(embed=result[0])
        else:
            if floor == 1:
                await interaction.response.send_message(embed=result[-1])
            else:
                await AbyssPaginator(interaction, result[1:]).start(embeded=True)
# /stuck

    @app_commands.command(
        name='stuck',
        description='找不到資料?'
    )
    async def stuck(self, interaction: Interaction):
        embed = defaultEmbed(
            "已經註冊,但有些資料找不到?",
            "1. 至hoyolab網頁中\n"
            "2. 點擊頭像\n"
            "3. personal homepage\n"
            "4. 右邊會看到genshin impact\n"
            "5. 點擊之後看到設定按鈕\n"
            "6. 打開 Do you want to enable real time-notes")
        await interaction.response.send_message(embed=embed)
# /farm

    @app_commands.command(
        name='farm',
        description='查看原神今日可刷素材'
    )
    async def farm(self, interaction: Interaction):
        print(log(False, False, 'Farm', interaction.user.id))
        weekdayGet = datetime.today().weekday()
        embedFarm = defaultEmbed(
            f"今天({getWeekdayName(weekdayGet)})可以刷的副本材料", " ")
        if weekdayGet == 0 or weekdayGet == 3:
            embedFarm.set_image(
                url="https://media.discordapp.net/attachments/823440627127287839/958862746349346896/73268cfab4b4a112.png")
        elif weekdayGet == 1 or weekdayGet == 4:
            embedFarm.set_image(
                url="https://media.discordapp.net/attachments/823440627127287839/958862746127060992/5ac261bdfc846f45.png")
        elif weekdayGet == 2 or weekdayGet == 5:
            embedFarm.set_image(
                url="https://media.discordapp.net/attachments/823440627127287839/958862745871220796/0b16376c23bfa1ab.png")
        elif weekdayGet == 6:
            embedFarm = defaultEmbed(
                f"今天({getWeekdayName(weekdayGet)})可以刷的副本材料", "禮拜日可以刷所有素材 (❁´◡`❁)")
        await interaction.response.send_message(embed=embedFarm)

    class BuildCharactersDropdown(Select):  # 角色配置下拉選單(依元素分類)
        def __init__(self, index: int):
            elemenet_chinese = ['風', '冰', '雷', '岩', '水', '火']
            elements = ['anemo', 'cryo', 'electro', 'geo', 'hydro', 'pyro']
            with open(f'data/builds/{elements[index]}.yaml', 'r', encoding='utf-8') as f:
                self.build_dict = yaml.full_load(f)
            options = []
            for character, value in self.build_dict.items():
                options.append(SelectOption(label=character, value=character))
            super().__init__(
                placeholder=f'{elemenet_chinese[index]}元素角色', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            result = await genshin_app.getBuild(self.build_dict, str(self.values[0]))
            await interaction.response.send_message(embed=result)

    class UserCharactersDropdown(Select):  # 使用者角色下拉選單(依元素分類)
        def __init__(self, index: int, user_characters):
            elemenet_chinese = ['風', '冰', '雷', '岩', '水', '火']
            elements = ['Anemo', 'Cryo', 'Electro', 'Geo', 'Hydro', 'Pyro']
            options = []
            self.user_characters = user_characters
            for character in user_characters:
                if character.element == elements[index]:
                    options.append(SelectOption(
                        label=f'C{character.constellation}R{character.weapon.refinement} {character.name}', value=character.name))
            if not options:
                options.append(SelectOption(label='無角色',value='無角色'))
            super().__init__(
                placeholder=f'{elemenet_chinese[index]}元素角色', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            if self.values[0]=='無角色':
                await interaction.response.send_message(embed=errEmbed('真的沒有角色','不應該這樣嗎?\n可能是因為你只有用`/setuid`註冊\n想查看完整角色請使用`/cookie`註冊'))
            else:
                await interaction.response.send_message(embed=genshin_app.parseCharacter(self.user_characters, self.values[0], interaction.user))

    class CharactersDropdownView(View):  # 角色配置下拉選單的view
        def __init__(self, index: int, user_characters):
            super().__init__(timeout=None)
            if user_characters is None:
                self.add_item(GenshinCog.BuildCharactersDropdown(index))
            else:
                self.add_item(GenshinCog.UserCharactersDropdown(
                    index, user_characters))

    class ElementButton(Button):  # 元素按鈕
        def __init__(self, index: int, user_characters):
            elemenet_chinese = ['風', '冰', '雷', '岩', '水', '火']
            self.index = index
            self.user_characters = user_characters
            super().__init__(
                label=f'{elemenet_chinese[index]}元素', style=ButtonStyle.blurple, row=index % 2)

        async def callback(self, i: Interaction):
            view = GenshinCog.CharactersDropdownView(
                self.index, self.user_characters)
            await i.response.send_message(view=view, ephemeral=True)

    class ElementChooseView(View):  # 選擇元素按鈕的view
        def __init__(self, user_characters=None):
            super().__init__(timeout=None)
            for i in range(0, 6):
                self.add_item(GenshinCog.ElementButton(i, user_characters))

    # /build
    @app_commands.command(name='build', description='查看角色推薦主詞條、畢業面板、不同配置等')
    async def build(self, i: Interaction):
        view = GenshinCog.ElementChooseView()
        await i.response.send_message(embed=defaultEmbed('請選擇想查看角色的元素', '如果你是用`/setuid`註冊的, 僅會顯示等級前8的角色'), view=view, ephemeral=True)

    # /characters
    @app_commands.command(name='characters', description='查看已擁有角色資訊, 如命座、親密度、聖遺物')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def characters(self, i: Interaction, member: Optional[Member] = None):
        member = member or i.user
        user_characters = await genshin_app.getUserCharacters(user_id=member.id)
        if type(user_characters) is discord.Embed:
            await i.response.send_message(embed=user_characters)
            return
        view = GenshinCog.ElementChooseView(user_characters)
        await i.response.send_message(embed=defaultEmbed('請選擇想查看角色的元素', ''), view=view, ephemeral=True)

# /rate

    @app_commands.command(name='rate', description='聖遺物評分計算(根據副詞條)')
    @app_commands.rename(type='聖遺物類型', crit_dmg='暴傷', crit_rate='暴擊率', atk='攻擊百分比')
    @app_commands.choices(type=[
        Choice(name='生之花', value=0),
        Choice(name='死之羽', value=1),
        # Choice(name='時之沙', value=2),
        Choice(name='空之杯', value=3)])
    # Choice(name='理之冠', value=4)])
    async def rate(self, interaction: Interaction, type: int, crit_dmg: str, crit_rate: str, atk: str):
        crit_dmg = int(re.search(r'\d+', crit_dmg).group())
        crit_rate = int(re.search(r'\d+', crit_rate).group())
        atk = int(re.search(r'\d+', atk).group())
        score = crit_rate*2 + atk*1.3 + crit_dmg*1
        typeStr = ''
        if type == 0:
            typeStr = '生之花'
        elif type == 1:
            typeStr = '死之羽'
        elif type == 2:
            typeStr = '時之沙'
        elif type == 3:
            typeStr = '空之杯'
        else:
            typeStr = '理之冠'
        if type == 0 or type == 1:
            if score >= 40:
                tier_url = 'https://www.expertwm.com/static/images/badges/badge-s.png'
                desc = '極品聖遺物, 足以用到關服'
            elif score >= 30:
                tier_url = 'https://www.expertwm.com/static/images/badges/badge-a.png'
                desc = '良品, 追求強度的人的目標'
            elif score >= 20:
                tier_url = 'https://www.expertwm.com/static/images/badges/badge-b.png'
                desc = '及格, 可以用了'
            else:
                tier_url = 'https://www.expertwm.com/static/images/badges/badge-c.png'
                desc = '過渡用, 繼續刷'
        else:
            if score >= 50:
                tier_url = 'https://www.expertwm.com/static/images/badges/badge-s.png'
                desc = '極品聖遺物, 足以用到關服'
            elif score >= 40:
                tier_url = 'https://www.expertwm.com/static/images/badges/badge-a.png'
                desc = '良品, 追求強度的人的目標'
            elif score >= 30:
                tier_url = 'https://www.expertwm.com/static/images/badges/badge-b.png'
                desc = '及格, 可以用了'
            else:
                tier_url = 'https://www.expertwm.com/static/images/badges/badge-c.png'
                desc = '過渡用, 繼續刷'
        result = defaultEmbed(
            '聖遺物評分結果',
            f'總分: {score}\n'
            f'「{desc}」'
        )
        result.add_field(
            name='詳情',
            value=f'類型: {typeStr}\n'
            f'暴傷: {crit_dmg}%\n'
            f'暴擊率: {crit_rate}%\n'
            f'攻擊百分比: {atk}%'
        )
        result.set_thumbnail(url=tier_url)
        result.set_footer(
            text='[來源](https://forum.gamer.com.tw/C.php?bsn=36730&snA=11316)')
        await interaction.response.send_message(embed=result)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GenshinCog(bot))
