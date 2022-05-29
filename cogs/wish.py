import os
from typing import Optional

import aiosqlite
import discord
import GGanalysislib
from discord import Embed, Interaction, Member, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord.ui import Modal, View
from utility.GeneralPaginator import GeneralPaginator
from utility.GenshinApp import GenshinApp
from utility.utils import defaultEmbed, errEmbed, log

import genshin


class WishCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.genshin_app = GenshinApp(self.bot.db, self.bot)

    wish = app_commands.Group(name='wish', description='原神祈願系統相關')

    class AuthKeyModal(Modal):
        def __init__(self, db: aiosqlite.Connection, bot):
            self.genshin_app = GenshinApp(db, bot)
            self.db = db
            super().__init__(title='抽卡紀錄設定', timeout=None, custom_id='cookie_modal')
        url = discord.ui.TextInput(
            label='Auth Key URL',
            placeholder='請ctrl+v貼上複製的連結',
            style=discord.TextStyle.long,
            required=True,
            min_length=0,
            max_length=3000
        )

        async def on_submit(self, i: discord.Interaction):
            client = genshin.Client()
            await i.response.defer()
            check, msg = await self.genshin_app.checkUserData(i.user.id)
            if check == False:
                await i.followup.send(embed=errEmbed('設置失敗', '請先使用`/cookie`來設置自己的原神cookie'), ephemeral=True)
                return
            url = self.url.value
            await self.bot.log.send(log(True, False, 'Wish Setkey',
                      f'{i.user.id}(url={url})'))
            authkey = genshin.utility.extract_authkey(url)
            client, uid, check = await self.genshin_app.getUserCookie(i.user.id)
            client.authkey = authkey
            await i.followup.send(embed=defaultEmbed('⏳ 請稍等, 處理數據中...', '過程約需30至45秒, 時長取決於祈願數量'), ephemeral=True)
            c = await self.db.cursor()
            await c.execute('SELECT * FROM wish_history WHERE user_id = ?', (i.user.id,))
            result = await c.fetchone()
            if result is not None:
                await c.execute('DELETE FROM wish_history WHERE user_id = ?', (i.user.id,))
            async for wish in client.wish_history():
                wish_time = f'{wish.time.year}-{wish.time.month}-{wish.time.day}'
                await c.execute('INSERT INTO wish_history (user_id, wish_name, wish_rarity, wish_time, wish_type) VALUES (?, ?, ?, ?, ?)', (i.user.id, wish.name, wish.rarity, wish_time, wish.type))
            await self.db.commit()
            await i.followup.send(embed=defaultEmbed('✅ 抽卡紀錄設置成功'), ephemeral=True)

    class ChoosePlatform(View):
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
                '6. 在這裡提交連結, 請輸入`/wish setkey`指令'
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
                '9. 在這裡提交連結, 請輸入`/wish setkey`指令'
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
                '12. 在這裡提交連結, 請輸入`/wish setkey`指令'
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
                '4. 在這裡提交連結, 請輸入`/wish setkey`指令'
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @wish.command(name='setkey', description='設置原神祈願紀錄')
    @app_commands.rename(function='功能')
    @app_commands.describe(function='查看說明或提交連結')
    @app_commands.choices(function=[Choice(name='查看祈願紀錄的設置方式', value='help'),
                                    Choice(name='提交連結', value='submit')])
    async def set_key(self, i: Interaction, function: str):
        if function == 'help':
            view = WishCog.ChoosePlatform()
            embed = defaultEmbed(
                '選擇你目前的平台',
                '提醒: PC的設置方式是最簡便也最安全的\n'
                '其他管道只有在真的不得已的情況下再去做使用\n'
                '尤其IOS的設置方式極其複雜且可能失敗\n'
                '也可以將帳號交給有PC且自己信任的人來獲取數據')
            await i.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await i.response.send_modal(WishCog.AuthKeyModal(self.bot.db, self.bot))

    async def wish_history_exists(self, user_id: int) -> Embed:
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT * FROM wish_history WHERE user_id = ?', (user_id,))
        result = await c.fetchone()
        embed = errEmbed('你還沒有設置過祈願紀錄!', '請使用`/wish setkey`指令')
        member = self.bot.get_user(user_id)
        embed.set_author(name=member, icon_url=member.avatar)
        if result is None:
            return False, embed
        else:
            return True, None

    async def char_banner_calc(self, user_id: int):
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute("SELECT wish_name, wish_rarity, wish_type FROM wish_history WHERE user_id = ? AND (wish_banner_type = 301 OR wish_banner_type = 400)", (user_id,))
        user_wish_history = await c.fetchall()
        std_characters = ['迪盧克', '琴', '七七', '莫娜', '刻晴']
        get_num = 0
        left_pull = 0
        use_pull = len(user_wish_history)
        found_last_five_star = False
        for index, tuple in enumerate(user_wish_history):
            wish_name = tuple[0]
            wish_rarity = tuple[1]
            if wish_rarity == 5:
                if wish_name not in std_characters:
                    get_num += 1
                if not found_last_five_star:
                    found_last_five_star = True
                    if wish_name not in std_characters:
                        up_guarantee = 0
                    else:
                        up_guarantee = 1
            else:
                if not found_last_five_star:
                    left_pull += 1
        return get_num, use_pull, left_pull, up_guarantee

    async def weapon_banner_calc(self, user_id: int):
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute("SELECT wish_name, wish_rarity FROM wish_history WHERE user_id = ? AND wish_banner_type = 302 AND wish_type = '武器'", (user_id,))
        user_wish_history = await c.fetchall()
        last_name = ''
        pull_state = 0
        for index, tuple in enumerate(user_wish_history):
            wish_name = tuple[0]
            wish_rarity = tuple[1]
            if wish_rarity != 5:
                pull_state += 1
            else:
                last_name = wish_name
                break
        return last_name, pull_state

    async def wish_overview_calc(self, user_id: int):
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        banner_ids = [100, 200, 301, 302]
        result = []
        for banner_id in banner_ids:
            if banner_id == 301:
                await c.execute('SELECT wish_rarity FROM wish_history WHERE user_id = ? AND (wish_banner_type = ? OR wish_banner_type = ?)', (user_id, banner_id, 400))
            else:
                await c.execute('SELECT wish_rarity FROM wish_history WHERE user_id = ? AND wish_banner_type = ?', (user_id, banner_id))
            total = await c.fetchall()
            total_wish = len(total)
            left_pull = 0
            for index, tuple in enumerate(total):
                wish_rarity = tuple[0]
                if wish_rarity != 5:
                    left_pull += 1
                else:
                    break
            await c.execute('SELECT * FROM wish_history WHERE user_id = ? AND wish_banner_type = ? AND wish_rarity = 5', (user_id, banner_id))
            five_star = await c.fetchall()
            five_star = len(five_star)
            await c.execute('SELECT * FROM wish_history WHERE user_id = ? AND wish_banner_type = ? AND wish_rarity = 4', (user_id, banner_id))
            four_star = await c.fetchall()
            four_star = len(four_star)
            result.append([total_wish, left_pull, five_star, four_star])
        return result

    def divide_chunks(l, n):  # 分割祈願紀錄的helper function
        for i in range(0, len(l), n):
            yield l[i:i + n]

    # /wish history
    @wish.command(name='history', description='祈願歷史紀錄查詢')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def wish_history(self, i: Interaction, member: Member = None):
        member = member or i.user
        await self.bot.log.send(log(False, False, 'Wish History', member.id))
        check, msg = await self.wish_history_exists(member.id)
        if not check:
            await i.response.send_message(embed=msg, ephemeral=True)
            return
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT wish_name, wish_rarity, wish_time, wish_type FROM wish_history WHERE user_id = ?', (member.id,))
        result = await c.fetchall()
        user_wishes = []
        for index, tuple in enumerate(result):
            wish_name = tuple[0]
            wish_time = tuple[2]
            wish_rarity = tuple[1]
            wish_type = tuple[3]
            if wish_rarity == 5 or wish_rarity == 4:
                user_wishes.append(
                    f"[{wish_time}: {wish_name} ({wish_rarity}☆ {wish_type})](https://github.com/seriaati/shenhe_bot)")
            else:
                user_wishes.append(
                    f"{wish_time}: {wish_name} ({wish_rarity}☆ {wish_type})")
        first_twenty_wishes = list(WishCog.divide_chunks(user_wishes, 20))
        embeds = []
        for l in first_twenty_wishes:
            embed_str = ''
            for w in l:
                embed_str += f'{w}\n'
            embeds.append(defaultEmbed('詳細祈願紀錄', embed_str))
        await GeneralPaginator(i, embeds).start(embeded=True)

    @wish.command(name='luck', description='限定祈願歐氣值分析')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def wish_analysis(self, i: Interaction, member: Member = None):
        member = member or i.user
        await self.bot.log.send(log(False, False, 'Wish Luck', member.id))
        check, msg = await self.wish_history_exists(member.id)
        if not check:
            await i.response.send_message(embed=msg, ephemeral=True)
            return
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT * FROM wish_history WHERE user_id = ? AND (wish_banner_type = 301 OR wish_banner_type = 400)', (member.id,))
        result = await c.fetchone()
        if result is None:
            await i.response.send_message(embed=errEmbed('你不能使用這個功能', '請在限定池中進行祈願\n再使用`/wish setkey`更新祈願紀錄'), ephemeral=True)
            return
        get_num, use_pull, left_pull, up_guarantee = await self.char_banner_calc(
            member.id)
        player = GGanalysislib.Up5starCharacter()
        gu_str = '有大保底' if up_guarantee == 1 else '沒有大保底'
        embed = defaultEmbed(
            '限定祈願歐氣值分析',
            f'• 你的運氣擊敗了{str(round(100*player.luck_evaluate(get_num=get_num, use_pull=use_pull, left_pull=left_pull, up_guarantee=up_guarantee), 2))}%的玩家\n'
            f'• 共**{use_pull}**抽\n'
            f'• 出了**{get_num}**個UP\n'
            f'• 墊了**{left_pull}**抽\n'
            f'• {gu_str}')
        embed.set_author(name=member, icon_url=member.avatar)
        await i.response.send_message(embed=embed)

    @wish.command(name='character', description='預測抽到角色的機率')
    @app_commands.rename(num='up角色數量', pull_num='祈願次數', member='其他人')
    @app_commands.describe(num='想要抽到幾個5星UP角色?', pull_num='預計抽幾抽? (目前原石數量/160=最大可抽數)', member='查看其他群友的資料')
    async def wish_char(self, i: Interaction, num: int, pull_num: int, member: Optional[Member] = None):
        member = member or i.user
        await self.bot.log.send(log(False, False, 'Wish Character', member.id))
        check, msg = await self.wish_history_exists(member.id)
        if not check:
            await i.response.send_message(embed=msg, ephemeral=True)
            return
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT * FROM wish_history WHERE user_id = ? AND (wish_banner_type = 301 OR wish_banner_type = 400)', (member.id,))
        result = await c.fetchone()
        if result is None:
            await i.response.send_message(embed=errEmbed('你不能使用這個功能', '請在限定池中進行祈願\n再使用`/wish setkey`更新祈願紀錄'), ephemeral=True)
            return
        get_num, use_pull, left_pull, up_guarantee = await self.char_banner_calc(
            member.id)
        gu_str = '有大保底' if up_guarantee == 1 else '沒有大保底'
        player = GGanalysislib.Up5starCharacter()
        result = player.get_p(item_num=num, calc_pull=pull_num,
                              pull_state=left_pull, up_guarantee=up_guarantee)
        embed = defaultEmbed(
            '祈願機率預測',
            f'• 想要抽出**{num}**個5星UP角色\n'
            f'• 預計抽**{pull_num}**次 (**{pull_num*160}**原石)\n'
            f'• 墊了**{left_pull}**抽\n'
            f'• {gu_str}\n'
            f'• 機率為: **{str(round(100*result, 2))}%**')
        embed.set_author(name=member, icon_url=member.avatar)
        await i.response.send_message(embed=embed)

    class UpOrStd(discord.ui.View):
        def __init__(self, author: Member):
            super().__init__(timeout=None)
            self.value = None
            self.author = author

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.author.id

        @discord.ui.button(label='UP', style=discord.ButtonStyle.blurple)
        async def is_up(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.value = True
            await interaction.response.defer()
            self.stop()

        @discord.ui.button(label='常駐', style=discord.ButtonStyle.grey)
        async def is_std(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.value = False
            await interaction.response.defer()
            self.stop()

    class WantOrNot(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.value = None

        @discord.ui.button(label='想要的', style=discord.ButtonStyle.blurple)
        async def want(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.value = True
            await interaction.response.defer()
            self.stop()

        @discord.ui.button(label='不想要的', style=discord.ButtonStyle.grey)
        async def dont_want(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.value = False
            await interaction.response.defer()
            self.stop()

    @wish.command(name='weapon', description='預測抽到想要的UP武器的機率')
    @app_commands.rename(item_num='up武器數量', calc_pull='祈願次數', member='其他人')
    @app_commands.describe(item_num='想要抽到幾把自己想要的UP武器?', calc_pull='預計抽幾抽? (目前原石數量/160=最大可抽數)', member='查看其他群友的資料')
    async def wish_weapon(self, i: Interaction, item_num: int, calc_pull: int, member: Optional[Member] = None):
        member = member or i.user
        await self.bot.log.send(log(False, False, 'Wish Weapon', member.id))
        check, msg = await self.wish_history_exists(member.id)
        if not check:
            await i.response.send_message(embed=msg, ephemeral=True)
            return
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT * FROM wish_history WHERE user_id = ? AND wish_banner_type = 302', (member.id,))
        result = await c.fetchone()
        if result is None:
            await i.response.send_message(embed=errEmbed(
                '你不能使用這個功能', '請在武器池中進行祈願\n再使用`/wish setkey`更新祈願紀錄'), ephemeral=True)
            return
        last_name, pull_state = await self.weapon_banner_calc(member.id)
        if last_name == '':
            await i.response.send_message(embed=errEmbed('你不能使用這個功能', '你還沒有在限定武器池抽中過五星武器'), ephemeral=True)
            return
        up_or_std_view = WishCog.UpOrStd(i.user)
        await i.response.send_message(embed=defaultEmbed(
            '限定UP還是常駐?',
            f'你最後一次抽到的五星武器是:\n'
            f'**{last_name}**\n'
            '請問這是一把限定UP還是常駐武器?'),
            view=up_or_std_view, ephemeral=True)
        await up_or_std_view.wait()
        if up_or_std_view.value:  # 是UP
            want_or_not_view = WishCog.WantOrNot()
            await i.followup.send(embed=defaultEmbed(
                '是想要的UP還是不想要的?', ''),
                view=want_or_not_view, ephemeral=True)
            await want_or_not_view.wait()
            if want_or_not_view.value:  # 是想要的UP
                up_guarantee = 0
            else:  # 是不想要的UP
                up_guarantee = 1
        else:  # 是常駐
            up_guarantee = 2
        player = GGanalysislib.Up5starWeaponEP()
        result = player.get_p(item_num=item_num, calc_pull=calc_pull,
                              pull_state=pull_state, up_guarantee=up_guarantee)
        embed = defaultEmbed(
            '武器機率預測',
            f'• 想抽出**{item_num}**把想要的UP\n'
            f'• 預計抽**{calc_pull}**抽\n'
            f'• 已經墊了**{pull_state}**抽\n'
            f'• 抽中想要UP的機率為: **{str(round(100*result, 2))}%**'
        )
        embed.set_author(name=member, icon_url=member.avatar)
        await i.followup.send(embed=embed)

    @wish.command(name='overview', description='祈願紀錄總覽')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def wish_overview(self, i: Interaction, member: Optional[Member] = None):
        member = member or i.user
        await self.bot.log.send(log(False, False, 'Wish Overview', member.id))
        check, msg = await self.wish_history_exists(member.id)
        if not check:
            await i.response.send_message(embed=msg, ephemeral=True)
            return
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        overview = await self.wish_overview_calc(member.id)
        total_wish = overview[0][0] + overview[1][0] + \
            overview[2][0] + overview[3][0]
        embed = defaultEmbed(
            '祈願總覽',
            f'共**{total_wish}**抽\n'
            f'即**{160*int(total_wish)}**原石'
        )
        # [100, 200, 301, 302]
        # [total, left_pull, five_star, four_star]
        embed.add_field(
            name='角色池',
            value=f'• 共**{overview[2][0]}**抽 (**{overview[2][0]*160}**原石)\n'
            f'• 5☆ **{overview[2][2]}**\n'
            f'• 4☆ **{overview[2][3]}**\n'
            f'• 距離保底**{90-overview[2][1]}**抽',
            inline=False
        )
        embed.add_field(
            name='武器池',
            value=f'• 共**{overview[3][0]}**抽 (**{160*overview[3][0]}**原石)\n'
            f'• 5☆ **{overview[3][2]}**\n'
            f'• 4☆ **{overview[3][3]}**\n'
            f'• 距離保底**{90-overview[3][1]}**抽',
            inline=False
        )
        embed.add_field(
            name='常駐池',
            value=f'• 共**{overview[1][0]}**抽 (**{160*overview[1][0]}**原石)\n'
            f'• 5☆ **{overview[1][2]}**\n'
            f'• 4☆ **{overview[1][3]}**\n'
            f'• 距離保底**{90-overview[1][1]}**抽',
            inline=False
        )
        embed.add_field(
            name='新手池',
            value=f'• 共**{overview[0][0]}**抽 (**{160*overview[0][0]}**原石)\n'
            f'• 5☆ **{overview[0][2]}**\n'
            f'• 4☆ **{overview[0][3]}**\n'
            f'• 距離保底**{20-overview[0][1]}**抽',
            inline=False
        )
        embed.set_author(name=member, icon_url=member.avatar)
        await i.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WishCog(bot))
