from datetime import datetime
import GGanalysislib
import re
import discord
from discord import Interaction, app_commands
from discord.ext import commands
from discord import ui
from discord.app_commands import Choice
import genshin
import yaml
from utility.utils import defaultEmbed, errEmbed, getWeekdayName, log, openFile, saveFile
from discord import Member
from utility.GenshinApp import genshin_app
from typing import List, Optional
from utility.AbyssPaginator import AbyssPaginator
from utility.WishPaginator import WishPaginator


class GenshinCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('data/builds/anemo.yaml', 'r', encoding='utf-8') as f:
            self.anemo_dict = yaml.full_load(f)
        with open('data/builds/cryo.yaml', 'r', encoding='utf-8') as f:
            self.cryo_dict = yaml.full_load(f)
        with open('data/builds/electro.yaml', 'r', encoding='utf-8') as f:
            self.electro_dict = yaml.full_load(f)
        with open('data/builds/geo.yaml', 'r', encoding='utf-8') as f:
            self.geo_dict = yaml.full_load(f)
        with open('data/builds/hydro.yaml', 'r', encoding='utf-8') as f:
            self.hydro_dict = yaml.full_load(f)
        with open('data/builds/pyro.yaml', 'r', encoding='utf-8') as f:
            self.pyro_dict = yaml.full_load(f)
#cookie
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

    @app_commands.command(
        name='cookie',
        description='設定Cookie')
    @app_commands.rename(option='選項')
    @app_commands.choices(option=[
        Choice(name='1. 顯示說明如何取得Cookie', value=0),
        Choice(name='2. 提交已取得的Cookie', value=1)])
    async def slash_cookie(self, interaction: Interaction, option: int):
        if option == 0:
            help_msg = (
                "1.先複製底下的整段程式碼\n"
                "2.PC或手機使用Chrome開啟Hoyolab登入帳號 <https://www.hoyolab.com>\n"
                "3.在網址列先輸入 `java`, 然後貼上程式碼, 確保網址開頭變成 `javascript:`\n"
                "4.按Enter, 網頁會變成顯示你的Cookie, 全選然後複製\n"
                "5.在這裡提交結果, 使用：`/cookie 提交已取得的Cookie`\n"
                "https://i.imgur.com/OQ8arx0.gif")
            code_msg = "```script:d=document.cookie; c=d.includes('account_id') || alert('過期或無效的Cookie,請先登出帳號再重新登入!'); c && document.write(d)```"
            await interaction.response.send_message(content=help_msg)
            await interaction.followup.send(content=code_msg)
        elif option == 1:
            await interaction.response.send_modal(self.CookieModal())
#/setuid
    @app_commands.command(
        name='setuid',
        description='設定原神UID')
    @app_commands.describe(uid='請輸入要保存的原神UID')
    async def slash_uid(self, interaction: Interaction, uid: int):
        await interaction.response.defer(ephemeral=True)
        result = await genshin_app.setUID(interaction.user.id, int(uid))
        await interaction.edit_original_message(content=result)

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
#/stats
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
#/area
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
#/claim
    @app_commands.command(
        name='claim',
        description='領取hoyolab登入獎勵'
    )
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def claim(self, interaction: Interaction,
                    member: Optional[Member] = None
                    ):
        member = member or interaction.user
        result = await genshin_app.claimDailyReward(member.id)
        result.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.response.send_message(embed=result)
#/diary
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
#/log
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
        result.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.response.send_message(embed=result[type])
#/users
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
#/today
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
#/abyss
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
#/stuck
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
#/farm
    @app_commands.command(
        name='farm',
        description='查看原神今日可刷素材'
    )
    async def farm(self, interaction: Interaction):
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
#/build
    build = app_commands.Group(
        name='build', description='查看角色推薦主詞條、畢業面板、不同配置等')

    def get_anemo_choices():
        characters = openFile('/builds/anemo')
        character_list = []
        for name, value in characters.items():
            character_list.append(Choice(name=name, value=name))
        return character_list

    @build.command(name='風', description='查看風元素角色的配置、武器、畢業面板')
    @app_commands.rename(chara='角色')
    @app_commands.choices(chara=get_anemo_choices())
    async def anemo_build(self, interaction: Interaction, chara: str):
        result = await genshin_app.getBuild(self.anemo_dict, str(chara))
        await interaction.response.send_message(embed=result)

    def get_cryo_choices():
        characters = openFile('/builds/cryo')
        character_list = []
        for name, value in characters.items():
            character_list.append(Choice(name=name, value=name))
        return character_list

    @build.command(name='冰', description='查看冰元素角色的配置、武器、畢業面板')
    @app_commands.rename(chara='角色')
    @app_commands.choices(chara=get_cryo_choices())
    async def anemo_build(self, interaction: Interaction, chara: str):
        result = await genshin_app.getBuild(self.cryo_dict, str(chara))
        await interaction.response.send_message(embed=result)

    def get_electro_choices():
        characters = openFile('/builds/electro')
        character_list = []
        for name, value in characters.items():
            character_list.append(Choice(name=name, value=name))
        return character_list

    @build.command(name='雷', description='查看雷元素角色的配置、武器、畢業面板')
    @app_commands.rename(chara='角色')
    @app_commands.choices(chara=get_electro_choices())
    async def electro_build(self, interaction: Interaction, chara: str):
        result = await genshin_app.getBuild(self.electro_dict, str(chara))
        await interaction.response.send_message(embed=result)

    def get_geo_choices():
        characters = openFile('/builds/geo')
        character_list = []
        for name, value in characters.items():
            character_list.append(Choice(name=name, value=name))
        return character_list

    @build.command(name='岩', description='查看岩元素角色的配置、武器、畢業面板')
    @app_commands.rename(chara='角色')
    @app_commands.choices(chara=get_geo_choices())
    async def geo_build(self, interaction: Interaction, chara: str):
        result = await genshin_app.getBuild(self.geo_dict, str(chara))
        await interaction.response.send_message(embed=result)

    def get_hydro_choices():
        characters = openFile('/builds/hydro')
        character_list = []
        for name, value in characters.items():
            character_list.append(Choice(name=name, value=name))
        return character_list

    @build.command(name='水', description='查看水元素角色的配置、武器、畢業面板')
    @app_commands.rename(chara='角色')
    @app_commands.choices(chara=get_hydro_choices())
    async def anemo_build(self, interaction: Interaction, chara: str):
        result = await genshin_app.getBuild(self.hydro_dict, str(chara))
        await interaction.response.send_message(embed=result)

    def get_pyro_choices():
        characters = openFile('/builds/pyro')
        character_list = []
        for name, value in characters.items():
            character_list.append(Choice(name=name, value=name))
        return character_list

    @build.command(name='火', description='查看火元素角色的配置、武器、畢業面板')
    @app_commands.rename(chara='角色')
    @app_commands.choices(chara=get_pyro_choices())
    async def pyro_build(self, interaction: Interaction, chara: str):
        result = await genshin_app.getBuild(self.pyro_dict, str(chara))
        await interaction.response.send_message(embed=result)

    char = app_commands.Group(
        name='char', description='查看已擁有角色資訊, 如命座、親密度、聖遺物')

    @char.command(name='風', description='查看已擁有風元素角色資訊, 如命座、親密度、聖遺物')
    @app_commands.rename(char='角色', member='其他人')
    @app_commands.describe(char='僅能查看自己擁有角色的資料', member='查看其他群友的資料')
    @app_commands.choices(char=get_anemo_choices())
    async def anemo_char(self, interaction: Interaction, char: str,
                         member: Optional[Member] = None
                         ):
        member = member or interaction.user
        await interaction.response.defer()
        result = await genshin_app.getUserCharacters(char, member.id)
        result.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.followup.send(embed=result)

    @char.command(name='冰', description='查看已擁有冰元素角色資訊, 如命座、親密度、聖遺物')
    @app_commands.rename(char='角色', member='其他人')
    @app_commands.describe(char='僅能查看自己擁有角色的資料', member='查看其他群友的資料')
    @app_commands.choices(char=get_cryo_choices())
    async def cryo_char(self, interaction: Interaction, char: str,
                        member: Optional[Member] = None
                        ):
        member = member or interaction.user
        await interaction.response.defer()
        result = await genshin_app.getUserCharacters(char, member.id)
        result.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.followup.send(embed=result)

    @char.command(name='雷', description='查看已擁有雷元素角色資訊, 如命座、親密度、聖遺物')
    @app_commands.rename(char='角色', member='其他人')
    @app_commands.describe(char='僅能查看自己擁有角色的資料', member='查看其他群友的資料')
    @app_commands.choices(char=get_electro_choices())
    async def electro_char(self, interaction: Interaction, char: str,
                           member: Optional[Member] = None
                           ):
        member = member or interaction.user
        await interaction.response.defer()
        result = await genshin_app.getUserCharacters(char, member.id)
        result.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.followup.send(embed=result)

    @char.command(name='岩', description='查看已擁有岩元素角色資訊, 如命座、親密度、聖遺物')
    @app_commands.rename(char='角色', member='其他人')
    @app_commands.describe(char='僅能查看自己擁有角色的資料', member='查看其他群友的資料')
    @app_commands.choices(char=get_geo_choices())
    async def geo_char(self, interaction: Interaction, char: str,
                       member: Optional[Member] = None
                       ):
        member = member or interaction.user
        await interaction.response.defer()
        result = await genshin_app.getUserCharacters(char, member.id)
        result.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.followup.send(embed=result)

    @char.command(name='水', description='查看已擁有水元素角色資訊, 如命座、親密度、聖遺物')
    @app_commands.rename(char='角色', member='其他人')
    @app_commands.describe(char='僅能查看自己擁有角色的資料', member='查看其他群友的資料')
    @app_commands.choices(char=get_hydro_choices())
    async def hydro_char(self, interaction: Interaction, char: str,
                         member: Optional[Member] = None
                         ):
        member = member or interaction.user
        await interaction.response.defer()
        result = await genshin_app.getUserCharacters(char, member.id)
        result.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.followup.send(embed=result)

    @char.command(name='火', description='查看已擁有火元素角色資訊, 如命座、親密度、聖遺物')
    @app_commands.rename(char='角色', member='其他人')
    @app_commands.describe(char='僅能查看自己擁有角色的資料', member='查看其他群友的資料')
    @app_commands.choices(char=get_pyro_choices())
    async def pyro_char(self, interaction: Interaction, char: str,
                        member: Optional[Member] = None
                        ):
        member = member or interaction.user
        await interaction.response.defer()
        result = await genshin_app.getUserCharacters(char, member.id)
        result.set_author(name=self.bot.get_user(member.id),
                          icon_url=self.bot.get_user(member.id).avatar)
        await interaction.followup.send(embed=result)
#/rate
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
   #/wish 
    class PageChooser(discord.ui.Select):
        def __init__(self, page:int, result:list, author: discord.Member):
            options = self.get_page_choices(page)
            self.page = page 
            self.result = result
            super().__init__(placeholder='選擇頁數', min_values=1, max_values=1, options=options)

        def get_page_choices(self, page:int):
            result = []
            for i in range (1, page+1):
                result.append(discord.SelectOption(label=f'第 {i} 頁'))
            return result

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.author.id
        
        async def callback(self, interaction: discord.Interaction):
            choice = self.values[0]
            pos = [int(s) for s in re.findall(r'\b\d+\b', choice)]
            resultStr = ''
            for wish in self.result[pos[0]-1]:
                resultStr += f'{wish}\n'
            await interaction.response.edit_message(embed=defaultEmbed('詳細祈願紀錄', resultStr))

    class PageChooserView(discord.ui.View):
        def __init__(self, page:int, result:list, i: Interaction):
            super().__init__(timeout=None)
            self.add_item(GenshinCog.PageChooser(page, result, i.user))
    
    def divide_chunks(l, n):
        for i in range(0, len(l), n): 
            yield l[i:i + n]
    
    @app_commands.command(name='wish', description='祈願紀錄查詢')
    async def wish_history(self, i: Interaction):
        print(log(False, False, 'Wish', i.user.id))
        await i.response.defer()
        try:
            user_wish_histroy = openFile(f'wish_history/{i.user.id}')
        except Exception as e:
            await i.response.send_message(embed=errEmbed('你還沒有設置過抽卡紀錄!', '請使用`/setkey`指令'), ephemeral=True)
            return
        result = []
        for wish in user_wish_histroy:
            wish_time = f'{wish.time.year}-{wish.time.month}-{wish.time.day}'
            if wish.rarity == 5 or wish.rarity == 4:
                result.append(f"[{wish_time}: {wish.name} ({wish.rarity}☆ {wish.type})](http://example.com/)")
            else:
                result.append(f"{wish_time}: {wish.name} ({wish.rarity}☆ {wish.type})")
        split_list = list(GenshinCog.divide_chunks(result, 20))
        embed_list = []
        for l in split_list:
            embed_str = ''
            for w in l:
                embed_str+=f'{w}\n'
            embed_list.append(defaultEmbed('詳細祈願紀錄',embed_str))
        await WishPaginator(i, embed_list).start(embeded=True)
        

    class AuthKeyModal(ui.Modal, title='抽卡紀錄設定'):
        url = discord.ui.TextInput(
            label='Auth Key URL',
            placeholder='請ctrl+v貼上複製的連結',
            style=discord.TextStyle.long,
            required=True,
            min_length=0,
            max_length=3000
        )

        async def on_submit(self, interaction: discord.Interaction):
            client = genshin.Client()
            try:
                check, msg = genshin_app.checkUserData(interaction.user.id)
                if check == False:
                    await interaction.response.send_message(embed=errEmbed('設置失敗', '請先使用`/cookie`來設置自己的原神cookie'), ephemeral=True)
                    return
                url = self.url.value
                authkey = genshin.utility.extract_authkey(url)
                client = genshin_app.getUserCookie(interaction.user.id)
                client.authkey = authkey
                await interaction.response.send_message(embed=defaultEmbed('⏳ 請稍等, 處理數據中...', '過程約需30至45秒, 時長取決於祈願數量'), ephemeral=True)
                wish_data = await client.wish_history()
                file = open(
                    f'data/wish_history/{interaction.user.id}.yaml', 'w+')
                saveFile(wish_data, f'wish_history/{interaction.user.id}')
                await interaction.followup.send(embed=defaultEmbed('✅ 抽卡紀錄設置成功', ''), ephemeral=True)
            except Exception as e:
                await interaction.followup.send(embed=errEmbed('設置失敗', f'請將這個訊息私訊給小雪```{e}```'), ephemeral=True)

    class ChoosePlatform(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label='PC', style=discord.ButtonStyle.blurple)
        async def pc(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = defaultEmbed(
                'PC 設置方式',
                '1. 在電腦開啟原神(如果你使用多組帳號，請重新啟動遊戲)\n'
                '2. 打開祈願紀錄並等待讀取\n'
                '3. 在鍵盤點選"開始"鍵 (Windows鍵), 並搜尋 Powershell\n'
                '4. 點選 Windows Powershell, 接著複製及貼上下列程式碼到 Powershell\n'
                '5. 按Enter鍵, 接著連結會自動複製到剪貼簿\n'
                '6. 在這裡提交連結, 請輸入`/setkey`指令'
            )
            code_msg = "iex ((New-Object System.Net.WebClient).DownloadString('https://gist.githubusercontent.com/MadeBaruna/1d75c1d37d19eca71591ec8a31178235/raw/41853f2b76dcb845cf8cb0c44174fb63459920f4/getlink_global.ps1'))"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.followup.send(content=f'```{code_msg}```', ephemeral=True)

        @discord.ui.button(label='Android', style=discord.ButtonStyle.blurple)
        async def android(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = defaultEmbed(
                'Android 設置方式',
                '[影片教學](https://youtu.be/pe_aROJ8Av8)\n'
                '影片教學中複製了所有文本, 請只複製連結(步驟7)\n'
                '1. 打開祈願界面 (遊戲內)\n'
                '2. 點擊歷史記錄\n'
                '3. 等待載入\n'
                '4. 斷網(關閉wifi或行動數據)\n'
                '5. 點擊右上角刷新按鈕\n'
                '6. 此時頁面應該提示錯誤, 並顯示一些文字\n'
                '7. 長按並複製「只有連結」的部份(粗體字)\n'
                '8. 連網(接回wifi或行動數據)\n'
                '9. 在這裡提交連結, 請輸入`/setkey`指令'
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @discord.ui.button(label='IOS', style=discord.ButtonStyle.blurple)
        async def ios(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = defaultEmbed(
                'IOS 設置方式',
                '[影片教學](https://www.youtube.com/watch?v=WfBpraUq41c)\n'
                '1. 在App Store 下載 Stream [點我](https://apps.apple.com/app/stream/id1312141691)\n'
                '2. 開啟app, 接著在系統設定 (設定 > 一般 > VPN與裝置管理) 中同意 VPN\n'
                '3. 安裝 CA (在Stream App點選 開始抓包 > 將會出現彈跳視窗並選擇同意 > 安裝 CA > CA 就下載好了\n'
                '4. 前往 設定 > 一般 > VPN與裝置管理 > 點選 Stream Generated CA and install\n'
                '5. 開啟原神，接著打開祈願畫面，並在這個畫面等待\n'
                '6. 回到 Stream App > 選擇 信任 > 按 開始抓包 按鈕\n'
                '7. 回到原神，接著開啟祈願歷史紀錄\n'
                '8. 等候頁面載入\n'
                '9. 回到 Stream App > 停止抓包\n'
                '10. 按 抓包歷史 > 選擇一個以.json結尾的歷史紀錄(該連結前面會像是 https://hk4e-api-os.mihoyo.com/)\n'
                '11. 點選 "請求" 分頁, 接著複製連結\n'
                '12. 在這裡提交連結, 請輸入`/setkey`指令'
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @discord.ui.button(label='Play Station', style=discord.ButtonStyle.blurple)
        async def ps(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = defaultEmbed(
                'Play Station 設置流程',
                '如果你沒辦法使用以下的設置方法, 請將自己的PS帳號綁定至一個hoyoverse帳號, 並接著使用PC/手機設置方式\n'
                '1. 在你的 PlayStation 裡打開原神\n'
                '2. 打開你的信箱 QR Code\n'
                '3. 用手機掃描 QR Code 得到連結'
                '4. 在這裡提交連結, 請輸入`/setkey`指令'
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='setkey', description='設置原神祈願紀錄')
    @app_commands.rename(function='功能')
    @app_commands.describe(function='查看說明或提交連結')
    @app_commands.choices(function=
        [Choice(name='查看祈願紀錄的設置方式', value='help'),
        Choice(name='提交連結', value='submit')])
    async def set_key(self, i: Interaction, function: str):
        if function == 'help':
            view = GenshinCog.ChoosePlatform()
            embed = defaultEmbed(
                '選擇你目前的平台',
                '提醒: PC的設置方式是最簡便也最安全的\n'
                '其他管道只有在真的不得已的情況下再去做使用\n'
                '尤其IOS的設置方式極其複雜且可能失敗\n'
                '也可以將帳號交給有PC且自己信任的人來獲取數據')
            await i.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await i.response.send_modal(GenshinCog.AuthKeyModal())

    @app_commands.command(name='wishanalysis', description='原神祈願分析')
    @app_commands.choices(function=
        [Choice(name='歐氣值檢測', value=0),])
    @app_commands.rename(function='功能')
    async def wish_analysis(self, i: Interaction, function: int):
        print(log(False, False, 'Wish Analysis', i.user.id))
        await i.response.defer()
        try:
            user_wish_histroy = openFile(f'wish_history/{i.user.id}')
        except Exception as e:
            await i.response.send_message(embed=errEmbed('你還沒有設置過抽卡紀錄!', '請使用`/setkey`指令'), ephemeral=True)
            return
        std_characters = ['迪盧克','琴','七七','莫娜','刻晴']
        up_num = 0
        up_gu = 0
        num_until_up = 0
        found = False
        found_last_five_star = False
        if function == 0:
            for wish in user_wish_histroy:
                if wish.banner_type==301:
                    if wish.rarity == 5 and wish.type == '角色':
                        if wish.name not in std_characters:
                            up_num+=1
                        if not found_last_five_star:
                            found_last_five_star = True
                            if wish.name not in std_characters:
                                up_gu = 0
                            else:
                                up_gu = 1
                        found = True
                    else:
                        if not found:
                            num_until_up+=1
            player = GGanalysislib.Up5starCharacter()
            gu_state = '有大保底' if up_gu == 1 else '沒有大保底'
            embed = defaultEmbed(
                '歐氣值檢測',
                f'• 你的運氣擊敗了{str(round(100*player.luck_evaluate(get_num=up_num, use_pull=len(user_wish_histroy), left_pull=num_until_up, up_guarantee=up_gu), 2))}%的玩家\n'
                f'• 共{len(user_wish_histroy)}抽\n'
                f'• 出了{up_num}個UP\n'
                f'• 墊了{num_until_up}抽\n'
                f'• {gu_state}')
            embed.set_author(name=i.user, icon_url=i.user.avatar)
            await i.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GenshinCog(bot))
