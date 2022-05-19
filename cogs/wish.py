import os
from typing import Optional

import discord
import GGanalysislib
from discord import Interaction, Member, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord.ui import Modal
from utility.GenshinApp import genshin_app
from utility.utils import defaultEmbed, errEmbed, log, openFile, saveFile
from utility.WishPaginator import WishPaginator

import genshin


class WishCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    wish = app_commands.Group(name='wish', description='原神祈願系統相關')

    class AuthKeyModal(Modal, title='抽卡紀錄設定'):
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
            await interaction.response.defer()
            try:
                check, msg = genshin_app.checkUserData(interaction.user.id)
                if check == False:
                    await interaction.followup.send(embed=errEmbed('設置失敗', '請先使用`/cookie`來設置自己的原神cookie'), ephemeral=True)
                    return
                url = self.url.value
                print(log(True, False, 'Wish Setkey',
                      f'{interaction.user.id}(url={url})'))
                authkey = genshin.utility.extract_authkey(url)
                client, uid, check = genshin_app.getUserCookie(interaction.user.id)
                client.authkey = authkey
                await interaction.followup.send(embed=defaultEmbed('⏳ 請稍等, 處理數據中...', '過程約需30至45秒, 時長取決於祈願數量'), ephemeral=True)
                wish_data = await client.wish_history()
                file = open(
                    f'data/wish_history/{interaction.user.id}.yaml', 'w+')
                saveFile(wish_data, f'wish_history/{interaction.user.id}')
                if os.path.exists(f'data/wish_cache/{interaction.user.id}.yaml'):
                    # 刪除之前的快取檔案
                    os.remove(f'data/wish_cache/{interaction.user.id}.yaml')
                await interaction.followup.send(embed=defaultEmbed('✅ 抽卡紀錄設置成功'), ephemeral=True)
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
            await i.response.send_modal(WishCog.AuthKeyModal())

    def make_wish_cache(self, user_id: int):
        if not os.path.exists(f'data/wish_cache/{user_id}.yaml'):
            print(log(True, False, 'Wish Cache',
                  f'making wish cache for {user_id}'))
            file = open(f'data/wish_cache/{user_id}.yaml', 'w+')  # 創建快取檔案
            wish_cache = {}
            saveFile(wish_cache, f'/wish_cache/{str(user_id)}')
        user_wish_cache = openFile(f'/wish_cache/{str(user_id)}')
        wish_cache_categories = ['up_char', 'weapon', 'overview']
        for category in wish_cache_categories:
            if category not in user_wish_cache:
                user_wish_history = openFile(f'wish_history/{user_id}')
                break
        if 'up_char' not in user_wish_cache:  # 角色限定祈願快取
            print(log(True, False, 'Wish Cache',
                  f'making character wish cache for {user_id}'))
            user_wish_cache['up_char'] = {}
            required_data = ['up_num', 'up_gu', 'num_until_up', 'wish_sum']
            std_characters = ['迪盧克', '琴', '七七', '莫娜', '刻晴']
            up_num = 0
            up_gu = 0
            num_until_up = 0
            wish_sum = 0
            found = False
            found_last_five_star = False
            for wish in user_wish_history:
                if wish.banner_type == 301:
                    wish_sum += 1
                    if wish.rarity == 5 and wish.type == '角色':
                        if wish.name not in std_characters:
                            up_num += 1
                        if not found_last_five_star:
                            found_last_five_star = True
                            if wish.name not in std_characters:
                                up_gu = 0
                            else:
                                up_gu = 1
                        found = True
                    else:
                        if not found:
                            num_until_up += 1
            for data in required_data:
                user_wish_cache['up_char'][data] = eval(data)
            saveFile(user_wish_cache, f'/wish_cache/{str(user_id)}')
        if 'weapon' not in user_wish_cache:  # 限定武器快取
            user_wish_history = openFile(f'wish_history/{user_id}')
            print(log(True, False, 'Wish Cache',
                  f'making weapon wish cache for {user_id}'))
            user_wish_cache['weapon'] = {}
            required_data = ['last_five_star_weapon_name', 'pull_state']
            last_five_star_weapon_name = ''
            pull_state = 0
            for wish in user_wish_history:
                if wish.banner_type == 302:
                    if wish.rarity != 5:
                        pull_state += 1
                    else:
                        last_five_star_weapon_name = wish.name
                        break
            for data in required_data:
                user_wish_cache['weapon'][data] = eval(data)
            saveFile(user_wish_cache, f'/wish_cache/{str(user_id)}')
        if 'overview' not in user_wish_cache:
            print(log(True, False, 'Wish Cache',
                  f'making overview wish cache for {user_id}'))
            user_wish_cache['overview'] = {}
            overview_dict = user_wish_cache['overview']
            overview_dict['character_event'] = {}
            overview_dict['weapon_event'] = {}
            overview_dict['standard'] = {}
            pools = ['character_event', 'weapon_event', 'standard']
            pool_ids = [301, 302, 200]
            per_pool_data = ['total_wish', 'five_star',
                             'four_star', 'pity', 'found']
            for pool in pools:  # 設定預設值
                for pool_data in per_pool_data:
                    if pool_data != 'found':
                        overview_dict[pool][pool_data] = 0
                    else:
                        overview_dict[pool][pool_data] = False
            overview_dict['total_wish'] = len(user_wish_history)
            for wish in user_wish_history:
                for pool_id in pool_ids:
                    if wish.banner_type == pool_id:
                        is_five_star = self.evaluate_rarity(wish)
                        index = pool_ids.index(pool_id)
                        pool_name = pools[index]
                        overview_dict[pool_name]['total_wish'] += 1
                        if is_five_star:
                            overview_dict[pool_name]['five_star'] += 1
                            overview_dict[pool_name]['found'] = True
                        else:
                            overview_dict[pool_name]['four_star'] += 1
                        if not overview_dict[pool_name]['found']:  # 如果還沒找到五星
                            overview_dict[pool_name]['pity'] += 1
                        break
            saveFile(user_wish_cache, f'/wish_cache/{str(user_id)}')

    def evaluate_rarity(self, wish):
        if wish.rarity == 5:
            return True
        elif wish.rarity == 4:
            return False

    def divide_chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    # /wish history
    @wish.command(name='history', description='祈願歷史紀錄查詢')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def wish_history(self, i: Interaction, member: Optional[Member] = None):
        member = member or i.user
        print(log(False, False, 'Wish History', member.id))
        await i.response.defer()
        if not os.path.exists(f'data/wish_history/{member.id}.yaml'):
            await i.followup.send(embed=errEmbed('你還沒有設置過抽卡紀錄!', '請使用`/wish setkey`指令'), ephemeral=True)
            return
        result = []
        user_wish_history = openFile(f'wish_history/{member.id}')
        for wish in user_wish_history:
            wish_time = f'{wish.time.year}-{wish.time.month}-{wish.time.day}'
            if wish.rarity == 5 or wish.rarity == 4:
                result.append(
                    f"[{wish_time}: {wish.name} ({wish.rarity}☆ {wish.type})](http://example.com/)")
            else:
                result.append(
                    f"{wish_time}: {wish.name} ({wish.rarity}☆ {wish.type})")
        split_list = list(WishCog.divide_chunks(result, 20))
        embed_list = []
        for l in split_list:
            embed_str = ''
            for w in l:
                embed_str += f'{w}\n'
            embed_list.append(defaultEmbed('詳細祈願紀錄', embed_str))
        await WishPaginator(i, embed_list).start(embeded=True)

    @wish.command(name='luck', description='歐氣值分析')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def wish_analysis(self, i: Interaction, member: Optional[Member] = None):
        member = member or i.user
        print(log(False, False, 'Wish Luck', member.id))
        await i.response.defer()
        if not os.path.exists(f'data/wish_history/{member.id}.yaml'):
            await i.followup.send(embed=errEmbed('你還沒有設置過抽卡紀錄!', '請使用`/wish setkey`指令'), ephemeral=True)
            return
        self.make_wish_cache(member.id)
        user_wish_cache = openFile(f'/wish_cache/{member.id}')
        up_num = user_wish_cache['up_char']['up_num']
        up_gu = user_wish_cache['up_char']['up_gu']
        num_until_up = user_wish_cache['up_char']['num_until_up']
        wish_sum = user_wish_cache['up_char']['wish_sum']
        player = GGanalysislib.Up5starCharacter()
        gu_state = '有大保底' if up_gu == 1 else '沒有大保底'
        embed = defaultEmbed(
            '限定祈願分析',
            f'• 你的運氣擊敗了{str(round(100*player.luck_evaluate(get_num=up_num, use_pull=wish_sum, left_pull=num_until_up, up_guarantee=up_gu), 2))}%的玩家\n'
            f'• 共{wish_sum}抽\n'
            f'• 出了{up_num}個UP\n'
            f'• 墊了{num_until_up}抽\n'
            f'• {gu_state}')
        embed.set_author(name=member, icon_url=member.avatar)
        await i.followup.send(embed=embed)

    @wish.command(name='character', description='預測抽到角色的機率')
    @app_commands.rename(num='up角色數量', pull_num='祈願次數', member='其他人')
    @app_commands.describe(num='想要抽到幾個5星UP角色?', pull_num='預計抽幾抽? (目前原石數量/160=最大可抽數)', member='查看其他群友的資料')
    async def wish_char(self, i: Interaction, num: int, pull_num: int, member: Optional[Member] = None):
        member = member or i.user
        print(log(False, False, 'Wish Character', member.id))
        await i.response.defer()
        if not os.path.exists(f'data/wish_history/{member.id}.yaml'):
            await i.followup.send(embed=errEmbed('你還沒有設置過抽卡紀錄!', '請使用`/wish setkey`指令'), ephemeral=True)
            return
        self.make_wish_cache(member.id)
        user_wish_cache = openFile(f'/wish_cache/{member.id}')
        up_gu = user_wish_cache['up_char']['up_gu']
        num_until_up = user_wish_cache['up_char']['num_until_up']
        gu_state = '有大保底' if up_gu == 1 else '沒有大保底'
        player = GGanalysislib.Up5starCharacter()
        result = player.get_p(item_num=num, calc_pull=pull_num,
                              pull_state=num_until_up, up_guarantee=up_gu)
        embed = defaultEmbed(
            '祈願機率預測',
            f'• 想要抽出{num}個5星UP角色\n'
            f'• 預計抽{pull_num}次\n'
            f'• 墊了{num_until_up}抽\n'
            f'• {gu_state}\n'
            f'• 機率為: {str(round(100*result, 2))}%')
        embed.set_author(name=member, icon_url=member.avatar)
        await i.followup.send(embed=embed)

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
            await interaction.response.send_message('好的', ephemeral=True)
            self.stop()

        @discord.ui.button(label='常駐', style=discord.ButtonStyle.grey)
        async def is_std(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.value = False
            await interaction.response.send_message('好的', ephemeral=True)
            self.stop()

    class WantOrNot(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.value = None

        @discord.ui.button(label='想要的', style=discord.ButtonStyle.blurple)
        async def want(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.value = True
            await interaction.response.send_message('好的', ephemeral=True)
            self.stop()

        @discord.ui.button(label='不想要的', style=discord.ButtonStyle.grey)
        async def dont_want(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.value = False
            await interaction.response.send_message('好的', ephemeral=True)
            self.stop()

    @wish.command(name='weapon', description='預測抽到想要的UP武器的機率')
    @app_commands.rename(item_num='up武器數量', calc_pull='祈願次數', member='其他人')
    @app_commands.describe(item_num='想要抽到幾把自己想要的UP武器?', calc_pull='預計抽幾抽? (目前原石數量/160=最大可抽數)', member='查看其他群友的資料')
    async def wish_weapon(self, i: Interaction, item_num: int, calc_pull: int, member: Optional[Member] = None):
        member = member or i.user
        print(log(False, False, 'Wish Weapon', member.id))
        await i.response.defer()
        if not os.path.exists(f'data/wish_history/{member.id}.yaml'):
            await i.followup.send(embed=errEmbed('你還沒有設置過抽卡紀錄!', '請使用`/wish setkey`指令'), ephemeral=True)
            return
        self.make_wish_cache(member.id)
        user_wish_cache = openFile(f'/wish_cache/{member.id}')
        last_five_star_weapon_name = user_wish_cache['weapon']['last_five_star_weapon_name']
        pull_state = user_wish_cache['weapon']['pull_state']
        if last_five_star_weapon_name == '':
            await i.followup.send(embed=errEmbed('很抱歉, 你目前不能使用這項功能', '你還沒有在限定武器池抽中過五星武器'), ephemeral=True)
            return
        up_or_std_view = WishCog.UpOrStd(i.user)
        await i.followup.send(embed=defaultEmbed(
            '限定UP還是常駐?',
            f'你最後一次抽到的五星武器是:\n'
            f'**{last_five_star_weapon_name}**\n'
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
            f'• 想抽出 {item_num} 把想要的UP\n'
            f'• 預計抽 {calc_pull} 抽\n'
            f'• 已經墊了 {pull_state} 抽\n'
            f'• 抽中想要UP的機率為: {str(round(100*result, 2))}%'
        )
        embed.set_author(name=member, icon_url=member.avatar)
        await i.followup.send(embed=embed)

    @wish.command(name='overview', description='祈願紀錄總覽')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def wish_overview(self, i: Interaction, member: Optional[Member] = None):
        member = member or i.user
        print(log(False, False, 'Wish Overview', member.id))
        await i.response.defer()
        if not os.path.exists(f'data/wish_history/{member.id}.yaml'):
            await i.followup.send(embed=errEmbed('你還沒有設置過抽卡紀錄!', '請使用`/wish setkey`指令'), ephemeral=True)
            return
        self.make_wish_cache(member.id)
        user_wish_cache = openFile(f'/wish_cache/{member.id}')
        user_overview = user_wish_cache['overview']
        character_event = user_overview['character_event']
        weapon_event = user_overview['weapon_event']
        standard = user_overview['standard']
        total_wish = user_overview["total_wish"]
        embed = defaultEmbed(
            '祈願總覽',
            f'共 {total_wish} 抽\n'
            f'即 {160*int(total_wish)} 原石'
        )
        embed.add_field(
            name='角色池',
            value=f'• 共 {character_event["total_wish"]} 抽 ({160*int(character_event["total_wish"])}原石)\n'
            f'• 5☆ {character_event["five_star"]}\n'
            f'• 4☆ {character_event["four_star"]}\n'
            f'• 距離保底 {90-int(character_event["pity"])} 抽',
            inline=False
        )
        embed.add_field(
            name='武器池',
            value=f'• 共 {weapon_event["total_wish"]} 抽 ({160*int(weapon_event["total_wish"])}原石)\n'
            f'• 5☆ {weapon_event["five_star"]}\n'
            f'• 4☆ {weapon_event["four_star"]}\n'
            f'• 距離保底 {90-int(weapon_event["pity"])} 抽',
            inline=False
        )
        embed.add_field(
            name='常駐池',
            value=f'• 共 {standard["total_wish"]} 抽 ({160*int(standard["total_wish"])}原石)\n'
            f'• 5☆ {standard["five_star"]}\n'
            f'• 4☆ {standard["four_star"]}\n'
            f'• 距離保底 {90-int(standard["pity"])} 抽',
            inline=False
        )
        embed.set_author(name=member, icon_url=member.avatar)
        await i.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WishCog(bot))
