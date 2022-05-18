import uuid
from datetime import datetime
from typing import List, Optional

import discord
from discord import Guild, Interaction, Member, Role, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from utility.FlowApp import flow_app
from utility.utils import defaultEmbed, errEmbed, log, openFile, saveFile
from utility.WishPaginator import WishPaginator


class FlowCog(commands.Cog, name='flow', description='flow系統相關'):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        users = openFile('flow')
        discordID = message.author.id
        user = self.bot.get_user(message.author.id)
        if message.author.bot:
            return

        if "早" in message.content or "午" in message.content or "晚" in message.content:
            if '早午晚' in message.content:
                await message.add_reaction('<:PaimonSeria:958341967698337854>')
                return
            check, msg = flow_app.checkFlowAccount(discordID)
            if check == False:
                try:
                    await user.send(embed=msg)
                except:
                    pass
                return
            users = openFile('flow')
            now = datetime.now()
            default_time = datetime(
                year=now.year, month=now.month, day=now.day-1,
                hour=now.hour, minute=now.minute, second=now.second,
                microsecond=now.microsecond)
            time_keys = ['morning','noon','night']
            for time_key in time_keys:
                if time_key not in users[discordID]:
                    users[discordID][time_key] = default_time
                    saveFile(users, 'flow')

            if "早" in message.content:
                start = datetime(year=now.year, month=now.month,
                                 day=now.day, hour=5, minute=0, second=0, microsecond=0)
                end = datetime(year=now.year, month=now.month, day=now.day,
                               hour=11, minute=59, second=0, microsecond=0)
                if start <= now <= end:
                    if users[discordID]['morning'].day != now.day:
                        flow_app.transaction(
                            discordID, 1, time_state='morning')
                        await message.add_reaction('⛅')
            elif "午" in message.content:
                start = datetime(year=now.year, month=now.month, day=now.day,
                                 hour=12, minute=0, second=0, microsecond=0)
                end = datetime(year=now.year, month=now.month, day=now.day,
                               hour=17, minute=59, second=0, microsecond=0)
                if start <= now <= end:
                    if users[discordID]['noon'].day != now.day:
                        flow_app.transaction(discordID, 1, time_state='noon')
                        await message.add_reaction('☀️')
            elif "晚" in message.content:
                start = datetime(year=now.year, month=now.month, day=now.day,
                                 hour=18, minute=0, second=0, microsecond=0)
                end = datetime(year=now.year, month=now.month, day=now.day +
                               1, hour=4, minute=59, second=0, microsecond=0)
                if start <= now <= end:
                    if users[discordID]['night'].day != now.day:
                        flow_app.transaction(discordID, 1, time_state='night')
                        await message.add_reaction('🌙')

    @commands.Cog.listener()
    async def on_member_remove(self, member:Member):
        users = openFile('flow')
        if member.id in users:
            flow_app.transaction(member.id, users[member.id]['flow'], is_removing_account=True)

    @app_commands.command(name='acc', description='查看flow帳號')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def acc(self, interaction: discord.Interaction,
                  member: Optional[Member] = None
                  ):
        print(log(False, False, 'Acc', interaction.user.id))
        if interaction.channel.id == 960861105503232030:
            await interaction.response.send_message(embed=defaultEmbed('請不要在這裡使用/acc唷', ''), ephemeral=True)
            return
        users = openFile('flow')
        member = member or interaction.user
        discordID = member.id
        now = datetime.now()
        check, msg = flow_app.checkFlowAccount(discordID)
        if check == False:
            await interaction.response.send_message(embed=msg, ephemeral=True)
            return
        if 'morning' not in users[discordID]:
            users[discordID]['morning'] = datetime(year=now.year, month=now.month, day=now.day-1,
                                                   hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)
            saveFile(users, 'flow')
        if 'noon' not in users[discordID]:
            users[discordID]['noon'] = datetime(year=now.year, month=now.month, day=now.day-1,
                                                hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)
            saveFile(users, 'flow')
        if 'night' not in users[discordID]:
            users[discordID]['night'] = datetime(year=now.year, month=now.month, day=now.day-1,
                                                 hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)
            saveFile(users, 'flow')
        embed = defaultEmbed(
            f"flow帳號",
            f"flow幣: {users[discordID]['flow']}\n"
            f"早安幣: {users[discordID]['morning']}\n"
            f"午安幣: {users[discordID]['noon']}\n"
            f"晚安幣: {users[discordID]['night']}")
        embed.set_author(name=member, icon_url=member.avatar)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='give', description='給其他人flow幣')
    @app_commands.rename(member='某人', flow='要給予的flow幣數量')
    async def give(self, interaction: discord.Interaction, member: Member, flow: int):
        print(log(False, False, 'Give',
              f'{interaction.user.id} give {flow} to {member.id}'))
        users = openFile('flow')
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=errEmbed(
                    '不可以自己給自己flow幣',
                    '<:PaimonSeria:958341967698337854> 還想學土司跟ceye洗錢啊!'),
                ephemeral=True)
            return
        if flow < 0:
            await interaction.response.send_message(
                embed=errEmbed(
                    '不可以給負數flow幣',
                    '<:PaimonSeria:958341967698337854> 還想學土司跟ceye洗錢啊!'),
                ephemeral=True)
            return

        giverID = int(interaction.user.id)
        acceptorID = int(member.id)
        if acceptorID not in users:
            embed = errEmbed('你沒有flow帳號!', '請重新執行交易動作')
            await interaction.response.send_message(embed=embed, ephemeral=True)
            flow_app.register(acceptorID)
            return
        if giverID not in users:
            embed = errEmbed('對方沒有flow帳號!', '請重新執行交易動作')
            await interaction.response.send_message(embed=embed, ephemeral=True)
            flow_app.register(giverID)
            return

        if users[giverID]['flow'] < int(flow):
            embed = errEmbed(
                "❌ 交易失敗",
                "你的flow幣數量不足已承擔這筆交易")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        try:
            users[giverID]['flow'] -= int(flow)
            users[acceptorID]['flow'] += int(flow)
            saveFile(users, 'flow')
            embed = defaultEmbed(
                "✅ 交易成功",
                f"{self.bot.get_user(giverID).mention} **-{flow}**\n"
                f"{self.bot.get_user(acceptorID).mention} **+{flow}**")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(log(True, True, 'Give', e))
            embed = errEmbed('發生未知錯誤', f'```{e}```')
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='take', description='將某人的flow幣轉回銀行')
    @app_commands.rename(member='某人', flow='要拿取的flow幣數量', private='私人訊息')
    @app_commands.choices(private=[
        Choice(name='是', value=0),
        Choice(name='否', value=1)])
    @app_commands.checks.has_role('小雪團隊')
    async def take(self, interaction: discord.Interaction, member: Member, flow: int, private: int):
        print(log(False, False, 'Take',
              f'{interaction.user.id} take {flow} from {member.id}'))
        check, msg = flow_app.checkFlowAccount(member.id)
        if check == False:
            await interaction.response.send_message(embed=msg, ephemeral=True)
            return
        else:
            flow_app.transaction(member.id, -int(flow))
            acceptor = self.bot.get_user(member.id)
            embed = defaultEmbed(
                "✅ 已成功施展反摩拉克斯的力量",
                f"{interaction.user.mention} 從 {acceptor.mention} 的帳戶裡拿走了 {flow} 枚flow幣"
            )
            ephemeral_toggler = True if private == 0 else False
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral_toggler)

    @take.error
    async def err_handle(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    @app_commands.command(name='make', description='從銀行轉出flow幣給某人')
    @app_commands.rename(member='某人', flow='要給予的flow幣數量', private='私人訊息')
    @app_commands.choices(private=[
        Choice(name='是', value=0),
        Choice(name='否', value=1)])
    @app_commands.checks.has_role('小雪團隊')
    async def make(self, interaction: discord.Interaction, member: Member, flow: int, private: int = 1):
        print(log(False, False, 'make',
              f'{interaction.user.id} make {flow} for {member.id}'))
        check, msg = flow_app.checkFlowAccount(member.id)
        if check == False:
            await interaction.response.send_message(embed=msg, ephemeral=True)
            return
        else:
            flow_app.transaction(member.id, int(flow))
            acceptor = self.bot.get_user(member.id)
            embed = defaultEmbed(
                "✅ 已成功施展摩拉克斯的力量",
                f"{interaction.user.mention} 給了 {acceptor.mention} {flow} 枚flow幣"
            )
            ephemeral_toggler = True if private == 0 else False
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral_toggler)

    @make.error
    async def err_handle(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    @app_commands.command(name='total', description='查看目前群組帳號及銀行flow幣分配情況')
    async def total(self, interaction: discord.Interaction):
        print(log(False, False, 'Total', f'{interaction.user.id}'))
        users = openFile('flow')
        bank = openFile('bank')
        user_total = 0
        count = 0
        for user in users:
            discordID = user
            count += 1
            user_total += users[discordID]['flow']
        sum = user_total+bank['flow']
        embed = defaultEmbed(
            f'目前共{count}個flow帳號',
            f'用戶{user_total}+銀行{bank["flow"]}={sum}枚flow幣'
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='flows', description='查看群組內所有flow帳號')
    async def flows(self, interaction: discord.Interaction):
        print(log(False, False, 'flows', interaction.user.id))
        await interaction.response.defer()
        users = openFile('flow')
        userStr = ""
        sum = 0
        flow_categories = {
            '小於 100 flow': [],
            '100~200 flow': [],
            '200~300 flow': [],
            '大於 300 flow': []
        }
        for user_id, value in users.items():
            user = interaction.client.get_user(user_id)
            if user is None:
                flow_app.transaction(
                    user_id, value['flow'], is_removing_account=True)
                continue
            if value['flow'] < 100:
                flow_categories['小於 100 flow'].append(
                    f'{user.name}: {value["flow"]}')
            elif 100 <= value['flow'] <= 200:
                flow_categories['100~200 flow'].append(
                    f'{user.name}: {value["flow"]}')
            elif 200 < value['flow'] <= 300:
                flow_categories['200~300 flow'].append(
                    f'{user.name}: {value["flow"]}')
            elif value['flow'] > 300:
                flow_categories['大於 300 flow'].append(
                    f'{user.name}: {value["flow"]}')
            sum += 1
        embed_list = []
        embed = defaultEmbed(f"共 {sum} 個flow帳戶")
        embed_list.append(embed)
        for category, users in flow_categories.items():
            if len(users) == 0:
                continue
            value = ''
            for user in users:
                value += f'{user}\n'
            embed = defaultEmbed(
                f'{category} ({len(users)})',
                value
            )
            embed_list.append(embed)
        await WishPaginator(interaction, embed_list).start(embeded=True)

    shop = app_commands.Group(name="shop", description="flow商店")

    @shop.command(name='show', description='顯示商店')
    async def show(self, interaction: discord.Interaction):
        print(log(False, False, 'shop show', interaction.user.id))
        shop = openFile('shop')
        itemStr = ""
        for item, value in shop.items():
            itemStr = itemStr + \
                f"• {item} - {value['flow']} flow ({value['current']}/{value['max']})\n\n"
        embed = defaultEmbed("🛒 flow商店", itemStr)
        await interaction.response.send_message(embed=embed)

    @shop.command(name='newitem', description='新增商品')
    @app_commands.rename(item='商品名稱', flow='價格', max='最大購買次數')
    @app_commands.checks.has_role('小雪團隊')
    async def newitem(self, interaction: discord.Interaction, item: str, flow: int, max: int):
        print(log(False, False, 'shop newitem',
              f'{interaction.user.id}: (item={item}, flow={flow}, max={max})'))
        shop = openFile('shop')
        uuid = str(uuid.uuid4())
        try:
            shop[item] = {'uuid': str(uuid), 'flow': int(
                flow), 'current': 0, 'max': int(max)}
            saveFile(shop, 'shop')
            await interaction.response.send_message(f"商品{item}新增成功")
        except Exception as e:
            print(log(True, True, 'shop newitem', e))

    @newitem.error
    async def err_handle(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    async def shop_autocomplete(self, interaction: discord.Interaction, current: str,) -> List[app_commands.Choice[str]]:
        shop = openFile('shop')
        return [
            app_commands.Choice(name=shop, value=shop)
            for shop in shop if current.lower() in shop.lower()
        ]

    @shop.command(name='removeitem', description='刪除商品')
    @app_commands.checks.has_role('小雪團隊')
    @app_commands.rename(item='商品')
    @app_commands.describe(item='要移除的商品')
    @app_commands.autocomplete(item=shop_autocomplete)
    async def removeitem(self, interaction: discord.Interaction, item: str):
        print(log(False, False, 'shop removeitem',
              f'{interaction.user.id}: (item={item})'))
        shop = openFile('shop')
        if item not in shop:
            embed = errEmbed('找不到該商品!', '')
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            try:
                del shop[item]
                saveFile(shop, 'shop')
                await interaction.response.send_message("商品刪除成功")
            except Exception as e:
                print(log(True, True, 'shop removeitem', e))

    @removeitem.error
    async def err_handle(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    @shop.command(name='buy', description='購買商品')
    @app_commands.rename(item='商品')
    @app_commands.describe(item='要購買的商品')
    @app_commands.autocomplete(item=shop_autocomplete)
    async def buy(self, interaction: discord.Interaction, item: str):
        print(log(False, False, 'shop buy',
              f'{interaction.user.id}: (item={item})'))
        users = openFile('flow')
        shop = openFile('shop')
        logs = openFile('log')
        discordID = interaction.user.id
        check, msg = flow_app.checkFlowAccount(discordID)
        if check == False:
            await interaction.response.send_message(embed=msg, ephemeral=True)
            return
        if item not in shop:
            await interaction.response.send_message(embed=errEmbed('找不到該商品!', ''), ephemeral=True)
            return
        itemPrice = int(shop[item]['flow'])
        if users[discordID]['flow'] < itemPrice:
            await interaction.response.send_message(embed=errEmbed("你的flow幣不足夠購買這項商品", ""), ephemeral=True)
            return
        if shop[item]['current'] >= shop[item]['max']:
            await interaction.response.send_message(embed=errEmbed("這個商品已經售罄了", ''), ephemeral=True)
            return
        shop[item]['current'] += 1
        logID = str(uuid.uuid4())
        logs[logID] = {'item': item,
                       'flow': itemPrice, 'buyerID': interaction.user.id}
        saveFile(logs, 'log')
        flow_app.transaction(discordID, -int(itemPrice))
        await interaction.response.send_message(f"商品 {item} 購買成功, 詳情請查看私訊")
        await interaction.user.send(f"您已在flow商城購買了 {item} 商品, 請將下方的收據截圖並寄給小雪或律律來兌換商品")
        embed = defaultEmbed(
            "📜 購買證明",
            f"購買人: {interaction.user.mention}\n"
            f"購買人ID: {interaction.user.id}\n"
            f"商品: {item}\n"
            f"收據UUID: {logID}\n"
            f"價格: {shop[item]['flow']}")
        await interaction.user.send(embed=embed)

    @shop.command(name='log', description='取得商品購買紀錄')
    @app_commands.checks.has_role('小雪團隊')
    async def shop_log(self, interaction: discord.Interaction):
        print(log(False, False, 'shop log', interaction.user.id))
        await interaction.response.send_message('購買紀錄如下', ephemeral=True)
        logs = openFile('log')
        for log in logs:
            logID = log
            user = self.bot.get_user(logs[logID]['buyerID'])
            embed = defaultEmbed(
                "購買紀錄",
                f"商品: {logs[logID]['item']}\n"
                f"價格: {logs[logID]['flow']}\n"
                f"購買人: {user.mention}\n"
                f"購買人ID: {logs[logID]['buyerID']}")
            await interaction.followup.send(embed=embed, ephemeral=True)

    @shop_log.error
    async def err_handle(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    @shop.command(name='clear', description='將所有商品的購買次數歸零')
    @app_commands.checks.has_role('小雪團隊')
    @app_commands.rename(item='商品')
    @app_commands.describe(item='要清零購買次數的商品')
    @app_commands.autocomplete(item=shop_autocomplete)
    async def clear(self, interaction: discord.Interaction, item: str):
        print(log(False, False, 'shop clear', interaction.user.id))
        shop = openFile('shop')
        if item not in shop:
            await interaction.response.send_message(embed=errEmbed('找不到該商品!', ''), ephemeral=True)
        else:
            try:
                shop[item]['current'] = 0
                saveFile(shop, 'shop')
                await interaction.response.send_message('已將所有商品的購買次數清零')
            except Exception as e:
                print(log(True, True, 'shop clear', e))

    @clear.error
    async def err_handle(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    def check_in_find_channel(self, channel_id: int):
        if channel_id != 960861105503232030:
            channel = self.bot.get_channel(960861105503232030)
            return False, f"請在{channel.mention}裡使用此指令"
        else:
            return True, f'成功'

    def check_flow(self, user_id: int, flow: int):
        users = openFile('flow')
        if int(flow) < 0:
            result = errEmbed("發布失敗, 請輸入大於1的flow幣", "")
            return False, result
        elif users[user_id]['flow'] < int(flow):
            result = errEmbed("發布失敗, 請勿輸入大於自己擁有數量的flow幣", "")
            return False, result
        else:
            return True, None

    class AcceptView(discord.ui.View):
        def __init__(self, author: discord.Member):
            super().__init__(timeout=None)
            self.author = author

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id != self.author.id

        class OKconfirm(discord.ui.View):
            def __init__(self, author: discord.Member):
                super().__init__(timeout=None)
                self.author = author

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                return interaction.user.id == self.author.id

            @discord.ui.button(label='OK', style=discord.ButtonStyle.blurple)
            async def ok_confirm(self, interaction: discord.Interaction, button: discord.ui.button):
                self.stop()
                confirms = openFile('confirm')
                msg = interaction.message
                authorID = confirms[msg.id]['authorID']
                receiverID = interaction.user.id
                confirms = openFile('confirm')
                free_trial = openFile('find_free_trial')
                if authorID not in free_trial:
                    free_trial[authorID] = 0
                if receiverID not in free_trial:
                    free_trial[receiverID] = 0
                receiverID = confirms[msg.id]['receiverID']
                flow = confirms[msg.id]['flow']
                type = confirms[msg.id]['type']
                title = confirms[msg.id]['title']
                str = ''
                new_flow = flow
                author = interaction.client.get_user(authorID)
                receiver = interaction.client.get_user(receiverID)
                if type == 4:
                    if free_trial[receiverID] < 10 and flow >= 10:
                        flow_app.transaction(receiverID, 10)
                        new_flow = flow-10
                        free_trial[receiverID] += 1
                        str = f'({receiver.mention}受到10 flow幣贊助)\n'
                        f'已使用{free_trial[receiverID]}/10次贊助機會'
                    flow_app.transaction(authorID, flow)
                    flow_app.transaction(receiverID, -int(new_flow))
                    embed = defaultEmbed(
                        "🆗 結算成功",
                        f"幫忙名稱: {title}\n"
                        f"幫助人: {author.mention} **+{flow} flow幣**\n"
                        f"被幫助人: {receiver.mention} **-{new_flow} flow幣**\n{str}")
                else:
                    if free_trial[authorID] < 10 and flow >= 10:
                        flow_app.transaction(authorID, 10)
                        new_flow = flow-10
                        free_trial[authorID] += 1
                        str = f'({receiver.mention}受到10 flow幣贊助)\n'
                        f'已使用{free_trial[receiverID]}/10次贊助機會'
                    flow_app.transaction(authorID, -int(new_flow))
                    flow_app.transaction(receiverID, flow)
                    embed = defaultEmbed(
                        "🆗 結算成功",
                        f"委託名稱: {title}\n"
                        f"委託人: {author.mention} **-{new_flow} flow幣**\n"
                        f"接收人: {receiver.mention} **+{flow} flow幣**\n{str}")
                await interaction.response.send_message(embed=embed)
                g = interaction.client.get_guild(916838066117824553)
                t = g.get_thread(confirms[msg.id]['thread_id'])
                await t.edit(archived=True)
                del confirms[msg.id]
                saveFile(confirms, 'confirm')
                saveFile(free_trial, 'find_free_trial')

        @discord.ui.button(label='接受委託', style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.stop()
            button.disabled = True 
            interaction.edit_original_message(view=FlowCog.AcceptView(interaction.user))
            msg = interaction.message
            finds = openFile('find')
            confirms = openFile('confirm')
            if msg.id in finds:
                print(log(True, False, 'Accept',
                      f"(author = {finds[msg.id]['authorID']}, accepter = {interaction.user.id})"))
                author = interaction.client.get_user(finds[msg.id]['authorID'])
                acceptUser = interaction.client.get_user(interaction.user.id)
                thread = await msg.create_thread(name=f"{author.name} • {finds[msg.id]['title']}")
                await thread.add_user(author)
                await thread.add_user(acceptUser)
                if finds[msg.id]['type'] == 1:
                    await interaction.response.send_message(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {finds[msg.id]['title']} 委託")
                elif finds[msg.id]['type'] == 2:
                    await interaction.response.send_message(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {finds[msg.id]['title']} 素材委託")
                elif finds[msg.id]['type'] == 3:
                    await interaction.response.send_message(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {finds[msg.id]['title']} 委託")
                elif finds[msg.id]['type'] == 4:
                    await interaction.response.send_message(f"✅ {acceptUser.mention} 接受 {author.mention} 的 {finds[msg.id]['title']} 幫助")

                view = self.OKconfirm(author)

                if finds[msg.id]['type'] == 4:
                    embedDM = defaultEmbed(
                        f"結算單",
                        f"當{acceptUser.mention}完成幫忙的內容時, 請按OK來結算flow幣\n"
                        f"按下後, 你的flow幣將會 **- {finds[msg.id]['flow']}**\n"
                        f"對方則會 **+ {finds[msg.id]['flow']}**")
                else:
                    embedDM = defaultEmbed(
                        f"結算單",
                        f"當{acceptUser.mention}完成委託的內容時, 請按OK來結算flow幣\n"
                        f"按下後, 你的flow幣將會 **- {finds[msg.id]['flow']}**\n"
                        f"對方則會 **+ {finds[msg.id]['flow']}**")
                embedDM.set_author(name=author, icon_url=author.avatar)
                dm = await thread.send(embed=embedDM, view=view)

                confirms[dm.id] = {
                    'title': finds[msg.id]['title'],
                    'authorID': int(finds[msg.id]['authorID']),
                    'receiverID': interaction.user.id,
                    'flow': finds[msg.id]['flow'],
                    'type': finds[msg.id]['type'],
                    'thread_id': thread.id}
                del finds[msg.id]
                saveFile(finds, 'find')
                saveFile(confirms, 'confirm')

    @app_commands.command(name='find', description='發布委託')
    @app_commands.rename(type='委託類型', title='幫助名稱', flow='flow幣數量', tag='tag人開關')
    @app_commands.describe(title='需要什麼幫助?', flow='這個幫助值多少flow幣?', tag='是否要tag委託通知?')
    @app_commands.choices(type=[
        Choice(name='1類委託 其他玩家進入你的世界(例如: 陪玩, 打素材等)', value=1),
        Choice(name='2類委託 你進入其他玩家的世界(例如: 拿特產)', value=2),
        Choice(name='3類委託 其他委託(例如: 打apex, valorant)', value=3),
        Choice(name='4類委託 可以幫助別人(讓拿素材, 可幫打刀鐔等)', value=4)],
        tag=[Choice(name='不tag', value=0),
             Choice(name='tag', value=1)])
    async def find(self, interaction: discord.Interaction, type: int, title: str, flow: int, tag: int = 1):
        print(log(False, False, 'Find',
              f'{interaction.user.id}: (type={type}, title={title}, flow={flow})'))
        check, msg = self.check_in_find_channel(interaction.channel.id)
        if check == False:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        check, msg = flow_app.checkFlowAccount(interaction.user.id)
        if check == False:
            await interaction.response.send_message(embed=msg, ephemeral=True)
            return
        WLroles = []
        for i in range(1, 9):
            WLroles.append(discord.utils.get(
                interaction.user.guild.roles, name=f"W{str(i)}"))
            i += 1
        roleForChannel = self.bot.get_channel(962311051683192842)
        roleStr = f'請至{roleForChannel.mention}選擇身份組'
        for r in WLroles:
            if r in interaction.user.roles:
                roleStr = r.name
                break
        check, msg = self.check_flow(interaction.user.id, flow)
        if check == False:
            await interaction.response.send_message(embed=msg)
            return
        if type == 1:
            embed = defaultEmbed(
                f'請求幫助: {title}',
                f'發布者: {interaction.user.mention}\n'
                f'flow幣: {flow}\n'
                f'世界等級: >={roleStr}\n'
            )
        elif type == 2:
            embed = defaultEmbed(
                f'請求幫助: {title}',
                f'發布者: {interaction.user.mention}\n'
                f'flow幣: {flow}\n'
                f'世界等級: <={roleStr}\n'
            )
        elif type == 3:
            embed = defaultEmbed(
                f'請求幫助: {title}',
                f'發布者: {interaction.user.mention}\n'
                f'flow幣: {flow}'
            )
        elif type == 4:
            embed = defaultEmbed(
                f'可以幫忙: {title}',
                f'發布者: {interaction.user.mention}\n'
                f'flow幣: {flow}\n'
                f'發布者世界等級: {roleStr}\n'
            )

        acceptView = self.AcceptView(interaction.user)
        await interaction.response.send_message(embed=embed, view=acceptView)
        guild = self.bot.get_guild(916838066117824553)
        if tag == 1:
            role = guild.get_role(965141973700857876)  # 委託通知
            await interaction.channel.send(role.mention)
        msg = await interaction.original_message()
        finds = openFile('find')
        finds[msg.id] = {'title': title, 'flow': int(flow),
                         'author': str(interaction.user), 'authorID': interaction.user.id, 'type': 1}
        saveFile(finds, 'find')
        await acceptView.wait()

    @app_commands.command(name='rolemembers', description='查看一個身份組內的所有成員')
    @app_commands.rename(role='身份組')
    @app_commands.describe(role='請選擇要查看的身份組')
    async def role_members(self, i: discord.Interaction, role: Role):
        print(log(False, False, 'role members',
              f'{i.user.id}: (role: {role})'))
        if role is None:
            await i.response.send_message('找不到該身份組!', ephemeral=True)
            return
        memberStr = ''
        count = 0
        for member in role.members:
            count += 1
            memberStr += f'{count}. {member}\n'
        embed = defaultEmbed(role.name, memberStr)
        await i.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FlowCog(bot))
