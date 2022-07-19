import ast
import json
import re
from datetime import datetime
from typing import Any, List, Optional, Tuple

import aiosqlite
import discord
import GGanalysislib
import yaml
from data.game.elements import elements
from data.game.equip_types import equip_types
from data.game.fight_prop import fight_prop
from data.game.talent_books import talent_books
from data.game.GOModes import hitModes
from debug import DefaultView
from discord import (ButtonStyle, Embed, Emoji, Interaction, Member,
                     SelectOption, app_commands)
from discord.app_commands import Choice
from discord.ext import commands
from discord.ui import Button, Modal, Select, TextInput, button
from enkanetwork import EnkaNetworkAPI, EnkaNetworkResponse, UIDNotFounded
from enkanetwork.enum import DigitType, EquipmentsType
from pyppeteer.browser import Browser
from utility.apps.GenshinApp import GenshinApp
from utility.paginators.AbyssPaginator import AbyssPaginator
from utility.paginators.GeneralPaginator import GeneralPaginator
from utility.utils import (calculateArtifactScore, calculateDamage,
                           defaultEmbed, divide_chunks, errEmbed, getArtifact,
                           getCharacter, getClient, getConsumable,
                           getElementEmoji, getFightProp, getStatEmoji,
                           getTalent, getWeapon, getWeekdayName,
                           parse_damage_embed)

from cogs.wish import WishCog
from genshin.models import WikiPageType


class GenshinCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.genshin_app = GenshinApp(self.bot.db, self.bot)
        self.debug_toggle = self.bot.debug_toggle

# cookie

    class CookieModal(Modal):
        def __init__(self, db: aiosqlite.Connection, bot: commands.Bot):
            self.genshin_app = GenshinApp(db, bot)
            super().__init__(title='提交cookie', timeout=None, custom_id='cookie_modal')

        cookie = discord.ui.TextInput(
            label='Cookie',
            placeholder='請貼上從網頁上取得的Cookie, 取得方式請使用指令 /cookie',
            style=discord.TextStyle.long,
            required=True
        )

        async def on_submit(self, i: Interaction):
            result, success = await self.genshin_app.setCookie(i.user.id, self.cookie.value)
            await i.response.send_message(embed=result, ephemeral=not success)

        async def on_error(self, error: Exception, i: Interaction):
            embed = errEmbed(message=f'```{error}```').set_author(
                name='未知錯誤', icon_url=i.user.avatar)
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
            await i.response.send_message(embed=embed, ephemeral=True)
            await i.followup.send(content=code_msg, ephemeral=True)
        elif option == 1:
            await i.response.send_modal(GenshinCog.CookieModal(self.bot.db, self.bot))

    @app_commands.command(
        name='check即時便籤',
        description='查看即時便籤, 例如樹脂、洞天寶錢、探索派遣'
    )
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def check(self, i: Interaction, member: Optional[Member] = None):
        member = member or i.user
        result, success = await self.genshin_app.getRealTimeNotes(member.id)
        await i.response.send_message(embed=result, ephemeral=not success)
# /stats

    @app_commands.command(name='stats數據', description='查看原神資料, 如活躍時間、神瞳數量、寶箱數量')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def stats(self, i: Interaction, member: Optional[Member] = None):
        member = member or i.user
        result, success = await self.genshin_app.getUserStats(member.id)
        await i.response.send_message(embed=result, ephemeral=not success)
# /area

    @app_commands.command(name='area探索度', description='查看區域探索度')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def area(self, i: Interaction, member: Optional[Member] = None):
        member = member or i.user
        result, success = await self.genshin_app.getArea(member.id)
        await i.response.send_message(embed=result, ephemeral=not success)
# /claim

    @app_commands.command(name='claim登入獎勵', description='領取hoyolab登入獎勵')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def claim(self, i: Interaction, member: Member = None):
        member = member or i.user
        result, success = await self.genshin_app.claimDailyReward(member.id)
        await i.response.send_message(embed=result, ephemeral=not success)

    class DiaryLogView(DefaultView):
        def __init__(self, author: Member, member: Member, db: aiosqlite.Connection, bot: commands.Bot):
            super().__init__(timeout=None)
            self.author = author
            self.member = member
            self.genshin_app = GenshinApp(db, bot)

        async def interaction_check(self, interaction: Interaction) -> bool:
            if interaction.user.id != self.author.id:
                await interaction.response.send_message(embed=errEmbed().set_author(name='輸入 /diary 來打開你的旅行者日記', icon_url=interaction.user.avatar))
            return self.author.id == interaction.user.id

        @button(label='原石紀錄', emoji='<:primo:958555698596290570>')
        async def primo(self, i: Interaction, button: Button):
            result, success = await self.genshin_app.getDiaryLog(self.member.id)
            if not success:
                await i.response.send_message(embed=result, ephemeral=True)
            result = result[0]
            await i.response.send_message(embed=result, ephemeral=True)

        @button(label='摩拉紀錄', emoji='<:mora:958577933650362468>')
        async def mora(self, i: Interaction, button: Button):
            result, success = await self.genshin_app.getDiaryLog(self.member.id)
            if not success:
                await i.response.send_message(embed=result, ephemeral=True)
            result = result[1]
            await i.response.send_message(embed=result, ephemeral=True)

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
        result, success = await self.genshin_app.getDiary(member.id, month)
        if not success:
            await i.response.send_message(embed=result, ephemeral=not success)
        else:
            await i.response.send_message(embed=result, view=GenshinCog.DiaryLogView(i.user, member, self.bot.db, self.bot))

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
        result, success = await self.genshin_app.getAbyss(member.id, previous, overview)
        if not success:
            return await i.response.send_message(embed=result, ephemeral=True)
        if overview:
            return await i.response.send_message(embed=result)
        else:
            return await AbyssPaginator(i, result).start(embeded=True)

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
                await interaction.response.send_message(embed=errEmbed(message='輸入 `/remind` 來設置自己的提醒功能').set_author(name='這不是你的操作視窗', icon_url=interaction.user.avatar), ephemeral=True)
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
            user_chara_list: str = (await c.fetchone())[0]
            chara_str = ''
            if user_chara_list == '':
                talent_notif_chara_list = []
                chara_str = '目前尚未設置任何角色'
            else:
                talent_notif_chara_list: list = ast.literal_eval(
                    user_chara_list)
                for chara in talent_notif_chara_list:
                    chara_str += f'• {chara}\n'
            if chara_str == '':
                chara_str = '目前尚未設置任何角色'
            embed.add_field(name='目前已設置角色', value=chara_str)
            await interaction.response.edit_message(embed=embed, view=GenshinCog.TalentCharaChooserView(self.element, self.view.author, self.db, talent_notif_chara_list))

    class TalentCharaChooserView(DefaultView):
        def __init__(self, element: str, author: Member, db: aiosqlite.Connection, talent_notif_chara_list: list):
            super().__init__(timeout=None)
            self.add_item(GenshinCog.TalentCharaChooser(
                element, db, talent_notif_chara_list, author))
            self.talent_notif_chara_list = talent_notif_chara_list
            self.author = author
            self.db = db

        @button(emoji='<:left:982588994778972171>', style=ButtonStyle.gray, row=2)
        async def go_back(self, i: Interaction, button: Button):
            message = ''
            for chara in self.talent_notif_chara_list:
                message += f'• {chara}\n'
            if message == '':
                message = '目前尚未設置任何角色'
            embed = defaultEmbed()
            embed.add_field(name='已設置角色', value=message)
            embed.set_author(name='選擇想要設置提醒功能的角色元素', icon_url=i.user.avatar)
            await i.response.edit_message(embed=embed, view=GenshinCog.TalentElementChooser(i.user, self.db))

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(embed=errEmbed(message='輸入 `/remind` 來設置自己的提醒功能').set_author(name='這不是你的操作視窗', icon_url=interaction.user.avatar), ephemeral=True)
            return self.author.id == interaction.user.id

    class TalentCharaChooser(Select):
        def __init__(self, element: str, db: aiosqlite.Connection, talent_notif_chara_list: list, author: Member):
            options = []
            self.db = db
            self.author = author
            self.element = element
            for week_day, books in talent_books.items():
                for book_name, characters in books.items():
                    for character_name, element_name in characters.items():
                        if element == element_name:
                            desc = f'{week_day} - 「{book_name}」'
                            if character_name in talent_notif_chara_list:
                                desc = '已設置過此角色, 再次選擇將會移除'
                            options.append(SelectOption(
                                label=character_name, description=desc, emoji=getCharacter(name=character_name)['emoji']))
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
            await c.execute('SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?', (interaction.user.id,))
            chara_list = ast.literal_eval((await c.fetchone())[0])
            chara_str = ''
            for chara in chara_list:
                chara_str += f'• {chara}\n'
            chara_str = '目前尚未設置任何角色' if chara_str == '' else chara_str
            embed = defaultEmbed(message='選擇已經設置過的角色將移除該角色的提醒')
            embed.set_author(
                name='選擇角色', icon_url=interaction.user.avatar)
            embed.add_field(name='目前已設置角色', value=chara_str)
            c = await self.db.cursor()
            await c.execute('SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?', (interaction.user.id,))
            user_chara_list: list = (await c.fetchone())[0]
            if user_chara_list == '':
                talent_notif_chara_list = []
            else:
                talent_notif_chara_list: list = ast.literal_eval(
                    user_chara_list)
            await interaction.response.edit_message(embed=embed, view=GenshinCog.TalentCharaChooserView(self.element, self.author, self.db, talent_notif_chara_list))

    @app_commands.command(name='remind提醒', description='設置提醒功能')
    @app_commands.rename(function='功能', toggle='開關')
    @app_commands.describe(function='提醒功能', toggle='要開啟或關閉該提醒功能')
    @app_commands.choices(function=[Choice(name='樹脂提醒', value=0), Choice(name='天賦素材提醒', value=1), Choice(name='隱私設定', value=2)],
                          toggle=[Choice(name='開 (調整設定)', value=1), Choice(name='關', value=0)])
    async def remind(self, i: Interaction, function: int, toggle: int = 1):
        if function == 0:
            if toggle == 0:
                result, success = await self.genshin_app.setResinNotification(i.user.id, 0, None, None)
                await i.response.send_message(embed=result, ephemeral=not success)
            else:
                modal = GenshinCog.ResinNotifModal()
                await i.response.send_modal(modal)
                await modal.wait()
                result, success = await self.genshin_app.setResinNotification(i.user.id, toggle, modal.resin_threshold.value, modal.max_notif.value)
                await i.followup.send(embed=result, ephemeral=not success)
        elif function == 1:
            if toggle == 0:
                c: aiosqlite.Cursor = await self.bot.db.cursor()
                await c.execute('UPDATE genshin_accounts SET talent_notif_toggle = 0 WHERE user_id = ?', (i.user.id,))
                await self.bot.db.commit()
                embed = defaultEmbed()
                embed.set_author(name='天賦提醒功能已關閉', icon_url=i.user.avatar)
                await i.response.send_message(embed=embed)
            else:
                c: aiosqlite.Cursor = await self.bot.db.cursor()
                message = ''
                await c.execute('SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?', (i.user.id,))
                talent_notif_chara_list: list = (await c.fetchone())[0]
                if talent_notif_chara_list == '':
                    talent_notif_chara_list = []
                else:
                    talent_notif_chara_list: list = ast.literal_eval(
                        talent_notif_chara_list)
                for chara in talent_notif_chara_list:
                    message += f'• {chara}\n'
                if message == '':
                    message = '目前尚未設置任何角色'
                embed = defaultEmbed()
                embed.add_field(name='已設置角色', value=message)
                embed.set_author(name='選擇想要設置提醒功能的角色元素',
                                 icon_url=i.user.avatar)
                view = GenshinCog.TalentElementChooser(i.user, self.bot.db)
                await i.response.send_message(embed=embed, view=view)
        elif function == 2:
            embed = defaultEmbed(message='1. 右鍵「緣神有你」\n2. 點擊「隱私設定」\n3. 將開關打開')
            embed.set_author(name='如何讓申鶴進入你的私訊?', icon_url=i.user.avatar)
            embed.set_image(url='https://i.imgur.com/sYg4SpD.gif')
            await i.response.send_message(embed=embed, ephemeral=True)

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
        def __init__(self, db: aiosqlite.Connection, emojis: List, author: Member, bot: commands.Bot):
            super().__init__(timeout=None)
            self.author = author
            for i in range(0, 6):
                self.add_item(GenshinCog.ElementButton(
                    i, db, emojis[i], author, bot))

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(embed=errEmbed(message='輸入 `/build` 來查看角色配置').set_author(name='這不是你的操作視窗', icon_url=interaction.user.avatar), ephemeral=True)
            return self.author.id == interaction.user.id

    class ElementButton(Button):  # 元素按鈕
        def __init__(self, index: int, db: aiosqlite.Connection, emoji: Emoji, author: Member, bot: commands.Bot):
            self.index = index
            self.db = db
            self.author = author
            self.bot = bot
            super().__init__(style=ButtonStyle.gray, row=index % 2, emoji=emoji)

        async def callback(self, i: Interaction):
            view = GenshinCog.CharactersDropdownView(
                self.index, self.db, self.author, self.bot)
            embed = defaultEmbed().set_author(name='選擇角色', icon_url=i.user.avatar)
            await i.response.edit_message(embed=embed, view=view)

    class CharactersDropdownView(DefaultView):  # 角色配置下拉選單的view
        def __init__(self, index: int, db: aiosqlite.Connection, author: Member, bot: commands.Bot):
            super().__init__(timeout=None)
            self.db = db
            self.author = author
            self.bot = bot
            self.add_item(
                GenshinCog.BuildCharactersDropdown(index, db, author, bot))

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(embed=errEmbed(message='輸入 `/build` 來查看角色配置').set_author(name='這不是你的操作視窗', icon_url=interaction.user.avatar), ephemeral=True)
            return self.author.id == interaction.user.id

        @button(emoji='<:left:982588994778972171>', style=ButtonStyle.gray, row=1)
        async def back(self, i: Interaction, button: Button):
            emojis = []
            ids = [982138235239137290, 982138229140635648, 982138220248711178,
                   982138232391237632, 982138233813098556, 982138221569900585]
            for id in ids:
                emojis.append(i.client.get_emoji(id))
            view = GenshinCog.ElementChooseView(
                self.db, emojis, self.author, self.bot)
            embed = defaultEmbed().set_author(name='選擇要查看角色的元素', icon_url=i.user.avatar)
            await i.response.edit_message(embed=embed, view=view)

    class BuildCharactersDropdown(Select):  # 角色配置下拉選單(依元素分類)
        def __init__(self, index: int, db: aiosqlite.Connection, author: Member, bot: commands.Bot):
            self.genshin_app = GenshinApp(db, bot)
            self.index = index
            self.db = db
            self.author = author
            self.bot = bot
            elemenet_chinese = ['風', '冰', '雷', '岩', '水', '火']
            elements = ['anemo', 'cryo', 'electro', 'geo', 'hydro', 'pyro']
            with open(f'data/builds/{elements[index]}.yaml', 'r', encoding='utf-8') as f:
                self.build_dict = yaml.full_load(f)
            options = []
            for character, value in self.build_dict.items():
                options.append(SelectOption(label=character, value=character,
                               emoji=getCharacter(name=character)['emoji']))
            super().__init__(
                placeholder=f'{elemenet_chinese[index]}元素角色', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: Interaction):
            result, has_thoughts = await self.genshin_app.getBuild(self.build_dict, str(self.values[0]))
            view = GenshinCog.BuildSelectView(
                len(result), result, self.index, self.db, self.author, has_thoughts, self.bot)
            await interaction.response.edit_message(embed=result[0][0], view=view)

    class BuildSelectView(DefaultView):
        def __init__(self, total: int, build_embeds: List, index: int, db: aiosqlite.Connection, author: Member, has_thoughts: bool, bot: commands.Bot):
            super().__init__(timeout=None)
            self.index = index
            self.db = db
            self.author = author
            self.bot = bot
            self.add_item(GenshinCog.BuildSelect(
                total, build_embeds, has_thoughts))

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(embed=errEmbed(message='輸入 `/build` 來查看角色配置').set_author(name='這不是你的操作視窗', icon_url=interaction.user.avatar), ephemeral=True)
            return self.author.id == interaction.user.id

        @button(emoji='<:left:982588994778972171>', style=ButtonStyle.gray, row=1)
        async def back(self, i: Interaction, button: Button):
            view = GenshinCog.CharactersDropdownView(
                self.index, self.db, self.author, self.bot)
            embed = defaultEmbed().set_author(name='選擇角色', icon_url=i.user.avatar)
            await i.response.edit_message(embed=embed, view=view)

    class BuildSelect(Select):
        def __init__(self, total: int, build_embeds: List, has_thoughts: bool):
            options = []
            self.embeds = build_embeds
            for i in range(1, total+1):
                options.append(SelectOption(
                    label=f'配置{i} - {build_embeds[i-1][1]} - {build_embeds[i-1][2]}', value=i))
            if has_thoughts:
                options[-1] = SelectOption(
                    label=f'聖遺物思路', value=total)
            super().__init__(
                placeholder=f'選擇配置', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: Interaction) -> Any:
            await interaction.response.edit_message(embed=self.embeds[int(self.values[0])-1][0])

    # /build
    @app_commands.command(name='build角色配置', description='查看角色推薦主詞條、畢業面板、不同配置、聖遺物思路等')
    async def build(self, i: Interaction):
        emojis = []
        ids = [982138235239137290, 982138229140635648, 982138220248711178,
               982138232391237632, 982138233813098556, 982138221569900585]
        for id in ids:
            emojis.append(self.bot.get_emoji(id))
        view = GenshinCog.ElementChooseView(
            self.bot.db, emojis, i.user, self.bot)
        await i.response.send_message(embed=defaultEmbed().set_author(name='選擇要查看角色的元素', icon_url=i.user.avatar), view=view)

    @app_commands.command(name='uid查詢', description='查詢特定使用者的原神UID')
    @app_commands.rename(player='使用者')
    @app_commands.describe(player='選擇想要查詢的使用者')
    async def search_uid(self, i: Interaction, player: Member):
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (player.id,))
        uid = await c.fetchone()
        if uid is None:
            return await i.response.send_message(embed=errEmbed('這個使用者還沒有註冊過UID\n請至 <#978871680019628032> 註冊 UID').set_author(name='查無 UID', icon_url=player.avatar), ephemeral=True)
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
                    label=item[0], value=item[1], emoji=getCharacter(name=item[0])['emoji']))
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
            await i.response.send_message(embed=defaultEmbed(message='使用`/todo`指令來查看你的代辦事項').set_author(name='代辦事項新增成功', icon_url=i.user.avatar), ephemeral=True)

    calc = app_commands.Group(name="calc", description="原神養成計算機")

    @calc.command(name='notown所有角色', description='計算一個自己不擁有的角色所需的素材')
    async def calc_notown(self, i: Interaction):
        client = getClient()
        charas = await client.get_calculator_characters()
        chara_list = []
        for chara in charas:
            chara_list.append([chara.name, chara.id, chara.element])
        button_view = GenshinCog.CalcultorElementButtonView(
            i.user, chara_list, '角色')
        embed = defaultEmbed().set_author(name='選擇角色的元素', icon_url=i.user.avatar)
        await i.response.send_message(embed=embed, view=button_view)
        await button_view.wait()
        select_view = GenshinCog.CalculatorItems(
            i.user, button_view.element_chara_list, button_view.item_type)
        embed = defaultEmbed().set_author(name='選擇角色', icon_url=i.user.avatar)
        await i.edit_original_message(embed=embed, view=select_view)
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
        value = ''
        for consumable in cost.character:
            value += f'{getConsumable(consumable.id)["emoji"]} {consumable.name}  x{consumable.amount}\n'
            materials.append([consumable.name, consumable.amount])
        if value == '':
            value = '不需要任何素材'
        embed.add_field(name='角色所需素材', value=value, inline=False)
        value = ''
        for consumable in cost.talents:
            value += f'{getConsumable(consumable.id)["emoji"]} {consumable.name}  x{consumable.amount}\n'
            materials.append([consumable.name, consumable.amount])
        if value == '':
            value = '不需要任何素材'
        embed.add_field(name='天賦所需素材', value=value, inline=False)
        disabled = True if len(materials) == 0 else False
        view = GenshinCog.AddMaterialsView(
            self.bot.db, disabled, i.user, materials)
        await i.edit_original_message(embed=embed, view=view)

    @calc.command(name='character擁有角色', description='個別計算一個自己擁有的角色所需的素材')
    async def calc_character(self, i: Interaction):
        client, uid, only_uid, user = await self.genshin_app.getUserCookie(i.user.id)
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
        embed = defaultEmbed().set_author(name='選擇角色的元素', icon_url=i.user.avatar)
        await i.response.send_message(embed=embed, view=button_view)
        await button_view.wait()
        embed = defaultEmbed().set_author(name='選擇角色', icon_url=i.user.avatar)
        select_view = GenshinCog.CalculatorItems(
            i.user, button_view.element_chara_list, button_view.item_type)
        await i.edit_original_message(embed=embed, view=select_view)
        await select_view.wait()
        valid, error_msg = self.check_level_validity(
            select_view.target, select_view.a, select_view.e, select_view.q)
        if not valid:
            return await i.followup.send(embed=error_msg, ephemeral=True)
        chara_name = ''
        for chara in chara_list:
            if int(select_view.value) == int(chara[1]):
                chara_name = chara[0]
        details = await client.get_character_details(select_view.value)
        character = (await client.get_calculator_characters(query=chara_name, sync=True))[0]
        if character.level > select_view.target:
            return await i.followup.send(embed=errEmbed().set_author(name='目前等級大於目標等級', icon_url=i.user.avatar))
        talent_targets = [select_view.a, select_view.e, select_view.q]
        for index in range(0, 3):
            if details.talents[index].level > talent_targets[index]:
                return await i.followup.send(embed=errEmbed().set_author(name='目前等級大於目標等級', icon_url=i.user.avatar))
        embed = defaultEmbed().set_author(name='計算結果', icon_url=i.user.avatar)
        embed.set_thumbnail(url=character.icon)
        value = ''
        value += f'角色等級 {character.level} ▸ {select_view.target}\n'
        value += f'普攻等級 {details.talents[0].level} ▸ {select_view.a}\n'
        value += f'元素戰技(E)等級 {details.talents[1].level} ▸ {select_view.e}\n'
        value += f'元素爆發(Q)等級 {details.talents[2].level} ▸ {select_view.q}\n'
        embed.add_field(name='計算內容', value=value, inline=False)
        cost = await (
            client.calculator()
            .set_character(select_view.value, current=character.level, target=select_view.target)
            .with_current_talents(attack=select_view.a, skill=select_view.e, burst=select_view.q)
        )
        materials = []
        value = ''
        for consumable in cost.character:
            value += f'{getConsumable(consumable.id)["emoji"]} {consumable.name}  x{consumable.amount}\n'
            materials.append([consumable.name, consumable.amount])
        if value == '':
            value = '不需要任何素材'
        embed.add_field(name='角色所需素材', value=value, inline=False)
        value = ''
        for consumable in cost.talents:
            value += f'{getConsumable(consumable.id)["emoji"]} {consumable.name}  x{consumable.amount}\n'
            materials.append([consumable.name, consumable.amount])
        if value == '':
            value = '不需要任何素材'
        embed.add_field(name='天賦所需素材', value=value, inline=False)
        disabled = True if len(materials) == 0 else False
        view = GenshinCog.AddMaterialsView(
            self.bot.db, disabled, i.user, materials)
        await i.edit_original_message(embed=embed, view=view)

    class CalcWeaponView(DefaultView):
        def __init__(self, weapons, author: Member, db: aiosqlite.Connection):
            super().__init__(timeout=None)
            self.author = author
            self.add_item(GenshinCog.CalcWeaponSelect(weapons, db))

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(embed=errEmbed(message='輸入 `/calc weapon` 來計算武器所需素材').set_author(name='這不是你的操作視窗', icon_url=interaction.user.avatar))
            return self.author.id == interaction.user.id

    class CalcWeaponSelect(Select):
        def __init__(self, weapons, db: aiosqlite.Connection):
            options = []
            for w in weapons:
                options.append(SelectOption(
                    label=w.name, value=w.id, emoji=getWeapon(w.id)['emoji']))
            super().__init__(placeholder='選擇武器', options=options)
            self.weapons = weapons
            self.db = db

        async def callback(self, interaction: Interaction) -> Any:
            await interaction.response.send_modal(GenshinCog.CalcWeaponModal(self.values[0], self.db))

    class CalcWeaponModal(Modal):
        current = TextInput(
            label='目前等級', placeholder='例如: 1')
        target = TextInput(label='目標等級', placeholder='例如: 90')

        def __init__(self, chosen_weapon: str, db: aiosqlite.Connection) -> None:
            super().__init__(
                title=f'設置{getWeapon(chosen_weapon)["name"]}要計算的等級', timeout=None)
            self.chosen_weapon = chosen_weapon
            self.db = db

        async def on_submit(self, interaction: Interaction) -> None:
            if int(self.current.value) < 1 or int(self.target.value) < 1:
                return await interaction.response.send_message(embed=errEmbed().set_author(name='等級不可小於1', icon_url=interaction.user.avatar), ephemeral=True)
            if int(self.target.value) > 90 or int(self.current.value) > 90:
                return await interaction.response.send_message(embed=errEmbed().set_author(name='等級不可大於90', icon_url=interaction.user.avatar), ephemeral=True)
            client = getClient()
            cost = await (
                client.calculator()
                .set_weapon(self.chosen_weapon, current=int(self.current.value), target=int(self.target.value))
            )
            embed = defaultEmbed().set_author(name='計算結果', icon_url=interaction.user.avatar)
            embed.add_field(
                name='計算內容', value=f'武器: {getWeapon(self.chosen_weapon)["name"]}\n等級: {self.current.value} ▸ {self.target.value}', inline=False)
            materials = []
            value = ''
            for consumable in cost.weapon:
                value += f'{getConsumable(consumable.id)["emoji"]} {consumable.name}  x{consumable.amount}\n'
                materials.append([consumable.name, consumable.amount])
            if value == '':
                value = '不需要任何素材'
            embed.add_field(name='武器所需素材', value=value, inline=False)
            embed.set_thumbnail(url=getWeapon(self.chosen_weapon)["icon"])
            disabled = True if len(materials) == 0 else False
            view = GenshinCog.AddMaterialsView(
                self.db, disabled, interaction.user, materials)
            await interaction.response.edit_message(embed=embed, view=view)

    @calc.command(name='weapon武器', description='計算武器所需的素材')
    @app_commands.rename(types='武器類別', rarities='稀有度')
    @app_commands.describe(types='要計算的武器的類別', rarities='武器的稀有度')
    @app_commands.choices(
        types=[
            Choice(name='單手劍', value=1),
            Choice(name='法器', value=10),
            Choice(name='大劍', value=11),
            Choice(name='弓箭', value=12),
            Choice(name='長槍', value=13)],
        rarities=[
            Choice(name='★★★★★', value=5),
            Choice(name='★★★★', value=4),
            Choice(name='★★★', value=3),
            Choice(name='★★', value=2),
            Choice(name='★', value=1)])
    async def calc_weapon(self, i: Interaction, types: int, rarities: int):
        client = getClient()
        weapons = await client.get_calculator_weapons(types=[types], rarities=[rarities])
        await i.response.send_message(view=GenshinCog.CalcWeaponView(weapons, i.user, self.bot.db))

    def oculi_embed_style(element: str, url: str):
        embed = defaultEmbed(f'{element}神瞳位置')
        embed.set_image(url=url)
        embed.set_footer(text='單純功能搬運, 圖源並非來自我')
        return embed

    def get_oculi_embeds(area: int):
        embeds = []
        if area == 0:
            for i in range(1, 5):
                url = f'https://fortoffans.github.io/Maps/Oculus/Anemoculus/Map_Anemoculus_{i}.jpg?width=831&height=554'
                embeds.append(GenshinCog.oculi_embed_style('風', url))
        elif area == 1:
            for i in range(1, 6):
                url = f'https://images-ext-1.discordapp.net/external/Gm5I4dqqanZEksPk7pggWfwoqW5UOiKPJP8Rt-uYQ5E/https/fortoffans.github.io/Maps/Oculus/Geoculus/Map_Geoculus_{i}.jpg?width=831&height=554'
                embeds.append(GenshinCog.oculi_embed_style('岩', url))
        elif area == 2:
            for i in range(1, 7):
                url = f'https://images-ext-1.discordapp.net/external/u6qgVi5Fk28_wwEuu3OS9blTzC-7JQpridJiWv0vI5s/https/fortoffans.github.io/Maps/Oculus/Electroculus/Map_Electroculus_{i}.jpg?width=831&height=554'
                embeds.append(GenshinCog.oculi_embed_style('雷', url))
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
        def __init__(self, embeds: dict[int, Embed], artifact_embeds: dict[int, Embed], character_options: list[SelectOption], data: EnkaNetworkResponse, browser: Browser, eng_data: EnkaNetworkResponse, author: Member):
            super().__init__(timeout=None)
            self.embeds = embeds
            self.artifact_embeds = artifact_embeds
            self.character_options = character_options
            self.character_id = None
            self.browser = browser
            self.author = author
            self.data = data
            self.eng_data = eng_data
            self.add_item(GenshinCog.EnkaArtifactButton())
            self.add_item(GenshinCog.CalculateDamageButton())
            self.add_item(GenshinCog.EnkaPageSelect(character_options))
            self.children[0].disabled = True
            self.children[1].disabled = True
            
        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(embed=errEmbed(message='指令: `/profile`').set_author(name='你不是這個指令的發起者', icon_url=interaction.user.avatar), ephemeral=True)
            return self.author.id == interaction.user.id

    class EnkaPageSelect(Select):
        def __init__(self, character_options: list[SelectOption]):
            super().__init__(placeholder='選擇角色', options=character_options)

        async def callback(self, i: Interaction) -> Any:
            disabled = True if self.values[0] == '0' else False
            self.view.children[0].disabled = disabled
            self.view.children[1].disabled = disabled
            self.view.character_id = self.values[0]
            await i.response.edit_message(embed=self.view.embeds[self.values[0]], view=self.view)

    class EnkaArtifactButton(Button):
        def __init__(self):
            super().__init__(label='聖遺物', style=ButtonStyle.blurple)

        async def callback(self, i: Interaction) -> Any:
            self.disabled = True
            await i.response.edit_message(embed=self.view.artifact_embeds[self.view.character_id], view=self.view)
    
    class CalculateDamageButton(Button):
        def __init__(self):
            super().__init__(style=ButtonStyle.blurple, label='計算傷害')

        async def callback(self, i: Interaction) -> Any:
            view = GenshinCog.DamageCalculatorView(self.view)
            reactionMode_elements = ['Pyro', 'Cryo', 'Hydro', 'pyro', 'cryo']
            for item in view.children:
                item.disabled = True
            view.children[0].disabled = False
            await i.response.edit_message(embed=defaultEmbed('<a:LOADER:982128111904776242> 計算傷害中', '約需 5 至 10 秒'), view=view)
            embed = await calculateDamage(self.view.eng_data, self.view.browser, self.view.character_id, 'critHit', i.user)
            for item in view.children:
                item.disabled = False
            view.children[4].disabled = True
            character_element = getCharacter(self.view.character_id)['element']
            if character_element in reactionMode_elements or view.infusionAura in reactionMode_elements:
                view.children[4].disabled = False
            await i.edit_original_message(embed=embed, view=view)
            
    async def returnDamage(view: DefaultView, i: Interaction):
        for item in view.children:
            item.disabled = True
        view.children[0].disabled = False
        await i.response.edit_message(embed=defaultEmbed('<a:LOADER:982128111904776242> 計算中', '約需 5 至 10 秒'), view=view)
        embed = await calculateDamage(view.enka_view.eng_data, view.enka_view.browser, view.enka_view.character_id, view.hitMode, i.user, view.reactionMode, view.infusionAura, view.team, )
        for item in view.children:
            item.disabled = False
        reactionMode_disabled = True
        character_element = getCharacter(view.enka_view.character_id)['element']
        reactionMode_elements = ['Pyro', 'Cryo', 'Hydro', 'pyro', 'cryo']
        if character_element in reactionMode_elements or view.infusionAura in reactionMode_elements:
            reactionMode_disabled = False
        view.children[4].disabled = reactionMode_disabled
        await i.edit_original_message(embed=embed, view=view)

    class DamageCalculatorView(DefaultView):
        def __init__(self, enka_view: DefaultView):
            super().__init__(timeout=None)
            # defining damage calculation variables
            self.enka_view = enka_view
            self.hitMode = 'critHit'
            self.reactionMode = ''
            self.infusionAura = ''
            self.team = []
            
            # producing select options
            reactionMode_options = [SelectOption(label='無反應', value='none')]
            element = getCharacter(self.enka_view.character_id)['element']
            if element == 'Cryo' or self.infusionAura == 'cryo':
                reactionMode_options.append(SelectOption(label='融化', value='cryo_melt'))
            elif element == 'Pyro' or self.infusionAura == 'pyro':
                reactionMode_options.append(SelectOption(label='蒸發', value='pyro_vaporize'))
                reactionMode_options.append(SelectOption(label='融化', value='pyro_melt'))
            elif element == 'Hydro':
                reactionMode_options.append(SelectOption(label='蒸發', value='hydro_vaporize'))
            
            team_options = []
            option: SelectOption
            for option in self.enka_view.character_options:
                if str(option.value) == str(self.enka_view.character_id):
                    continue
                team_options.append(SelectOption(label=option.label, value=option.value, emoji=option.emoji))
            del team_options[0]
            
            # adding items
            self.add_item(GenshinCog.EnkaGoBackButton())
            for index in range(0, 3):
                self.add_item(GenshinCog.HitModeButton(index))
            self.add_item(GenshinCog.ReactionModeSelect(reactionMode_options))
            self.add_item(GenshinCog.InfusionAuraSelect())
            self.add_item(GenshinCog.TeamSelect(team_options))

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.enka_view.author.id != interaction.user.id:
                await interaction.response.send_message(embed=errEmbed(message='指令: `/profile`').set_author(name='你不是這個指令的發起者', icon_url=interaction.user.avatar), ephemeral=True)
            return self.enka_view.author.id == interaction.user.id

    class EnkaGoBackButton(Button):
        def __init__(self):
            super().__init__(emoji='<:left:982588994778972171>')

        async def callback(self, i: Interaction):
            for item in self.view.enka_view.children:
                item.disabled = False
            await i.response.edit_message(embed=self.view.enka_view.embeds[self.view.enka_view.character_id], view=self.view.enka_view)

    class HitModeButton(Button):
        def __init__(self, index: int):
            super().__init__(style=ButtonStyle.blurple, label=(list(hitModes.values())[index]))
            self.index = index
        
        async def callback(self, i: Interaction) -> Any:
            self.view.hitMode = (list(hitModes.keys()))[self.index]
            await GenshinCog.returnDamage(self.view, i)

    class ReactionModeSelect(Select):
        def __init__(self, options: list[SelectOption]):
            super().__init__(placeholder='選擇元素反應', options=options)

        async def callback(self, i: Interaction) -> Any:
            self.view.reactionMode = '' if self.values[0] == 'none' else self.values[0]
            await GenshinCog.returnDamage(self.view, i)

    class InfusionAuraSelect(Select):
        def __init__(self):
            options = [SelectOption(label='無附魔', value='none'), SelectOption(
                label='火元素附魔', description='班尼特六命', value='pyro'), SelectOption(label='冰元素附魔', description='重雲E', value='cryo')]
            super().__init__(placeholder='選擇近戰元素附魔', options=options)

        async def callback(self, i: Interaction) -> Any:
            self.view.infusionAura = '' if self.values[0] == 'none' else self.values[0]
            await GenshinCog.returnDamage(self.view, i)

    class TeamSelect(Select):
        def __init__(self, options):
            super().__init__(placeholder='選擇隊友', options=options, max_values=3)

        async def callback(self, i: Interaction) -> Any:
            self.view.team = self.values
            await GenshinCog.returnDamage(self.view, i)

    @app_commands.command(name='profile角色展示', description='透過 enka API 查看各式原神數據')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他人的資料')
    async def profile(self, i: Interaction, member: Member = None):
        await i.response.defer()
        member = member or i.user
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (member.id,))
        uid = await c.fetchone()
        if uid is None:
            uid_c = i.guild.get_channel(978871680019628032)
            return await i.followup.send(embed=errEmbed('找不到 UID!', f'請先至 {uid_c.mention} 設置 UID!'), ephemeral=True)
        enka_client: EnkaNetworkAPI = self.bot.enka_client
        enka_client.lang = 'cht'
        data: EnkaNetworkResponse = await enka_client.fetch_user(uid[0])
        enka_client.lang = 'en'
        eng_data = await enka_client.fetch_user(uid[0])
        if data.characters is None:
            embed = defaultEmbed(message='請在遊戲中打開「顯示角色詳情」\n(申鶴有機率判斷錯誤, 可以考慮重新輸入指令)\n(開啟後, 資料最多需要10分鐘更新)').set_author(
                name='找不到資料', icon_url=i.user.avatar).set_image(url='https://i.imgur.com/frMsGHO.gif')
            return await i.followup.send(embed=embed, ephemeral=True)
        embeds = {}
        sig = f'「{data.player.signature}」\n' if data.player.signature != '' else ''
        overview = defaultEmbed(
            f'{data.player.nickname}',
            f"{sig}"
            f"玩家等級: Lvl. {data.player.level}\n"
            f"世界等級: W{data.player.world_level}\n"
            f"完成成就: {data.player.achievement}\n"
            f"深淵已達: {data.player.abyss_floor}-{data.player.abyss_room}")
        overview.set_author(name=member, icon_url=member.avatar)
        overview.set_image(url=data.player.namecard.banner)
        embeds['0'] = overview
        options = [SelectOption(label='總覽', value=0,
                                emoji='<:SCORE:983948729293897779>')]
        artifact_embeds = {}
        for character in data.characters:
            options.append(SelectOption(label=f'{character.name} | Lvl. {character.level}',
                           value=character.id, emoji=getCharacter(character.id)['emoji']))
            embed = defaultEmbed(
                f'{character.name} C{character.constellations_unlocked}R{character.equipments[-1].refinement} | Lvl. {character.level}/{character.max_level}'
            )
            embed.add_field(
                name='屬性',
                value=f'<:HP:982068466410463272> 生命值上限 - {character.stats.FIGHT_PROP_MAX_HP.to_rounded()}\n'
                f"<:ATTACK:982138214305390632> 攻擊力 - {character.stats.FIGHT_PROP_CUR_ATTACK.to_rounded()}\n"
                f"<:DEFENSE:982068463566721064> 防禦力 - {character.stats.FIGHT_PROP_CUR_DEFENSE.to_rounded()}\n"
                f"<:ELEMENT_MASTERY:982068464938270730> 元素精通 - {character.stats.FIGHT_PROP_ELEMENT_MASTERY.to_rounded()}\n"
                f"<:CRITICAL:982068460731392040> 暴擊率 - {character.stats.FIGHT_PROP_CRITICAL.to_percentage_symbol()}\n"
                f"<:CRITICAL_HURT:982068462081933352> 暴擊傷害 - {character.stats.FIGHT_PROP_CRITICAL_HURT.to_percentage_symbol()}\n"
                f"<:CHARGE_EFFICIENCY:982068459179503646> 元素充能效率 - {character.stats.FIGHT_PROP_CHARGE_EFFICIENCY.to_percentage_symbol()}\n"
                f"<:FRIENDSHIP:982843487697379391> 好感度 - {character.friendship_level}",
                inline=False
            )
            value = ''
            for skill in character.skills:
                value += f'{skill.name} | Lvl. {skill.level}\n'
            embed.add_field(
                name='天賦',
                value=value
            )
            weapon = character.equipments[-1]
            weapon_sub_stats = ''
            for substat in weapon.detail.substats:
                weapon_sub_stats += f"{getFightProp(name=substat.name)['emoji']} {substat.name} {substat.value}{'%' if substat.type == DigitType.PERCENT else ''}\n"
            embed.add_field(
                name='武器',
                value=f'{getWeapon(weapon.id)["emoji"]} {weapon.detail.name} | Lvl. {weapon.level}\n'
                f"{getFightProp(name=weapon.detail.mainstats.name)['emoji']} {weapon.detail.mainstats.name} {weapon.detail.mainstats.value}{'%' if weapon.detail.mainstats.type == DigitType.PERCENT else ''}\n"
                f'{weapon_sub_stats}',
                inline=False
            )
            embed.set_thumbnail(url=character.image.icon)
            embed.set_author(name=member.display_name, icon_url=member.avatar)
            embeds[str(character.id)] = embed

            # artifacts
            artifact_embed = defaultEmbed(f'{character.name} | 聖遺物')
            index = 0
            for artifact in filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments):
                artifact_sub_stats = ''
                artifact_sub_stat_dict = {}
                for substat in artifact.detail.substats:
                    artifact_sub_stat_dict[substat.prop_id] = substat.value
                    artifact_sub_stats += f'{getFightProp(name=substat.name)["emoji"]} {substat.name} {substat.value}{"%" if substat.type == DigitType.PERCENT else ""}\n'
                if artifact.level == 20:
                    artifact_sub_stats += f'<:SCORE:983948729293897779> {int(calculateArtifactScore(artifact_sub_stat_dict))}'
                artifact_embed.add_field(
                    name=f'{list(equip_types.values())[index]}{artifact.detail.name} +{artifact.level}',
                    value=artifact_sub_stats
                )
                artifact_embed.set_thumbnail(url=character.image.icon)
                artifact_embed.set_author(
                    name=member.display_name, icon_url=member.avatar)
                artifact_embed.set_footer(text='聖遺物滿分99, 只有+20才會評分')
                index += 1
            artifact_embeds[str(character.id)] = artifact_embed

        view = GenshinCog.EnkaPageView(embeds, artifact_embeds, options, data, self.bot.browser, eng_data, i.user)
        await i.followup.send(embed=embeds['0'], view=view)

    @app_commands.command(name='redeem兌換', description='兌換禮物碼')
    @app_commands.rename(code='兌換碼')
    async def redeem(self, i: Interaction, code: str):
        result = await self.genshin_app.redeemCode(i.user.id, code)
        result.set_author(name=i.user, url=i.user.avatar)
        await i.response.send_message(embed=result)

    def parse_event_description(description: str):
        description = description.replace('\\n', '\n')
        # replace tags with style attributes
        description = description.replace('</p>', '\n')
        description = description.replace('<strong>', '**')
        description = description.replace('</strong>', '**')

        # remove all HTML tags
        CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        description = re.sub(CLEANR, '', description)
        return description

    @app_commands.command(name='events活動', description='查看原神近期的活動')
    async def events(self, i: Interaction):
        async with self.bot.session.get(f'https://api.ambr.top/assets/data/event.json') as r:
            events = await r.json()
        embeds = []
        for event_id, event in events.items():
            value = GenshinCog.parse_event_description(
                event['description']['CHT'])
            embed = defaultEmbed(
                event['name']['CHT'], event['nameFull']['CHT'])
            if len(value) < 1024:
                embed.add_field(
                    name='<:placeholder:982425507503165470>', value=value)
            else:
                while len(value) > 1024:
                    new_value = value[:1024]
                    value = value[1024:]
                    embed.add_field(
                        name='<:placeholder:982425507503165470>', value=new_value)
            embed.set_image(url=event['banner']['CHT'])
            embeds.append(embed)
        await GeneralPaginator(i, embeds).start(embeded=True)

    class ArtifactSubStatView(DefaultView):
        def __init__(self, author: Member):
            super().__init__(timeout=None)
            self.author = author
            self.sub_stat = None
            for prop_id, prop_info in fight_prop.items():
                if prop_info['substat']:
                    self.add_item(GenshinCog.ArtifactSubStatButton(
                        prop_id, prop_info['name']))

        async def interaction_check(self, interaction: Interaction) -> bool:
            if interaction.user.id != self.author.id:
                await interaction.response.send_message(embed=errEmbed(message='輸入 `/leaderbaord` 來查看排行榜').set_author(name='這不是你的操作視窗', icon_url=interaction.user.avatar), ephemeral=True)
            return interaction.user.id == self.author.id

    class ArtifactSubStatButton(Button):
        def __init__(self, prop_id: str, prop_name: str):
            super().__init__(label=prop_name, emoji=getStatEmoji(prop_id))
            self.prop_id = prop_id

        async def callback(self, interaction: Interaction) -> Any:
            await interaction.response.defer()
            self.view.sub_stat = self.prop_id
            self.view.stop()

    class LeaderboardArtifactGoBack(Button):
        def __init__(self, c: aiosqlite.Cursor):
            super().__init__(label='返回副詞條選擇', row=2, style=ButtonStyle.green)
            self.c = c

        async def callback(self, i: Interaction):
            view = GenshinCog.ArtifactSubStatView(i.user)
            await i.response.edit_message(embed=defaultEmbed().set_author(name='選擇想要查看的副詞條排行榜', icon_url=i.user.avatar), view=view)
            await view.wait()
            await self.c.execute('SELECT * FROM substat_leaderboard WHERE sub_stat = ?', (fight_prop.get(view.sub_stat)["name"],))
            leaderboard = await self.c.fetchall()
            leaderboard.sort(key=lambda index: index[5], reverse=True)
            user_rank = GenshinCog.rank_user(i.user.id, leaderboard)
            leaderboard = divide_chunks(leaderboard, 10)
            rank = 1
            embeds = []
            for small_leaderboard in leaderboard:
                message = ''
                for index, tuple in enumerate(small_leaderboard):
                    user_id = tuple[0]
                    avatar_id = tuple[1]
                    artifact_name = tuple[2]
                    equip_type = tuple[3]
                    sub_stat_value = tuple[5]
                    message += f'{rank}. {getCharacter(avatar_id)["emoji"]} {getArtifact(name=artifact_name)["emoji"]} {equip_types.get(equip_type)} {(i.guild.get_member(user_id)).display_name} • {sub_stat_value}\n\n'
                    rank += 1
                embed = defaultEmbed(
                    f'🏆 副詞條排行榜 - {fight_prop.get(view.sub_stat)["name"]} (你: #{user_rank})', message)
                embeds.append(embed)
            await GeneralPaginator(i, embeds, [GenshinCog.LeaderboardArtifactGoBack(self.c)]).start(embeded=True, edit_original_message=True)

    def rank_user(user_id: int, leaderboard: List[Tuple]):
        interaction_user_rank = None
        rank = 1
        for index, tuple in enumerate(leaderboard):
            if tuple[0] == user_id:
                interaction_user_rank = rank
                break
            rank += 1
        return interaction_user_rank

    @app_commands.command(name='leaderboard排行榜', description='查看排行榜')
    @app_commands.rename(type='分類')
    @app_commands.describe(type='選擇要查看的排行榜分類')
    @app_commands.choices(type=[Choice(name='成就榜', value=0), Choice(name='聖遺物副詞條榜', value=1), Choice(name='色色榜', value=2), Choice(name='歐氣榜', value=3)])
    async def leaderboard(self, i: Interaction, type: int):
        await i.response.defer()
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (i.user.id,))
        uid = await c.fetchone()
        if uid is None:
            return await i.response.send_message(embed=errEmbed().set_author(name='你還沒有註冊過 UID', icon_url=i.user.avatar))
        enka_client: EnkaNetworkAPI = self.bot.enka_client
        enka_client.lang = 'cht'
        try:
            data: EnkaNetworkResponse = await enka_client.fetch_user(uid[0])
        except:
            pass
        else:
            achievement = data.player.achievement
            await c.execute('INSERT INTO leaderboard (user_id, achievements) VALUES (?, ?) ON CONFLICT (user_id) DO UPDATE SET user_id = ?, achievements = ?', (i.user.id, achievement, i.user.id, achievement))
            if data.characters is not None:
                for character in data.characters:
                    for artifact in filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments):
                        for substat in artifact.detail.substats:
                            await c.execute('SELECT sub_stat_value FROM substat_leaderboard WHERE sub_stat = ? AND user_id = ?', (substat.prop_id, i.user.id))
                            sub_stat_value = await c.fetchone()
                            if sub_stat_value is None or float(str(sub_stat_value[0]).replace('%', '')) < substat.value:
                                await c.execute('INSERT INTO substat_leaderboard (user_id, avatar_id, artifact_name, equip_type, sub_stat, sub_stat_value) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (user_id, sub_stat) DO UPDATE SET user_id = ?, avatar_id = ?, artifact_name = ?, equip_type = ?, sub_stat_value = ?', (i.user.id, character.id, artifact.detail.name, artifact.detail.artifact_type, substat.prop_id, f"{substat.value}{'%' if substat.type == DigitType.PERCENT else ''}", i.user.id, character.id, artifact.detail.name, artifact.detail.artifact_type, f"{substat.value}{'%' if substat.type == DigitType.PERCENT else ''}"))
        await self.bot.db.commit()

        # clean up leaderboard
        leaderboards = ['leaderboard',
                        'substat_leaderboard', 'sese_leaderboard']
        for leaderboard in leaderboards:
            await c.execute(f'SELECT user_id FROM {leaderboard}')
            result = await c.fetchall()
            for index, tuple in enumerate(result):
                user_id = tuple[0]
                user = self.bot.get_user(user_id)
                if user is None or user not in i.guild.members:
                    await c.execute(f'DELETE FROM {leaderboard} WHERE user_id = ?', (user_id,))
        await self.bot.db.commit()

        if type == 0:
            await c.execute('SELECT user_id, achievements FROM leaderboard')
            leaderboard = await c.fetchall()
            leaderboard.sort(key=lambda index: index[1], reverse=True)
            user_rank = GenshinCog.rank_user(i.user.id, leaderboard)
            leaderboard = divide_chunks(leaderboard, 10)
            embeds = []
            rank = 1
            for small_leaderboard in leaderboard:
                message = ''
                for index, tuple in enumerate(small_leaderboard):
                    message += f'{rank}. {(i.guild.get_member(tuple[0])).display_name} - {tuple[1]}\n'
                    rank += 1
                embed = defaultEmbed(
                    f'🏆 成就數排行榜 (你: #{user_rank})', message)
                embeds.append(embed)
            await GeneralPaginator(i, embeds).start(embeded=True, follow_up=True)
        elif type == 1:
            view = GenshinCog.ArtifactSubStatView(i.user)
            await i.followup.send(embed=defaultEmbed().set_author(name='選擇想要查看的副詞條排行榜', icon_url=i.user.avatar), view=view)
            await view.wait()
            await c.execute('SELECT * FROM substat_leaderboard WHERE sub_stat = ?', (fight_prop.get(view.sub_stat)["name"],))
            leaderboard = await c.fetchall()
            leaderboard.sort(key=lambda index: index[5], reverse=True)
            user_rank = GenshinCog.rank_user(i.user.id, leaderboard)
            leaderboard = divide_chunks(leaderboard, 10)
            rank = 1
            embeds = []
            for small_leaderboard in leaderboard:
                message = ''
                for index, tuple in enumerate(small_leaderboard):
                    user_id = tuple[0]
                    avatar_id = tuple[1]
                    artifact_name = tuple[2]
                    equip_type = tuple[3]
                    sub_stat_value = tuple[5]
                    message += f'{rank}. {getCharacter(avatar_id)["emoji"]} {getArtifact(name=artifact_name)["emoji"]} {equip_types.get(equip_type)} {(i.guild.get_member(user_id)).display_name} • {sub_stat_value}\n\n'
                    rank += 1
                embed = defaultEmbed(
                    f'🏆 副詞條排行榜 - {fight_prop.get(view.sub_stat)["name"]} (你: #{user_rank})', message)
                embeds.append(embed)
            await GeneralPaginator(i, embeds, [GenshinCog.LeaderboardArtifactGoBack(c)]).start(embeded=True, edit_original_message=True)
        elif type == 2:
            embeds = []
            await c.execute('SELECT user_id, sese_count FROM sese_leaderboard')
            leaderboard = await c.fetchall()
            leaderboard.sort(key=lambda index: index[1], reverse=True)
            user_rank = GenshinCog.rank_user(i.user.id, leaderboard)
            leaderboard = divide_chunks(leaderboard, 10)
            rank = 1
            for small_leaderboard in leaderboard:
                message = ''
                for index, tuple in enumerate(small_leaderboard):
                    message += f'{rank}. {(i.guild.get_member(tuple[0])).display_name} - {tuple[1]}\n'
                    rank += 1
                embed = defaultEmbed(
                    f'🏆 色色榜 (你: #{user_rank})', message)
                embeds.append(embed)
            await GeneralPaginator(i, embeds).start(embeded=True, follow_up=True)
        elif type == 3:
            player = GGanalysislib.PityGacha()
            await c.execute('SELECT DISTINCT user_id FROM wish_history')
            result = await c.fetchall()
            data = {}
            for index, tuple in enumerate(result):
                get_num, use_pull, left_pull, up_guarantee = await WishCog.char_banner_calc(self, tuple[0], True)
                if tuple[0] in data:
                    continue
                data[tuple[0]] = 100*player.luck_evaluate(
                    get_num=get_num, use_pull=use_pull, left_pull=left_pull)
            leaderboard = list(
                sorted(data.items(), key=lambda item: item[1], reverse=True))
            user_rank = GenshinCog.rank_user(i.user.id, leaderboard)
            leaderboard = divide_chunks(leaderboard, 10)
            embeds = []
            rank = 1
            for small_leaderboard in leaderboard:
                message = ''
                for index, tuple in enumerate(small_leaderboard):
                    message += f'{rank}. {(i.guild.get_member(tuple[0])).display_name} - {round(tuple[1], 2)}%\n'
                    rank += 1
                embed = defaultEmbed(
                    f'🏆 歐氣榜 (你: #{user_rank})', message)
                embeds.append(embed)
            await GeneralPaginator(i, embeds).start(embeded=True, follow_up=True)

    class WikiElementChooseView(DefaultView):
        def __init__(self, data: dict, author: Member):
            super().__init__(timeout=None)
            self.author = author
            for index in range(0, 7):
                self.add_item(GenshinCog.WikiElementButton(data, index))
            self.avatar_id = None

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(embed=errEmbed().set_author(name='輸入 /wiki 來查看你的維基百科', icon_url=interaction.user.avatar), ephemeral=True)
            return interaction.user.id == self.author.id

    class WikiElementButton(Button):
        def __init__(self, data: dict, index: int):
            super().__init__(
                emoji=(list(elements.values()))[index], row=index//4)
            self.index = index
            self.data = data

        async def callback(self, interaction: Interaction) -> Any:
            self.view.clear_items()
            self.view.add_item(GenshinCog.WikiElementSelect(
                self.data, list(elements.keys())[self.index]))
            await interaction.response.edit_message(view=self.view)

    class WikiElementSelect(Select):
        def __init__(self, data: dict, element: str):
            options = []
            for avatar_id, avatar_info in data['data']['items'].items():
                if avatar_info['element'] == element:
                    options.append(SelectOption(label=avatar_info['name'], emoji=(
                        getCharacter(name=avatar_info['name']))['emoji'], value=avatar_id))
            super().__init__(placeholder='選擇角色', options=options)

        async def callback(self, i: Interaction):
            await i.response.defer()
            self.view.avatar_id = self.values[0]
            self.view.stop()

    class ShowMaterialsView(DefaultView):
        def __init__(self, embed: Embed, author: Member):
            super().__init__(timeout=None)
            self.author = author
            self.embed = embed

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(embed=errEmbed().set_author(name='輸入 /wiki 來查看你的維基百科', icon_url=interaction.user.avatar), ephemeral=True)
            return interaction.user.id == self.author.id

    @app_commands.command(name='wiki', description='原神百科')
    @app_commands.rename(type='分類')
    @app_commands.describe(type='選擇要查看的維基百科分類')
    @app_commands.choices(type=[Choice(name='角色', value=0)])
    async def wiki(self, i: Interaction, type: int):
        if type == 0:
            async with self.bot.session.get('https://api.ambr.top/v2/cht/avatar') as resp:
                data = await resp.json()
            view = GenshinCog.WikiElementChooseView(data, i.user)
            await i.response.send_message(view=view)
            await view.wait()
            async with self.bot.session.get(f'https://api.ambr.top/v2/cht/avatar/{view.avatar_id}') as resp:
                avatar = await resp.json()
            avatar_data = avatar["data"]
            embeds = []
            embed = defaultEmbed(
                f"{elements.get(avatar['data']['element'])} {avatar['data']['name']}")
            embed.add_field(
                name='基本資料',
                value=f'生日: {avatar_data["birthday"][0]}/{avatar_data["birthday"][1]}\n'
                f'頭銜: {avatar_data["fetter"]["title"]}\n'
                f'*{avatar_data["fetter"]["detail"]}*\n'
                f'命座: {avatar_data["fetter"]["constellation"]}\n'
                f'隸屬於: {avatar_data["native"] if "native" in avatar_data else "???"}\n'
                f'名片: {avatar_data["other"]["nameCard"]["name"] if "name" in avatar_data["other"]["nameCard"]else "???"}\n'
            )
            embed.set_image(
                url=f'https://api.ambr.top/assets/UI/namecard/{avatar_data["other"]["nameCard"]["icon"]}_P.png')
            embed.set_thumbnail(url=(getCharacter(view.avatar_id))['icon'])
            embeds.append(embed)
            embed = defaultEmbed().set_author(
                name='等級突破素材', icon_url=(getCharacter(view.avatar_id))['icon'])
            for promoteLevel in avatar_data['upgrade']['promote'][1:]:
                value = ''
                for item_id, item_count in promoteLevel['costItems'].items():
                    value += f'{(getConsumable(id=item_id))["emoji"]} x{item_count}\n'
                value += f'<:202:991561579218878515> x{promoteLevel["coinCost"]}\n'
                embed.add_field(
                    name=f'突破到 lvl.{promoteLevel["unlockMaxLevel"]}',
                    value=value,
                    inline=True
                )
            embed.set_thumbnail(url=(getCharacter(view.avatar_id))['icon'])
            embeds.append(embed)
            for talent_id, talent_info in avatar_data["talent"].items():
                max = 3
                if view.avatar_id == '10000002' or view.avatar_id == '10000041':
                    max = 4
                if int(talent_id) <= max:
                    embed = defaultEmbed().set_author(
                        name='天賦', icon_url=(getCharacter(view.avatar_id))['icon'])
                    embed.add_field(
                        name=talent_info['name'],
                        value=GenshinCog.parse_event_description(
                            talent_info["description"]),
                        inline=False
                    )
                    material_embed = defaultEmbed().set_author(
                        name='升級天賦所需素材', icon_url=(getCharacter(view.avatar_id))['icon'])
                    for level, promote_info in talent_info['promote'].items():
                        if level == '1' or int(level) > 10:
                            continue
                        value = ''
                        for item_id, item_count in promote_info['costItems'].items():
                            value += f'{(getConsumable(id=item_id))["emoji"]} x{item_count}\n'
                        value += f'<:202:991561579218878515> x{promote_info["coinCost"]}\n'
                        material_embed.add_field(
                            name=f'升到 lvl.{level}',
                            value=value,
                            inline=True
                        )
                    embed.set_thumbnail(
                        url=f'https://api.ambr.top/assets/UI/{talent_info["icon"]}.png')
                    embeds.append(embed)
                else:
                    embed = defaultEmbed().set_author(
                        name='固有天賦', icon_url=(getCharacter(view.avatar_id))['icon'])
                    embed.add_field(
                        name=talent_info['name'],
                        value=GenshinCog.parse_event_description(
                            talent_info["description"]),
                        inline=False
                    )
                    embed.set_thumbnail(
                        url=f'https://api.ambr.top/assets/UI/{talent_info["icon"]}.png')
                    embeds.append(embed)
            const_count = 1
            for const_id, const_info in avatar_data['constellation'].items():
                embed = defaultEmbed().set_author(
                    name=f'命座 {const_count}', icon_url=(getCharacter(view.avatar_id))['icon'])
                embed.add_field(
                    name=const_info['name'],
                    value=GenshinCog.parse_event_description(
                        const_info['description'])
                )
                embed.set_thumbnail(
                    url=f'https://api.ambr.top/assets/UI/{const_info["icon"]}.png')
                embeds.append(embed)
                const_count += 1
            await GeneralPaginator(i, embeds, material_embed=material_embed).start(embeded=True, edit_original_message=True, materials=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GenshinCog(bot))
