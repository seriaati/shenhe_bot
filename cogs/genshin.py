import ast
import json
import urllib.parse
from datetime import datetime
from typing import Any, List, Optional

import aiosqlite
import discord
import utility.global_vars as shenhe_emoji
import yaml
from data.game.characters_map import characters_map
from data.game.namecards_map import namecards_map
from data.game.talents import talents
from debug import DefaultView
from discord import (ButtonStyle, Embed, Emoji, Guild, Interaction, Member,
                     SelectOption, app_commands)
from discord.app_commands import Choice
from discord.ext import commands
from discord.ui import Button, Modal, Select, TextInput, button, select
from utility.apps.GenshinApp import GenshinApp
from utility.paginators.AbyssPaginator import AbyssPaginator
from utility.paginators.GeneralPaginator import GeneralPaginator
from utility.utils import (calculateArtifactScore, calculateDamage,
                           defaultEmbed, errEmbed, get_name, getCharacterIcon,
                           getCharaEmojiWithId, getCharaIdWithName, getClient,
                           getElementEmoji, getStatEmoji, getWeekdayName)

from genshin.models import WikiPageType


class GenshinCog(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.genshin_app = GenshinApp(self.bot.db)
        self.debug_toggle = self.bot.debug_toggle

# cookie

    class CookieModal(discord.ui.Modal):
        def __init__(self, db: aiosqlite.Connection):
            self.genshin_app = GenshinApp(db)
            super().__init__(title='提交cookie', timeout=None, custom_id='cookie_modal')

        cookie = discord.ui.TextInput(
            label='Cookie',
            placeholder='請貼上從網頁上取得的Cookie, 取得方式請使用指令 /cookie',
            style=discord.TextStyle.long,
            required=True
        )

        async def on_submit(self, i: Interaction):
            result = await self.genshin_app.setCookie(i.user.id, self.cookie.value)
            await i.response.send_message(embed=result, ephemeral=True)

        async def on_error(self, error: Exception, i: Interaction):
            embed = errEmbed(
                '<a:error_animated:982579472060547092> 錯誤', f'```{error}```')
            await i.response.send_message(embed=embed, ephemeral=True)
# Cookie Submission

    @app_commands.command(
        name='cookie設定',
        description='設定Cookie')
    @app_commands.rename(option='選項')
    @app_commands.choices(option=[
        Choice(name='1. 顯示說明如何取得Cookie', value=0),
        Choice(name='2. 提交已取得的Cookie', value=1)])
    async def slash_cookie(self, i: Interaction, option: int):
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
            await i.response.send_message(embed=embed)
            await i.followup.send(content=code_msg)
        elif option == 1:
            await i.response.send_modal(GenshinCog.CookieModal(self.bot.db))

    @app_commands.command(
        name='check即時便籤',
        description='查看即時便籤, 例如樹脂、洞天寶錢、探索派遣'
    )
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def check(self, i: Interaction, member: Optional[Member] = None):
        member = member or i.user
        result = await self.genshin_app.getRealTimeNotes(member.id, False)
        result.set_author(name='即時便籤', icon_url=member.avatar)
        await i.response.send_message(embed=result)
# /stats

    @app_commands.command(name='stats數據', description='查看原神資料, 如活躍時間、神瞳數量、寶箱數量')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def stats(self, i: Interaction, member: Optional[Member] = None):
        member = member or i.user
        result = await self.genshin_app.getUserStats(member.id)
        result.set_author(name='原神數據', icon_url=member.avatar)
        await i.response.send_message(embed=result)
# /area

    @app_commands.command(name='area探索度', description='查看區域探索度')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def area(self, i: Interaction, member: Optional[Member] = None):
        member = member or i.user
        result = await self.genshin_app.getArea(member.id)
        result.set_author(name='區域探索度', icon_url=member.avatar)
        await i.response.send_message(embed=result)
# /claim

    @app_commands.command(name='claim登入獎勵', description='領取hoyolab登入獎勵')
    @app_commands.rename(all='全部人', member='其他人')
    @app_commands.describe(all='是否要幫全部已註冊的使用者領取獎勵', member='查看其他群友的資料')
    @app_commands.choices(all=[
        Choice(name='是', value=1),
        Choice(name='否', value=0)])
    async def claim(self, i: Interaction, all: Optional[int] = 0, member: Optional[Member] = None):
        if all == 1:
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute('SELECT user_id FROM genshin_accounts WHERE ltuid IS NOT NULL')
            users = await c.fetchall()
            count = 0
            for index, tuple in enumerate(users):
                user_id = tuple[0]
                await self.genshin_app.claimDailyReward(user_id)
                count += 1
            await i.response.send_message(embed=defaultEmbed(f'<a:check_animated:982579879239352370> 全員簽到完成 ({count})'))
        else:
            member = member or i.user
            result = await self.genshin_app.claimDailyReward(member.id)
            result.set_author(name=member, icon_url=member.avatar)
            await i.response.send_message(embed=result)
# /diary

    @app_commands.command(name='diary旅行者日記', description='查看旅行者日記')
    @app_commands.rename(month='月份', member='其他人')
    @app_commands.describe(month='要查詢的月份', member='查看其他群友的資料')
    @app_commands.choices(month=[
        app_commands.Choice(name='這個月', value=0),
        app_commands.Choice(name='上個月', value=-1),
        app_commands.Choice(name='上上個月', value=-2)])
    async def diary(self, i: Interaction, month: int, member: Optional[Member] = None):
        member = member or i.user
        month = datetime.now().month + month
        month = month + 12 if month < 1 else month
        result = await self.genshin_app.getDiary(member.id, month)
        result.set_author(name='旅行者日記', icon_url=member.avatar)
        await i.response.send_message(embed=result)
# /log

    @app_commands.command(name='log收入紀錄', description='查看最近25筆原石或摩拉收入紀錄')
    @app_commands.choices(data_type=[
        app_commands.Choice(name='原石', value=0),
        app_commands.Choice(name='摩拉', value=1)])
    @app_commands.rename(data_type='類別', member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def log(self, i: Interaction, data_type: int, member: Optional[Member] = None):
        member = member or i.user
        result = await self.genshin_app.getDiaryLog(member.id)
        if type(result) is Embed:
            await i.response.send_message(embed=result, ephemeral=True)
            return
        result = result[data_type]
        if data_type == 0:
            result.set_author(
                name='<:primo:958555698596290570> 最近25筆原石紀錄', icon_url=member.avatar)
        elif data_type == 1:
            result.set_author(
                name='<:mora:958577933650362468> 最近25筆摩拉紀錄', icon_url=member.avatar)
        await i.response.send_message(embed=result)

# /abyss

    @app_commands.command(name='abyss深淵', description='深淵資料查詢')
    @app_commands.rename(overview='類別', previous='期別', member='其他人')
    @app_commands.describe(overview='想要查看的資料類別',
                           previous='這期還是上期?', member='查看其他群友的資料')
    @app_commands.choices(
        overview=[Choice(name='詳細', value=0),
                  Choice(name='總覽', value=1)],
        previous=[Choice(name='本期紀錄', value=0),
                  Choice(name='上期紀錄', value=1)]
    )
    async def abyss(self, i: Interaction, overview: int = 1, previous: int = 0, member: Member = None):
        member = member or i.user
        previous = True if previous == 1 else False
        overview = True if overview == 1 else False
        result= await self.genshin_app.getAbyss(member.id, previous, overview)
        if type(result) is not list:
            result.set_author(name='找不到深淵資料', icon_url=i.user.avatar)
            return await i.response.send_message(embed=result)
        if overview:
            result = result[0]
            result.set_author(name='深淵總覽', icon_url=i.user.avatar)
            await i.response.send_message(embed=result)
        else:
            for r in result:
                r.set_author(name='深淵詳細', icon_url=i.user.avatar)
            await AbyssPaginator(i, result).start(embeded=True)

# /stuck

    @app_commands.command(name='stuck', description='找不到資料?')
    async def stuck(self, i: Interaction):
        embed = defaultEmbed(
            '註冊了, 但是找不到資料?',
            '請至<https://www.hoyolab.com>登入你的hoyoverse帳號\n'
            '跟著下方圖片中的步驟操作\n\n'
            '文字教學:\n'
            '1. 點選右上角自己的頭像\n'
            '2. 個人主頁\n'
            '3. 右上角「原神」\n'
            '4. 設定齒輪\n'
            '5. 三個選項都打開')
        embed.set_image(url='https://i.imgur.com/w6Q7WwJ.gif')
        await i.response.send_message(embed=embed, ephemeral=True)

    class ResinNotifModal(Modal, title='樹脂提醒設定'):
        resin_threshold = TextInput(
            label='樹脂閥值', placeholder='例如: 140 (不得大於 160)')
        max_notif = TextInput(label='最大提醒值', placeholder='例如: 5')

        async def on_submit(self, interaction: Interaction) -> None:
            await interaction.response.defer()
            self.stop()

    class TalentElementChooser(DefaultView):
        def __init__(self, author: Member, db: aiosqlite.Connection):
            super().__init__(timeout=None)
            self.author = author
            elements = ['Anemo', 'Cryo', 'Electro', 'Pyro', 'Hydro', 'Geo']
            for index in range(0, 6):
                self.add_item(GenshinCog.TalentElementButton(
                    elements[index], index//3, db))

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(emebd=errEmbed(f'{shenhe_emoji.error} 這不是你的操作視窗', '輸入 `/remind` 來設置自己的提醒功能'), ephemeral=True)
            return self.author.id == interaction.user.id

    class TalentElementButton(Button):
        def __init__(self, element: str, row: int, db: aiosqlite.Connection):
            super().__init__(emoji=getElementEmoji(element), row=row)
            self.element = element
            self.db = db

        async def callback(self, interaction: Interaction) -> Any:
            embed = defaultEmbed(message='選擇已經設置過的角色將移除該角色的提醒')
            embed.set_author(name='選擇角色', icon_url=interaction.user.avatar)
            c = await self.db.cursor()
            await c.execute('SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?', (interaction.user.id,))
            user_chara_list: list = (await c.fetchone())[0]
            if user_chara_list == '':
                talent_notif_chara_list = []
            else:
                talent_notif_chara_list: list = ast.literal_eval(user_chara_list)
            await interaction.response.edit_message(embed=embed, view=GenshinCog.TalentCharaChooserView(self.element, self.view.author, self.db, talent_notif_chara_list))

    class TalentCharaChooserView(DefaultView):
        def __init__(self, element: str, author: Member, db: aiosqlite.Connection, talent_notif_chara_list: list):
            super().__init__(timeout=None)
            self.add_item(GenshinCog.TalentCharaChooser(element, db, talent_notif_chara_list, author))
            self.author = author
            self.db = db

        @button(emoji='<:left:982588994778972171>', style=ButtonStyle.gray, row=2)
        async def go_back(self, i: Interaction, button: Button):
            embed = defaultEmbed('')
            embed.set_author(name='選擇想要設置提醒功能的角色元素', icon_url=i.user.avatar)
            await i.response.edit_message(embed=embed, view=GenshinCog.TalentElementChooser(i.user, self.db))

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(emebd=errEmbed(f'{shenhe_emoji.error} 這不是你的操作視窗', '輸入 `/remind` 來設置自己的提醒功能'), ephemeral=True)
            return self.author.id == interaction.user.id

    class TalentCharaChooser(Select):
        def __init__(self, element: str, db: aiosqlite.Connection, talent_notif_chara_list: list, author: Member):
            options = []
            self.db = db
            self.author = author 
            self.element = element
            for week_day, books in talents.items():
                for book_name, characters in books.items():
                    for character_name, element_name in characters.items():
                        if element == element_name:
                            desc = f'{week_day} - 「{book_name}」'
                            if character_name in talent_notif_chara_list:
                                desc = '已設置過此角色, 再次選擇將會移除'
                            options.append(SelectOption(
                                label=character_name, description=desc, emoji=getCharaEmojiWithId(getCharaIdWithName(character_name))))
            super().__init__(options=options, placeholder='選擇角色', max_values=len(options))

        async def callback(self, interaction: Interaction) -> Any:
            c = await self.db.cursor()
            await c.execute('SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?', (interaction.user.id,))
            chara_list = (await c.fetchone())[0]
            if chara_list == '':
                chara_list = self.values
            else:
                chara_list: list = ast.literal_eval(chara_list)
                for chara in self.values:
                    if chara in chara_list:
                        chara_list.remove(chara)
                    else:
                        chara_list.append(chara)
            await c.execute('UPDATE genshin_accounts SET talent_notif_toggle = 1, talent_notif_chara_list = ? WHERE user_id = ?', (str(chara_list), interaction.user.id))
            await self.db.commit()
            embed = defaultEmbed(message='還想要設置其他元素的角色嗎? 視窗還在上面!')
            embed.set_author(name='天賦提醒設置成功', icon_url=interaction.user.avatar)
            await c.execute('SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?', (interaction.user.id,))
            chara_list = ast.literal_eval((await c.fetchone())[0])
            chara_str = ''
            for chara in chara_list:
                chara_str += f'• {chara}\n'
            chara_str = '(空)' if chara_str == '' else chara_str
            embed.add_field(name='目前已設置角色', value=chara_str)
            prev_embed = defaultEmbed(message='選擇已經設置過的角色將移除該角色的提醒')
            prev_embed.set_author(name='選擇角色', icon_url=interaction.user.avatar)
            c = await self.db.cursor()
            await c.execute('SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?', (interaction.user.id,))
            user_chara_list: list = (await c.fetchone())[0]
            if user_chara_list == '':
                talent_notif_chara_list = []
            else:
                talent_notif_chara_list: list = ast.literal_eval(user_chara_list)
            await interaction.response.edit_message(embed=prev_embed, view=GenshinCog.TalentCharaChooserView(self.element, self.author, self.db, talent_notif_chara_list))
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name='remind提醒', description='設置提醒功能')
    @app_commands.rename(function='功能', toggle='開關')
    @app_commands.describe(function='提醒功能', toggle='要開啟或關閉該提醒功能')
    @app_commands.choices(function=[Choice(name='樹脂提醒', value=0), Choice(name='天賦素材提醒', value=1)],
                          toggle=[Choice(name='開', value=1), Choice(name='關', value=0)])
    async def resin_remind(self, i: Interaction, function: int, toggle: int):
        if function == 0:
            if toggle == 0:
                result = await self.genshin_app.setResinNotification(i.user.id, 0, None, None)
                result.set_author(name='樹脂提醒功能已關閉', icon_url=i.user.avatar)
                await i.response.send_message(embed=result)
            else:
                modal = GenshinCog.ResinNotifModal()
                await i.response.send_modal(modal)
                await modal.wait()
                result = await self.genshin_app.setResinNotification(i.user.id, toggle, modal.resin_threshold.value, modal.max_notif.value)
                result.set_author(name='樹脂提醒設定成功', icon_url=i.user.avatar)
                await i.followup.send(embed=result)
        elif function == 1:
            if toggle == 0:
                c: aiosqlite.Cursor = await self.bot.db.cursor()
                await c.execute('UPDATE genshin_accounts SET talent_notif_toggle = 0 WHERE user_id = ?', (i.user.id,))
                await self.bot.db.commit()
                embed = defaultEmbed()
                embed.set_author(name='天賦提醒功能已關閉', icon_url=i.user.avatar)
                await i.response.send_message(embed=embed)
            else:
                embed = defaultEmbed()
                embed.set_author(name='選擇想要設置提醒功能的角色元素', icon_url=i.user.avatar)
                view = GenshinCog.TalentElementChooser(i.user, self.bot.db)
                await i.response.send_message(embed=embed, view=view)

# /farm

    def get_farm_image(day: int):
        if day == 0 or day == 3:
            url = "https://i.imgur.com/Jr5tlUs.png"
        elif day == 1 or day == 4:
            url = "https://media.discordapp.net/attachments/823440627127287839/958862746127060992/5ac261bdfc846f45.png"
        elif day == 2 or day == 5:
            url = "https://media.discordapp.net/attachments/823440627127287839/958862745871220796/0b16376c23bfa1ab.png"
        else:
            url = "https://i.imgur.com/MPI5uwW.png"
        return url

    class ChooseDay(DefaultView):
        def __init__(self):
            super().__init__(timeout=None)
            for i in range(0, 4):
                self.add_item(GenshinCog.DayButton(i))

    class DayButton(Button):
        def __init__(self, day: int):
            self.day = day
            if day == 0:
                label = '週一、週四'
            elif day == 1:
                label = '週二、週五'
            elif day == 2:
                label = '週三、週六'
            else:
                label = '週日'
                self.day = 6
            super().__init__(label=label, style=ButtonStyle.blurple)

        async def callback(self, i: Interaction) -> Any:
            day_str = f'{getWeekdayName(self.day)}、{getWeekdayName(self.day+3)}' if self.day != 6 else '週日'
            embed = defaultEmbed(f"{day_str}可以刷的副本材料")
            embed.set_image(url=GenshinCog.get_farm_image(self.day))
            await i.response.edit_message(embed=embed)

    @app_commands.command(name='farm刷素材', description='查看原神今日可刷素材')
    async def farm(self, interaction: Interaction):
        day = datetime.today().weekday()
        embed = defaultEmbed(
            f"今日 ({getWeekdayName(day)}) 可以刷的副本材料")
        embed.set_image(url=GenshinCog.get_farm_image(day))
        view = GenshinCog.ChooseDay()
        await interaction.response.send_message(embed=embed, view=view)

    class ElementChooseView(DefaultView):  # 選擇元素按鈕的view
        def __init__(self, db: aiosqlite.Connection, emojis: List):
            super().__init__(timeout=None)
            for i in range(0, 6):
                self.add_item(GenshinCog.ElementButton(
                    i, db, emojis[i]))

    class ElementButton(Button):  # 元素按鈕
        def __init__(self, index: int, db: aiosqlite.Connection, emoji: Emoji):
            self.index = index
            self.db = db
            super().__init__(style=ButtonStyle.gray, row=index % 2, emoji=emoji)

        async def callback(self, i: Interaction):
            view = GenshinCog.CharactersDropdownView(
                self.index, self.db)
            embed = defaultEmbed('請選擇角色')
            await i.response.edit_message(embed=embed, view=view)

    class CharactersDropdownView(DefaultView):  # 角色配置下拉選單的view
        def __init__(self, index: int, db: aiosqlite.Connection):
            super().__init__(timeout=None)
            self.db = db
            self.add_item(GenshinCog.BuildCharactersDropdown(index, db))

        @button(emoji='<:left:982588994778972171>', style=ButtonStyle.gray, row=1)
        async def back(self, i: Interaction, button: Button):
            emojis = []
            ids = [982138235239137290, 982138229140635648, 982138220248711178,
                   982138232391237632, 982138233813098556, 982138221569900585]
            for id in ids:
                emojis.append(i.client.get_emoji(id))
            view = GenshinCog.ElementChooseView(self.db, emojis)
            embed = defaultEmbed()
            embed.set_author(name='選擇想查看角色的元素', icon_url=i.user.avatar)
            await i.response.edit_message(embed=embed, view=view)

    class BuildCharactersDropdown(Select):  # 角色配置下拉選單(依元素分類)
        def __init__(self, index: int, db: aiosqlite.Connection):
            self.genshin_app = GenshinApp(db)
            self.index = index
            self.db = db
            elemenet_chinese = ['風', '冰', '雷', '岩', '水', '火']
            elements = ['anemo', 'cryo', 'electro', 'geo', 'hydro', 'pyro']
            with open(f'data/builds/{elements[index]}.yaml', 'r', encoding='utf-8') as f:
                self.build_dict = yaml.full_load(f)
            options = []
            for character, value in self.build_dict.items():
                options.append(SelectOption(label=character, value=character,
                               emoji=getCharaEmojiWithId(getCharaIdWithName(character))))
            super().__init__(
                placeholder=f'{elemenet_chinese[index]}元素角色', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: Interaction):
            result = await self.genshin_app.getBuild(self.build_dict, str(self.values[0]))
            view = GenshinCog.BuildSelectView(
                len(result), result, self.index, self.db)
            await interaction.response.edit_message(embed=result[0][0], view=view)

    class BuildSelectView(DefaultView):
        def __init__(self, total: int, build_embeds: List, index: int, db: aiosqlite.Connection):
            super().__init__(timeout=None)
            self.index = index
            self.db = db
            self.add_item(GenshinCog.BuildSelect(total, build_embeds))

        @button(emoji='<:left:982588994778972171>', style=ButtonStyle.gray, row=1)
        async def back(self, i: Interaction, button: Button):
            view = GenshinCog.CharactersDropdownView(
                self.index, self.db)
            embed = defaultEmbed('請選擇角色')
            await i.response.edit_message(embed=embed, view=view)

    class BuildSelect(Select):
        def __init__(self, total: int, build_embeds: List):
            options = []
            self.embeds = build_embeds
            for i in range(1, total+1):
                options.append(SelectOption(
                    label=f'配置{i} - {build_embeds[i-1][1]} - {build_embeds[i-1][2]}', value=i))
            super().__init__(
                placeholder=f'選擇配置', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: Interaction) -> Any:
            await interaction.response.edit_message(embed=self.embeds[int(self.values[0])-1][0])

    # /build
    @app_commands.command(name='build角色配置', description='查看角色推薦主詞條、畢業面板、不同配置等')
    async def build(self, i: Interaction):
        emojis = []
        ids = [982138235239137290, 982138229140635648, 982138220248711178,
               982138232391237632, 982138233813098556, 982138221569900585]
        for id in ids:
            emojis.append(self.bot.get_emoji(id))
        view = GenshinCog.ElementChooseView(self.bot.db, emojis)
        await i.response.send_message(embed=defaultEmbed('請選擇想查看角色的元素'), view=view)

    @app_commands.command(name='uid查詢', description='查詢特定使用者的原神UID')
    @app_commands.rename(player='使用者')
    @app_commands.describe(player='選擇想要查詢的使用者')
    async def search_uid(self, i: Interaction, player: Member):
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (player.id,))
        uid = await c.fetchone()
        if uid is None:
            await i.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 查無此用戶!', '這個使用者還沒有註冊過UID\n請至 <#978871680019628032> 註冊 UID'), ephemeral=True)
            return
        uid = uid[0]
        embed = defaultEmbed()
        embed.set_author(name=uid, icon_url=player.avatar)
        await i.response.send_message(embed=embed)

    class CalcultorElementButtonView(DefaultView):
        def __init__(self, author: Member, chara_list: List, item_type: str):
            super().__init__(timeout=None)
            self.author = author
            for i in range(0, 6):
                self.add_item(GenshinCog.CalcultorElementButton(
                    i, chara_list, item_type))

        async def interaction_check(self, i: Interaction) -> bool:
            return i.user.id == self.author.id

    class CalcultorElementButton(Button):
        def __init__(self, index: int, chara_list: List, item_type: str):
            self.element_name_list = ['Anemo', 'Cryo',
                                      'Electro', 'Geo', 'Hydro', 'Pyro']
            element_emojis = ['<:WIND_ADD_HURT:982138235239137290>', '<:ICE_ADD_HURT:982138229140635648>', '<:ELEC_ADD_HURT:982138220248711178>',
                              '<:ROCK_ADD_HURT:982138232391237632>', '<:WATER_ADD_HURT:982138233813098556>', '<:FIRE_ADD_HURT:982138221569900585>']
            self.index = index
            self.chara_list = chara_list
            self.item_type = item_type
            super().__init__(
                emoji=element_emojis[index], style=ButtonStyle.gray, row=index % 2)

        async def callback(self, i: Interaction):
            element_chara_list = []
            for chara in self.chara_list:
                if chara[2] == self.element_name_list[self.index]:
                    element_chara_list.append(chara)
            self.view.element_chara_list = element_chara_list
            self.view.item_type = self.item_type
            await i.response.defer()
            self.view.stop()

    class CalculatorItems(DefaultView):
        def __init__(self, author: Member, item_list: List, item_type: str):
            super().__init__(timeout=None)
            self.author = author
            self.add_item(GenshinCog.CalculatorItemSelect(
                item_list, item_type))

        async def interaction_check(self, i: Interaction) -> bool:
            return self.author.id == i.user.id

    class CalculatorItemSelect(Select):
        def __init__(self, items, item_type):
            options = []
            for item in items:
                options.append(SelectOption(
                    label=item[0], value=item[1], emoji=getCharaEmojiWithId(getCharaIdWithName(item[0]))))
            super().__init__(placeholder=f'選擇{item_type}',
                             min_values=1, max_values=1, options=options)

        async def callback(self, i: Interaction):
            modal = GenshinCog.LevelModal()
            await i.response.send_modal(modal)
            await modal.wait()
            self.view.target = int(modal.chara.value)
            self.view.a = int(modal.attack.value)
            self.view.e = int(modal.skill.value)
            self.view.q = int(modal.burst.value)
            self.view.value = self.values[0]
            self.view.stop()

    class LevelModal(Modal):
        chara = TextInput(
            label='角色目標等級',
            placeholder='例如: 90',
        )

        attack = TextInput(
            label='普攻目標等級',
            placeholder='例如: 10',
        )

        skill = TextInput(
            label='元素戰技(E)目標等級',
            placeholder='例如: 8',
        )

        burst = TextInput(
            label='元素爆發(Q)目標等級',
            placeholder='例如: 9',
        )

        def __init__(self) -> None:
            super().__init__(title='計算資料輸入', timeout=None)

        async def on_submit(self, interaction: Interaction) -> None:
            await interaction.response.defer()

    def check_level_validity(self, target: int, a: int, e: int, q: int):
        if target > 90:
            return False, errEmbed('原神目前的最大等級是90唷')
        if a > 10 or e > 10 or q > 10:
            return False, errEmbed('天賦的最高等級是10唷', '有命座請自行減3')
        if target <= 0:
            return False, errEmbed('原神角色最少至少要1等唷')
        if a <= 0 or e <= 0 or q <= 0:
            return False, errEmbed('天賦至少要1等唷')
        else:
            return True, None

    class AddMaterialsView(DefaultView):
        def __init__(self, db: aiosqlite.Connection, disabled: bool, author: Member, materials):
            super().__init__(timeout=None)
            self.add_item(GenshinCog.AddTodoButton(disabled, db, materials))
            self.author = author

        async def interaction_check(self, interaction: Interaction) -> bool:
            if interaction.user.id != self.author.id:
                await interaction.response.send_message(embed=errEmbed('這不是你的計算視窗', '輸入 `/calc` 來計算'), ephemeral=True)
            return interaction.user.id == self.author.id

    class AddTodoButton(Button):
        def __init__(self, disabled: bool, db: aiosqlite.Connection, materials):
            super().__init__(style=ButtonStyle.blurple, label='新增到代辦清單', disabled=disabled)
            self.db = db
            self.materials = materials

        async def callback(self, i: Interaction) -> Any:
            c = await self.db.cursor()
            for item_data in self.materials:
                await c.execute('SELECT count FROM todo WHERE user_id = ? AND item = ?', (i.user.id, item_data[0]))
                count = await c.fetchone()
                if count is None:
                    await c.execute('INSERT INTO todo (user_id, item, count) VALUES (?, ?, ?)', (i.user.id, item_data[0], item_data[1]))
                else:
                    count = count[0]
                    await c.execute('UPDATE todo SET count = ? WHERE user_id = ? AND item = ?', (count+int(item_data[1]), i.user.id, item_data[0]))
            await self.db.commit()
            await i.response.send_message(embed=defaultEmbed('<a:check_animated:982579879239352370> 代辦事項新增成功', '使用`/todo`指令來查看你的代辦事項'), ephemeral=True)

    calc = app_commands.Group(name="calc", description="原神養成計算機")

    @calc.command(name='notown所有角色', description='計算一個自己不擁有的角色所需的素材')
    async def calc_notown(self, i: Interaction):
        client, uid, only_uid = await self.genshin_app.getUserCookie(i.user.id)
        charas = await client.get_calculator_characters()
        chara_list = []
        for chara in charas:
            chara_list.append([chara.name, chara.id, chara.element])
        button_view = GenshinCog.CalcultorElementButtonView(
            i.user, chara_list, '角色')
        embed = defaultEmbed()
        embed.set_author(name='選擇角色的元素', icon_url=i.user.avatar)
        await i.response.send_message(embed=embed, view=button_view)
        await button_view.wait()
        select_view = GenshinCog.CalculatorItems(
            i.user, button_view.element_chara_list, button_view.item_type)
        await i.edit_original_message(view=select_view)
        await select_view.wait()
        valid, error_msg = self.check_level_validity(
            select_view.target, select_view.a, select_view.e, select_view.q)
        if not valid:
            await i.followup.send(embed=error_msg, ephemeral=True)
            return
        chara_name = ''
        for chara in chara_list:
            if int(select_view.value) == int(chara[1]):
                chara_name = chara[0]
        character = await client.get_calculator_characters(query=chara_name)
        character = character[0]
        embed = defaultEmbed()
        embed.set_author(name='計算結果', icon_url=i.user.avatar)
        embed.set_thumbnail(url=character.icon)
        embed.add_field(
            name='計算內容',
            value=f'角色等級 1 ▸ {select_view.target}\n'
            f'普攻等級 1 ▸ {select_view.a}\n'
            f'元素戰技(E)等級 1 ▸ {select_view.e}\n'
            f'元素爆發(Q)等級 1 ▸ {select_view.q}',
            inline=False
        )
        talents = await client.get_character_talents(select_view.value)
        builder = client.calculator()
        builder.set_character(select_view.value, current=1,
                              target=select_view.target)
        builder.add_talent(talents[0].group_id,
                           current=1, target=select_view.a)
        builder.add_talent(talents[1].group_id,
                           current=1, target=select_view.e)
        builder.add_talent(talents[2].group_id,
                           current=1, target=select_view.q)
        cost = await builder.calculate()
        materials = []
        for index, tuple in enumerate(cost):
            if tuple[0] == 'character':
                value = ''
                for item in tuple[1]:
                    value += f'{item.name}  x{item.amount}\n'
                    materials.append([item.name, item.amount])
                if value == '':
                    value = '不需要任何素材'
                embed.add_field(name='角色所需素材', value=value, inline=False)
            if tuple[0] == 'talents':
                value = ''
                for item in tuple[1]:
                    value += f'{item.name}  x{item.amount}\n'
                    materials.append([item.name, item.amount])
                if value == '':
                    value = '不需要任何素材'
                embed.add_field(name='天賦所需素材', value=value, inline=False)
        if len(materials) == 0:
            view = GenshinCog.AddMaterialsView(
                self.bot.db, True, i.user, materials)
        else:
            view = GenshinCog.AddMaterialsView(
                self.bot.db, False, i.user, materials)
        await i.edit_original_message(embed=embed, view=view)

    @calc.command(name='character自己有的角色', description='個別計算一個角色所需的素材')
    async def calc_character(self, i: Interaction):
        client, uid, only_uid = await self.genshin_app.getUserCookie(i.user.id)
        if only_uid:
            embed = errEmbed('你不能使用這項功能!', '請使用`/cookie`的方式註冊後再來試試看')
            await i.response.send_message(embed=embed, ephemeral=True)
            return
        try:
            charas = await client.get_calculator_characters(sync=True)
        except:
            embed = defaultEmbed(
                '等等!',
                '你需要先進行下列的操作才能使用此功能\n'
                '由於米哈遊非常想要大家使用他們的 hoyolab APP\n'
                '所以以下操作只能在手機上用 APP 進行 <:penguin_dead:978841159147343962>\n'
                'APP 下載連結: [IOS](https://apps.apple.com/us/app/hoyolab/id1559483982) [Android](https://play.google.com/store/apps/details?id=com.mihoyo.hoyolab&hl=en&gl=US)')
            embed.set_image(url='https://i.imgur.com/GiYbVwU.gif')
            await i.response.send_message(embed=embed, ephemeral=True)
            return
        chara_list = []
        for chara in charas:
            chara_list.append([chara.name, chara.id, chara.element])
        button_view = GenshinCog.CalcultorElementButtonView(
            i.user, chara_list, '角色')
        embed = defaultEmbed('選擇角色的元素')
        await i.response.send_message(embed=embed, view=button_view)
        await button_view.wait()
        select_view = GenshinCog.CalculatorItems(
            i.user, button_view.element_chara_list, button_view.item_type)
        await i.edit_original_message(view=select_view)
        await select_view.wait()
        valid, error_msg = self.check_level_validity(
            select_view.target, select_view.a, select_view.e, select_view.q)
        if not valid:
            await i.followup.send(embed=error_msg, ephemeral=True)
            return
        chara_name = ''
        for chara in chara_list:
            if int(select_view.value) == int(chara[1]):
                chara_name = chara[0]
        details = await client.get_character_details(select_view.value)
        character = await client.get_calculator_characters(query=chara_name, sync=True)
        character = character[0]
        embed = defaultEmbed('計算結果')
        embed.set_thumbnail(url=character.icon)
        value = ''
        for index, tuple in enumerate(details):
            if tuple[0] == 'talents':
                value += f'角色等級 {character.level} ▸ {select_view.target}\n'
                value += f'普攻等級 {tuple[1][0].level} ▸ {select_view.a}\n'
                value += f'元素戰技(E)等級 {tuple[1][1].level} ▸ {select_view.e}\n'
                value += f'元素爆發(Q)等級 {tuple[1][2].level} ▸ {select_view.q}\n'
                break
        embed.add_field(name='計算內容', value=value, inline=False)
        cost = await (
            client.calculator()
            .set_character(select_view.value, current=character.level, target=select_view.target)
            .with_current_talents(attack=select_view.a, skill=select_view.e, burst=select_view.q)
        )
        materials = []
        for index, tuple in enumerate(cost):
            if tuple[0] == 'character':
                value = ''
                for item in tuple[1]:
                    value += f'{item.name}  x{item.amount}\n'
                    materials.append([item.name, item.amount])
                if value == '':
                    value = '不需要任何素材'
                embed.add_field(name='角色所需素材', value=value, inline=False)
            if tuple[0] == 'talents':
                value = ''
                for item in tuple[1]:
                    value += f'{item.name}  x{item.amount}\n'
                    materials.append([item.name, item.amount])
                if value == '':
                    value = '不需要任何素材'
                embed.add_field(name='天賦所需素材', value=value, inline=False)
        if len(materials) == 0:
            view = GenshinCog.AddMaterialsView(
                self.bot.db, True, i.user, materials)
        else:
            view = GenshinCog.AddMaterialsView(
                self.bot.db, False, i.user, materials)
        await i.edit_original_message(embed=embed, view=view)

    def oculi_emebd_style(element: str, url: str):
        embed = defaultEmbed(f'{element}神瞳位置')
        embed.set_image(url=url)
        embed.set_footer(text='單純功能搬運, 圖源並非來自我')
        return embed

    def get_oculi_embeds(area: int):
        embeds = []
        if area == 0:
            for i in range(1, 5):
                url = f'https://fortoffans.github.io/Maps/Oculus/Anemoculus/Map_Anemoculus_{i}.jpg?width=831&height=554'
                embeds.append(GenshinCog.oculi_emebd_style('風', url))
        elif area == 1:
            for i in range(1, 6):
                url = f'https://images-ext-1.discordapp.net/external/Gm5I4dqqanZEksPk7pggWfwoqW5UOiKPJP8Rt-uYQ5E/https/fortoffans.github.io/Maps/Oculus/Geoculus/Map_Geoculus_{i}.jpg?width=831&height=554'
                embeds.append(GenshinCog.oculi_emebd_style('岩', url))
        elif area == 2:
            for i in range(1, 7):
                url = f'https://images-ext-1.discordapp.net/external/u6qgVi5Fk28_wwEuu3OS9blTzC-7JQpridJiWv0vI5s/https/fortoffans.github.io/Maps/Oculus/Electroculus/Map_Electroculus_{i}.jpg?width=831&height=554'
                embeds.append(GenshinCog.oculi_emebd_style('雷', url))
        return embeds

    @app_commands.command(name='oculi神瞳', description='查看不同地區的神瞳位置')
    @app_commands.rename(area='地區')
    @app_commands.choices(area=[
        Choice(name='蒙德', value=0),
        Choice(name='璃月', value=1),
        Choice(name='稻妻', value=2)])
    async def oculi(self, i: Interaction, area: int):
        embeds = GenshinCog.get_oculi_embeds(area)
        await GeneralPaginator(i, embeds).start(embeded=True)

    class EnkaPageView(DefaultView):
        def __init__(self, embeds: List[Embed], charas: List, equip_dict: dict, id: int, disabled: bool, member: Member, enka_data, index: int, bot: commands.Bot):
            super().__init__(timeout=None)
            self.add_item(GenshinCog.EnkaArtifactButton(
                equip_dict, id, disabled, member))
            self.add_item(GenshinCog.DamageCalculator(
                enka_data, id, disabled, member, embeds, index, bot, charas, equip_dict))
            self.add_item(GenshinCog.EnkaEmojiList())
            self.add_item(GenshinCog.EnkaPageSelect(
                embeds, charas, equip_dict, member, enka_data, bot))

    class EnkaPageSelect(Select):
        def __init__(self, embeds: List[Embed], charas: List, equip_dict: dict, member: Member, enka_data, bot: commands.Bot):
            options = [SelectOption(
                label='總覽', value=0, emoji='<:SCORE:983948729293897779>')]
            self.embeds = embeds
            self.equip_dict = equip_dict
            self.charas = charas
            self.member = member
            self.enka_data = enka_data
            self.bot = bot
            for chara in charas:
                options.append(SelectOption(
                    label=f"{characters_map.get(str(chara[2]))['rarity']}★ {chara[0]} {chara[1]}", value=f'{charas.index(chara)+1} {chara[2]}', emoji=getElementEmoji(characters_map.get(str(chara[2]))['element'])))
            super().__init__(placeholder='選擇分頁', min_values=1, max_values=1, options=options)

        async def callback(self, i: Interaction) -> Any:
            value = self.values[0].split()
            disabled = False if int(value[0]) != 0 else True
            chara_id = 0 if len(value) == 1 else value[1]
            view = GenshinCog.EnkaPageView(
                self.embeds, self.charas, self.equip_dict, chara_id, disabled, self.member, self.enka_data, int(value[0]), self.bot)
            await i.response.edit_message(embed=self.embeds[int(value[0])], view=view)

    class DamageTypeChoose(DefaultView):
        def __init__(self, enka_data: dict, chara_id: int, embeds: List[Embed], disabled: bool, index: int, bot: commands.Bot, charas, equip_dict: dict, member: Member, embed_index: int):
            super().__init__(timeout=None)
            self.enka_data = enka_data
            self.chara_id = chara_id
            self.embeds = embeds
            self.disabled = disabled
            self.index = index
            self.bot = bot
            self.charas = charas
            self.equip_dict = equip_dict
            self.embed_index = embed_index
            self.member = member
            for i in range(0, 3):
                style = ButtonStyle.blurple if i == index else ButtonStyle.gray
                self.add_item(GenshinCog.DamageTypeButton(enka_data, chara_id, member, i, bot,
                              style, self.equip_dict, self.charas, self.disabled, self.embeds, embed_index))

        @button(emoji='<:left:982588994778972171>', style=ButtonStyle.gray)
        async def go_back(self, i: Interaction, button: Button):
            view = GenshinCog.EnkaPageView(
                self.embeds, self.charas, self.equip_dict, self.chara_id, self.disabled, self.member, self.enka_data, self.embed_index, self.bot)
            await i.response.edit_message(embed=self.embeds[self.embed_index], view=view)

    class DamageTypeButton(Button):
        def __init__(self, enka_data: dict, chara_id: int, member: Member, index: int, bot: commands.Bot, style, equip_dict, charas, disabled, embeds, embed_index: int):
            labels = ['平均傷害', '沒暴擊傷害', '暴擊傷害']
            super().__init__(style=style, label=labels[index])
            self.id = chara_id
            self.member = member
            self.enka_data = enka_data
            self.index = index
            self.bot = bot
            self.equip_dict = equip_dict
            self.charas = charas
            self.disabled = disabled
            self.embeds = embeds
            self.embed_index = embed_index

        async def callback(self, i: Interaction) -> Any:
            await i.response.edit_message(embed=defaultEmbed('<a:LOADER:982128111904776242> 正在啟動傷害計算器 (1/6)'))
            view = GenshinCog.DamageTypeChoose(self.enka_data, self.id, self.embeds, self.disabled,
                                               self.index, self.bot, self.charas, self.equip_dict, self.member, self.embed_index)
            await i.edit_original_message(view=view)
            async for result in calculateDamage(self.enka_data, get_name.getName(int(self.id), True).replace(' ', ''), self.bot.browser, self.index):
                if isinstance(result, Embed):
                    await i.edit_original_message(embed=result)
                else:
                    embed = GenshinCog.parse_damage_embed(
                        self.id, result[0], self.member, self.index, result[1])
            await i.edit_original_message(embed=embed)

    def parse_damage_embed(chara_id: int, result: dict, member: Member, dmg: int, normal_attack_name: str):
        chara_name = get_name.getName(int(chara_id), True)
        result['重擊'], result['下落攻擊'] = result['下落攻擊'], result['重擊']
        embed = defaultEmbed(f'{get_name.getName(int(chara_id))} - 傷害')
        dmg_type_str = ['平均傷害', '沒暴擊傷害', '暴擊傷害']
        name = f'{get_name.getName(int(chara_id))} - {dmg_type_str[dmg]}'
        if chara_name == 'Xiao':
            name += ' (開Q狀態下)'
        elif chara_name == 'Raiden Shogun':
            name += ' (開E+願力50層)'
        elif chara_name == 'Kamisato Ayaka':
            name += ' (開E+被動碰到敵人)'
        elif chara_name == 'Hu Tao':
            name += '(開E+50%以下生命值)'
        embed.add_field(
            name=name,
            value=f'**{normal_attack_name}**',
            inline=False
        )
        field_count = 0
        for talent, damages in result.items():
            field_count += 1
            value = ''
            for label, label_damages in damages.items():
                if label == '低空墜地衝擊傷害':
                    label = '低空墜地傷害'
                elif label == '高空墜地衝擊傷害':
                    label = '高空墜地傷害'
                value += f'{label} - {label_damages[0]}\n'
            inline = False if field_count == 4 else True
            if talent == '重擊':
                talent = '下落攻擊'
            elif talent == '下落攻擊':
                talent = '重擊'
            embed.add_field(
                name=talent,
                value=value,
                inline=inline
            )
        embed.set_author(name=member, icon_url=member.avatar)
        embed.set_thumbnail(url=getCharacterIcon(int(chara_id)))
        return embed

    class DamageCalculator(Button):
        def __init__(self, enka_data: dict, chara_id: int, disabled: bool, member: Member, embeds: List[Embed], index: int, bot: commands.Bot, charas, equip_dict: dict):
            super().__init__(style=ButtonStyle.blurple, label='傷害計算', disabled=disabled)
            self.data = enka_data
            self.id = chara_id
            self.member = member
            self.enka_data = enka_data
            self.embeds = embeds
            self.button_disabled = disabled
            self.index = index
            self.bot = bot
            self.charas = charas
            self.equip_dict = equip_dict

        async def callback(self, i: Interaction) -> Any:
            await i.response.edit_message(embed=defaultEmbed('<a:LOADER:982128111904776242> 正在啟動傷害計算器 (1/6)'))
            view = GenshinCog.DamageTypeChoose(self.data, self.id, self.embeds, self.button_disabled,
                                               2, self.bot, self.charas, self.equip_dict, self.member, self.index)
            await i.edit_original_message(view=view)
            async for result in calculateDamage(self.enka_data, get_name.getName(int(self.id), True).replace(' ', ''), self.bot.browser, 2):
                if isinstance(result, Embed):
                    await i.edit_original_message(embed=result)
                else:
                    embed = GenshinCog.parse_damage_embed(
                        self.id, result[0], self.member, 2, result[1])
            await i.edit_original_message(embed=embed)

    def percent_symbol(propId: str):
        symbol = '%' if 'PERCENT' in propId or 'CRITICAL' in propId or 'CHARGE' in propId or 'HEAL' in propId or 'HURT' in propId else ''
        return symbol

    class EnkaArtifactButton(Button):
        def __init__(self, equip_dict: dict, id: int, disabled: bool, member: Member):
            self.equipments = equip_dict
            self.name = ''
            self.id = id
            self.member = member
            for e, val in equip_dict.items():
                if int(e) == int(id):
                    self.name = val['name']
                    self.chara_equipments = val['equipments']
            super().__init__(style=ButtonStyle.blurple, label=f'聖遺物', disabled=disabled)

        async def callback(self, i: Interaction) -> Any:
            artifact_emojis = [
                '<:Flower_of_Life:982167959717945374>', '<:Plume_of_Death:982167959915077643>',
                '<:Sands_of_Eon:982167959881547877>', '<:Goblet_of_Eonothem:982167959835402240>',
                '<:Circlet_of_Logos:982167959692787802>']
            set_name_simplify = {
                '昔日宗室之儀': '宗室',
                '冰風迷途的勇士': '冰套',
                '角鬥士的終幕禮': '角鬥士',
                '追憶之注連': '追憶',
                '絕緣之旗印': '絕緣',
                '平息鳴雷的尊者': '平雷',
                '如雷的盛怒': '如雷',
                '華館夢醒形骸記': '華館',
                '千岩牢固': '千岩'
            }
            embed = defaultEmbed(f'{self.name} - 聖遺物')
            for e in self.chara_equipments:
                if 'weapon' not in e:
                    artifact_name = get_name.getNameTextHash(
                        e['flat']['setNameTextMapHash'])
                    artifact_name = set_name_simplify.get(
                        artifact_name) or artifact_name
                    main = e["flat"]["reliquaryMainstat"]
                    symbol = GenshinCog.percent_symbol(main['mainPropId'])
                    artifact_str = f'{artifact_emojis[self.chara_equipments.index(e)]} {artifact_name}  +{int(e["reliquary"]["level"])-1}'
                    value = ''
                    value += f'**主詞條 {getStatEmoji(main["mainPropId"])} {main["statValue"]}{symbol}**\n'
                    artifact_calc_dict = {}
                    for sub in e['flat']['reliquarySubstats']:
                        symbol = GenshinCog.percent_symbol(sub['appendPropId'])
                        value += f'{getStatEmoji(sub["appendPropId"])} {sub["statValue"]}{symbol}\n'
                        artifact_calc_dict[sub["appendPropId"]
                                           ] = sub["statValue"]
                    if int(e["reliquary"]["level"])-1 == 20:
                        value += f'<:SCORE:983948729293897779> {int(calculateArtifactScore(artifact_calc_dict))}'
                    embed.add_field(
                        name=artifact_str,
                        value=value
                    )
                    embed.set_footer(text='聖遺物滿分99, 只有+20才會評分')
            embed.set_thumbnail(url=getCharacterIcon(int(self.id)))
            embed.set_author(name=self.member, icon_url=self.member.avatar)
            self.disabled = False
            await i.response.edit_message(embed=embed, view=self.view)

    class EnkaEmojiList(Button):
        def __init__(self):
            super().__init__(label='對照表', style=ButtonStyle.gray)

        async def callback(self, i: Interaction) -> Any:
            embed = defaultEmbed(
                '符號對照表',
                '<:HP:982068466410463272> 生命值\n'
                '<:HP_PERCENT:982138227450347553> 生命值%\n'
                '<:DEFENSE:982068463566721064> 防禦力\n'
                '<:DEFENSE_PERCENT:982138218822639626> 防禦力%\n'
                '<:ATTACK:982138214305390632> 攻擊力\n'
                '<:ATTACK_PERCENT:982138215832117308> 攻擊力%\n'
                '<:CRITICAL:982068460731392040> 暴擊率\n'
                '<:CRITICAL_HURT:982068462081933352> 暴擊傷害\n'
                '<:CHARGE_EFFICIENCY:982068459179503646> 充能效率\n'
                '<:ELEMENT_MASTERY:982068464938270730> 元素精通\n'
                '<:HEAL_ADD:982138224170401853> 治療加成\n\n'
                '<:ICE_ADD_HURT:982138229140635648> 冰元素傷害加成\n'
                '<:FIRE_ADD_HURT:982138221569900585> 火元素傷害加成\n'
                '<:ELEC_ADD_HURT:982138220248711178> 雷元素傷害加成\n'
                '<:GRASS_ADD_HURT:982138222891110432> 草元素傷害加成\n'
                '<:ROCK_ADD_HURT:982138232391237632> 岩元素傷害加成\n'
                '<:WATER_ADD_HURT:982138233813098556> 水元素傷害加成\n'
                '<:WIND_ADD_HURT:982138235239137290> 風元素傷害加成\n'
                '<:PHYSICAL_ADD_HURT:982138230923231242> 物理傷害加成'
            )
            await i.response.edit_message(embed=embed, view=self.view)

    @app_commands.command(name='profile角色展示', description='透過 enka API 查看各式原神數據')
    @app_commands.rename(member='其他人', custom_uid='uid')
    @app_commands.describe(member='查看其他人的資料', custom_uid='使用 UID 查閱')
    async def profile(self, i: Interaction, member: Member = None, custom_uid: int = None):
        await i.response.send_message(embed=defaultEmbed('<a:LOADER:982128111904776242> 獲取資料中'))
        member = member or i.user
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (member.id,))
        uid = await c.fetchone()
        if uid is None:
            uid_c = i.guild.get_channel(978871680019628032)
            await i.edit_original_message(embed=errEmbed('找不到 UID!', f'請先至 {uid_c.mention} 設置 UID!'))
            return
        uid = uid[0]
        uid = custom_uid if custom_uid is not None else uid
        async with self.bot.session.get(f'https://enka.shinshin.moe/u/{uid}/__data.json?key=b21lZ2FsdWxrZWt3dGY') as r:
            data = await r.json()
        if 'avatarInfoList' not in data:
            embed = errEmbed(message='請照下方的指示操作')
            embed.set_author(name='找不到資料', icon_url=i.user.avatar)
            await i.edit_original_message(embed=embed)
            embed = defaultEmbed(
                '<a:error_animated:982579472060547092> 錯誤', '請在遊戲中打開「顯示角色詳情」\n(申鶴有機率判斷錯誤, 可以考慮重新輸入指令)\n(資料最多需要10分鐘更新)')
            embed.set_image(url='https://i.imgur.com/frMsGHO.gif')
            await i.followup.send(embed=embed, ephemeral=True)
            return
        player = data['playerInfo']
        embeds = []
        sig = f"「{player['signature']}」" if 'signature' in player else '(該玩家沒有簽名)'
        overview = defaultEmbed(
            f'{player["nickname"]}',
            f"{sig}\n"
            f"玩家等級: Lvl. {player['level']}\n"
            f"世界等級: W{player['worldLevel']}\n"
            f"完成成就: {player['finishAchievementNum']}\n"
            f"深淵已達: {player['towerFloorIndex']}-{player['towerLevelIndex']}")
        overview.set_author(name=member, icon_url=member.avatar)
        overview.set_image(
            url=f"https://enka.shinshin.moe/ui/{namecards_map.get(int(player['nameCardId']))['Card']}.png")
        embeds.append(overview)
        charas = []
        for chara in player['showAvatarInfoList']:
            if chara['avatarId'] == 10000007 or chara['avatarId'] == 10000005:
                continue
            charas.append([get_name.getName(chara['avatarId']),
                          f"Lvl. {chara['level']}", chara['avatarId']])
        info = data['avatarInfoList']
        equipt_dict = {}
        for chara in info:
            if chara['avatarId'] == 10000007 or chara['avatarId'] == 10000005:
                continue
            prop = chara['fightPropMap']
            talent_levels = chara['skillLevelMap']
            talent_str = ''
            const = 0 if 'talentIdList' not in chara else len(
                chara['talentIdList'])
            for id, level in talent_levels.items():
                talent_str += f'{get_name.getName(int(id))} - Lvl. {level}\n'
            equipments = chara['equipList']
            equipt_dict[chara['avatarId']] = {
                'name': get_name.getName(chara["avatarId"]),
                'equipments': equipments
            }
            weapon_str = ''
            for e in equipments:
                if 'weapon' in e:
                    weapon_name = get_name.getNameTextHash(
                        e['flat']['nameTextMapHash'])
                    refinment_str = ''
                    if 'affixMap' in e['weapon']:
                        refinment_str = f"- R{int(list(e['weapon']['affixMap'].values())[0])+1}"
                    weapon_str += f"{weapon_name} - Lvl. {e['weapon']['level']} {refinment_str}\n"
                    weapon_sub_str = ''
                    if len(e['flat']['weaponStats']) == 2:
                        propId = e['flat']['weaponStats'][1]['appendPropId']
                        symbol = GenshinCog.percent_symbol(propId)
                        weapon_sub_str = f"{getStatEmoji(propId)} {e['flat']['weaponStats'][1]['statValue']}{symbol}"
                    weapon_str += f"<:ATTACK:982138214305390632> {e['flat']['weaponStats'][0]['statValue']}\n{weapon_sub_str}"
                    break
            max_level = 20
            ascention = chara['propMap']['1002']['ival']
            if ascention == 1:
                max_level = 30
            elif ascention == 2:
                max_level = 50
            elif ascention == 3:
                max_level = 60
            elif ascention == 4:
                max_level = 70
            elif ascention == 5:
                max_level = 80
            else:
                max_level = 90
            embed = defaultEmbed(
                f"{get_name.getName(chara['avatarId'])} C{const} (Lvl. {chara['propMap']['4001']['val']}/{max_level})",
                f'<:HP:982068466410463272> 生命值上限 - {round(prop["2000"])} ({round(prop["1"])}/{round(prop["2000"])-round(prop["1"])})\n'
                f"<:ATTACK:982138214305390632> 攻擊力 - {round(prop['2001'])} ({round(prop['4'])}/{round(prop['2001'])-round(prop['4'])})\n"
                f"<:DEFENSE:982068463566721064> 防禦力 - {round(prop['2002'])} ({round(prop['7'])}/{round(prop['2002'])-round(prop['7'])})\n"
                f"<:ELEMENT_MASTERY:982068464938270730> 元素精通 - {round(prop['28'])}\n"
                f"<:CRITICAL:982068460731392040> 暴擊率 - {round(prop['20']*100, 1)}%\n"
                f"<:CRITICAL_HURT:982068462081933352> 暴擊傷害 - {round(prop['22']*100, 1)}%\n"
                f"<:CHARGE_EFFICIENCY:982068459179503646> 元素充能效率 - {round(prop['23']*100, 1)}%\n"
                f"<:FRIENDSHIP:982843487697379391> 好感度 - {chara['fetterInfo']['expLevel']}")
            embed.add_field(
                name='天賦',
                value=talent_str,
                inline=False
            )
            embed.add_field(
                name='武器',
                value=weapon_str,
                inline=False
            )
            embed.set_thumbnail(url=getCharacterIcon(chara['avatarId']))
            embed.set_author(name=member, icon_url=member.avatar)
            embeds.append(embed)

        view = GenshinCog.EnkaPageView(
            embeds, charas, equipt_dict, 0, True, member, data, 0, self.bot)
        await i.edit_original_message(embed=overview, view=view)

    @app_commands.command(name='redeem兌換', description='兌換禮物碼')
    @app_commands.rename(code='兌換碼')
    async def redeem(self, i: Interaction, code: str):
        result = await self.genshin_app.redeemCode(i.user.id, code)
        result.set_author(name=i.user, url=i.user.avatar)
        await i.response.send_message(embed=result)

    @app_commands.command(name='wiki', description='查看原神維基百科')
    @app_commands.choices(wikiType=[Choice(name='角色', value=0)])
    @app_commands.rename(wikiType='類別', query='關鍵詞')
    @app_commands.describe(wikiType='要查看的維基百科分頁類別')
    async def wiki(self, i: Interaction, wikiType: int, query: str):
        span_styles = ['<span style="color:#80FFD7FF">', '<span style="color:#FFD780FF">', '<span style="color:#80C0FFFF">',
                       '<span style="color:#FF9999FF">', '<span style="color:#99FFFFFF">', '<span style="color:#FFACFFFF">', '<span style="color:#FFE699FF">']
        client = getClient()
        found = False
        if wikiType == 0:
            previews = await client.get_wiki_previews(WikiPageType.CHARACTER)
            await i.edit_original_message(embed=defaultEmbed(f'<a:LOADER:982128111904776242> 正在搜尋關鍵字'))
            for p in previews:
                d = (await client.get_wiki_page(p.id)).modules
                for item in d['屬性']['list']:
                    if item['key'] == '名字' and query in item['value']:
                        found = True
                        wiki = d
                        break
        if not found:
            return await i.edit_original_message(embed=errEmbed('<a:error_animated:982579472060547092> 找不到該維基百科頁面', '請重新檢查關鍵詞是否輸入錯誤'))
        result = [[], [], []]
        embed = defaultEmbed('搜尋結果')
        name = '屬性'
        value = ''
        for property in wiki['屬性']['list']:
            value += f"{property['key']} - {property['value'][0]}\n"
        embed.add_field(name=name, value=value)
        result[0].append(embed)
        embed = defaultEmbed('突破後屬性')
        for level in wiki['突破']['list'][:-1]:
            value = ''
            for combat in level['combatList'][1:]:
                value += f"{combat['key']} - {combat['values'][1]}\n"
            embed.add_field(name=level['key'], value=value)
        result[0].append(embed)
        embed = defaultEmbed('突破素材')
        for level in wiki['突破']['list'][1:-1]:
            value = ''
            for mat in level['materials']:
                mat = json.loads(mat.replace('$', ''))
                value += f"{(get_name.getWikiMaterialName(mat[0]['ep_id'])).replace(' ','')} - {mat[0]['amount']}\n"
            embed.add_field(name=level['key'], value=value)
        result[0].append(embed)
        embed = defaultEmbed('全圖')
        embed.set_image(url=urllib.parse.quote(wiki['畫廊']['pic'], safe=':/'))
        result[1].append(embed)
        for art in wiki['畫廊']['list']:
            embed = defaultEmbed(art['key'])
            embed.set_image(url=urllib.parse.quote(art['img'], safe=':/'))
            embed.set_footer(text=art['imgDesc'])
            result[1].append(embed)
        for talent in wiki['天賦']['list']:
            talent_desc = talent['desc'].replace(
                '<br/>', '\n').replace('<i>', '*').replace('</i>', '*').replace('</span>', '')
            for style in span_styles:
                if style in talent_desc:
                    talent_desc = talent_desc.replace(style, '')
            embed = defaultEmbed(talent['title'], talent_desc)
            embed.set_thumbnail(url=urllib.parse.quote(
                talent['icon_url'], safe=':/'))
            embed.set_image(url=urllib.parse.quote(
                talent['talent_img'], safe=':/'))
            result[2].append(embed)
        await GeneralPaginator(i, result[0]).start(embeded=True, edit_original_message=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GenshinCog(bot))
