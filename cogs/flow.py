from doctest import debug_script
from discord.ext import commands
from discord import Guild, Interaction, app_commands
from datetime import date
from discord import Member
from discord.app_commands import Choice
from typing import List, Optional
import uuid
import random
import yaml
import inflect
from utility.utils import defaultEmbed, errEmbed
import emoji
import discord


class FlowCog(commands.Cog, name='flow', description='flow系統相關'):
    def __init__(self, bot) -> None:
        self.bot = bot
        with open('data/flow.yaml', 'r', encoding="utf-8") as f:
            self.user_dict = yaml.full_load(f)
        with open('data/bank.yaml', 'r', encoding="utf-8") as f:
            self.bank_dict = yaml.full_load(f)
        with open('data/confirm.yaml', 'r', encoding="utf-8") as f:
            self.confirm_dict = yaml.full_load(f)
        with open('data/giveaways.yaml', 'r', encoding="utf-8") as f:
            self.gv_dict = yaml.full_load(f)
        with open('data/find.yaml', 'r', encoding="utf-8") as f:
            self.find_dict = yaml.full_load(f)
        with open('data/shop.yaml', 'r', encoding="utf-8") as f:
            self.shop_dict = yaml.full_load(f)
        with open('data/log.yaml', 'r', encoding="utf-8") as f:
            self.log_dict = yaml.full_load(f)

    async def register(self, interaction:discord.Interaction, discordID: int, *args):
        dcUser = self.bot.get_user(discordID)
        users = dict(self.user_dict)
        bank = dict(self.bank_dict)
        if not dcUser.bot or args==False:
            embed = defaultEmbed(
                f"找不到你的flow帳號!",
                f"{dcUser.mention}\n"
                "現在申鶴已經幫你辦了一個flow帳號\n"
                "請重新執行剛才的操作")
            today = date.today()
            users[discordID] = {'discordID': int(
                discordID), 'flow': 100, 'morning': today}
            bank['flow'] -= 100
            self.saveData(users, 'flow')
            self.saveData(bank, 'bank')
            if args != False:
                await interaction.response.send(embed=embed, ephemeral=True)
            else:
                pass
        else:
            return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        users = dict(self.user_dict)
        finds = dict(self.find_dict)
        confirms = dict(self.confirm_dict)
        bank = dict(self.bank_dict)
        giveaways = dict(self.gv_dict)

        channel = self.bot.get_channel(payload.channel_id)
        discordID = payload.user_id
        reactor = self.bot.get_user(payload.user_id)
        if channel is not None:
            message = channel.get_partial_message(payload.message_id)

        if discordID not in users:
            user = self.bot.get_user(payload.user_id)
            await self.register(channel, discordID, False)

        if payload.message_id == 965143582178705459 and payload.emoji.name == "Serialook":
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = discord.utils.get(guild.roles, name=f"委託通知")
            await member.add_roles(role)

        elif payload.message_id == 963972447600771092:
            for i in range(1, 9):
                p = inflect.engine()
                word = p.number_to_words(i)
                emojiStr = emoji.emojize(f":{word}:", language='alias')
                if payload.emoji.name == str(emojiStr):
                    guild = self.bot.get_guild(payload.guild_id)
                    member = guild.get_member(payload.user_id)
                    role = discord.utils.get(guild.roles, name=f"W{i}")
                    await member.add_roles(role)
                    break

        elif payload.emoji.name == "🎉" and payload.user_id != self.bot.user.id and payload.message_id in giveaways:
            lulurR = self.bot.get_user(665092644883398671)
            if users[discordID]['flow'] < giveaways[payload.message_id]['ticket']:
                await channel.send(f"{reactor.mention} 你的flow幣數量不足以參加這項抽獎", delete_after=5)
                return
            users[discordID]['flow'] -= giveaways[payload.message_id]['ticket']
            bank['flow'] += giveaways[payload.message_id]['ticket']
            giveaways[payload.message_id]['current'] += giveaways[payload.message_id]['ticket']
            giveaways[payload.message_id]['members'].append(
                payload.user_id)
            self.saveData(users, 'flow')
            self.saveData(bank, 'bank')
            self.saveData(giveaways, 'giveaways')
            giveawayMsg = await channel.fetch_message(payload.message_id)
            newEmbed = defaultEmbed(":tada: 抽獎啦!!!",
                                    f"獎品: {giveaways[payload.message_id]['prize']}\n目前flow幣: {giveaways[payload.message_id]['current']}/{giveaways[payload.message_id]['goal']}\n參加抽獎要付的flow幣: {giveaways[payload.message_id]['ticket']}\n\n註: 按🎉來支付flow幣並參加抽獎\n抽獎將會在目標達到後開始")
            await giveawayMsg.edit(embed=newEmbed)
            await channel.send(f"{reactor.mention} 花了 {giveaways[payload.message_id]['ticket']} flow幣參加 {giveaways[payload.message_id]['prize']} 抽獎", delete_after=5)
            if giveaways[payload.message_id]['current'] == giveaways[payload.message_id]['goal']:
                memberList = giveaways[payload.message_id]['members']
                winner = random.choice(memberList)
                winnerID = int(winner)
                winnerUser = self.bot.get_user(winnerID)
                await giveawayMsg.delete()
                embed = defaultEmbed(
                    "抽獎結果", f"恭喜{winnerUser.mention}獲得價值 {giveaways[payload.message_id]['goal']} flow幣的 {giveaways[payload.message_id]['prize']} !")
                await channel.send(f"{lulurR.mention} {winnerUser.mention}")
                await channel.send(embed=embed)
                del giveaways[payload.message_id]
                self.saveData(giveaways,'giveaways')

    @commands.Cog.listener()
    async def on_message(self, message):
        users = dict(self.user_dict)
        bank = dict(self.bank_dict)
        discordID = message.author.id
        channel = self.bot.get_channel(message.channel.id)
        
        if message.author == self.bot.user:
            return
        if "早安" in message.content:
            if discordID not in users:
                user = self.bot.get_user(message.author.id)
                await self.register(channel, discordID, False)
            today = date.today()
            if discordID in users:
                if users[discordID]['morning'] != today:
                    users[discordID]['flow'] += 1
                    users[discordID]['morning'] = today
                    bank['flow'] -= 1
                    self.saveData(users,'flow')
                    self.saveData(bank,'bank')
                    await message.add_reaction(f"☀️")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        users = dict(self.user_dict)
        bank = dict(self.bank_dict)
        giveaways = dict(self.gv_dict)
        
        channel = self.bot.get_channel(payload.channel_id)
        discordID = payload.user_id
        reactor = self.bot.get_user(payload.user_id)
        if payload.message_id == 965143582178705459 and payload.emoji.name == "Serialook":
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = discord.utils.get(guild.roles, name=f"委託通知")
            await member.remove_roles(role)
        elif payload.message_id == 963972447600771092:
            for i in range(1, 9):
                p = inflect.engine()
                word = p.number_to_words(i)
                emojiStr = emoji.emojize(f":{word}:", language='alias')
                if payload.emoji.name == str(emojiStr):
                    guild = self.bot.get_guild(payload.guild_id)
                    member = guild.get_member(payload.user_id)
                    role = discord.utils.get(guild.roles, name=f"W{i}")
                    await member.remove_roles(role)
                    break

        elif payload.emoji.name == "🎉" and payload.user_id != self.bot.user.id and payload.message_id in giveaways:
            users[discordID]['flow'] += giveaways[payload.message_id]['ticket']
            bank['flow'] -= giveaways[payload.message_id]['ticket']
            giveaways[payload.message_id]['current'] -= giveaways[payload.message_id]['ticket']
            giveaways[payload.message_id]['members'].remove(discordID)
            self.saveData(users, 'flow')
            self.saveData(bank, 'bank')
            self.saveData(giveaways, 'giveaways')
            giveawayMsg = await channel.fetch_message(payload.message_id)
            newEmbed = defaultEmbed(":tada: 抽獎啦!!!",
                                    f"獎品: {giveaways[payload.message_id]['prize']}\n目前flow幣: {giveaways[payload.message_id]['current']}/{giveaways[payload.message_id]['goal']}\n參加抽獎要付的flow幣: {giveaways[payload.message_id]['ticket']}\n\n註: 按🎉來支付flow幣並參加抽獎\n抽獎將會在目標達到後開始")
            await giveawayMsg.edit(embed=newEmbed)
            await channel.send(f"{reactor.mention} 收回了 {giveaways[payload.message_id]['ticket']} flow幣來取消參加 {giveaways[payload.message_id]['prize']} 抽獎", delete_after=5)

    @app_commands.command(name='forceroll', description='強制抽出得獎者')
    @app_commands.rename(msgID='訊息')
    @app_commands.checks.has_role('小雪團隊')
    async def forceroll(self, interaction: discord.Interaction ,msgID:int):
        giveaways = dict(self.gv_dict)
        giveawayMsg = self.bot.fetch_message(msgID)
        giveawayChannel = self.bot.get_channel(965517075508498452)
        lulurR = self.bot.get_user(665092644883398671)
        if msgID in giveaways:
            memberList = giveaways[msgID]['members']
            winner = random.choice(memberList)
            winnerID = int(winner)
            winnerUser = self.bot.get_user(winnerID)
            await giveawayMsg.delete()
            embed = defaultEmbed(
                "抽獎結果", f"恭喜{winnerUser.mention}獲得價值 {giveaways[msgID]['goal']} flow幣的 {giveaways[msgID]['prize']} !")
            await giveawayChannel.send(f"{lulurR.mention} {winnerUser.mention}")
            await giveawayChannel.send(embed=embed)
            del giveaways[msgID]
            self.saveData(giveaways,'giveaways')
            await interaction.response.send_message(f'{msgID} 強制抽獎成功',ephemeral=True)

    @app_commands.command(name='acc', description='查看flow帳號')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def acc(self, interaction: discord.Interaction,
        member: Optional[Member] = None
    ):
        users = dict(self.user_dict)
        member = member or interaction.user
        discordID = member.id
        if discordID in users:
            embed = defaultEmbed(
                f"使用者: {member}", f"flow幣: {users[discordID]['flow']}")
            await interaction.response.send_message(embed=embed)
        else:
            user = self.bot.get_user(discordID)
            await self.register(interaction, discordID)

    @app_commands.command(name='give', description='給其他人flow幣')
    @app_commands.rename(member='某人', flow='要給予的flow幣數量')
    async def give(self, interaction: discord.Interaction, member: Member, flow: int):
        users = dict(self.user_dict)
        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=errEmbed(
                    '不可以自己給自己flow幣',
                    '<:PaimonSeria:958341967698337854> 還想學土司跟ceye洗錢啊!'
                )
            )
            return
        if flow < 0:
            await interaction.response.send_message(
                embed=errEmbed(
                    '不可以給負數flow幣',
                    '<:PaimonSeria:958341967698337854> 還想學土司跟ceye洗錢啊!'
                )
            )
            return

        giverID = int(interaction.user.id)
        acceptorID = int(member.id)
        if giverID in users:
            if users[giverID]['flow'] < int(flow):
                embed = defaultEmbed(
                    "❌ 交易失敗",
                    "你的flow幣數量不足已承擔這筆交易"
                )
                await interaction.response.send_message(embed=embed)
                return
            else:
                users[giverID]['flow'] -= int(flow)
                self.saveData(users,'flow')
        if acceptorID in users:
            embed = defaultEmbed(
                "✅ 交易成功",
                f"{self.bot.get_user(giverID).mention}: **-{flow}**\n"
                f"{self.bot.get_user(acceptorID).mention}: **+{flow}**")
            await interaction.response.send_message(embed=embed)
            users[acceptorID]['flow'] += int(flow)
            self.saveData(users,'flow')
        else:
            user = self.bot.get_user(giverID)
            await self.register(interaction, giverID)

    @app_commands.command(name='take', description='將某人的flow幣轉回銀行')
    @app_commands.rename(member='某人', flow='要拿取的flow幣數量')
    @app_commands.checks.has_role('小雪團隊')
    async def take(self, interaction: discord.Interaction, member: Member, flow: int):
        bank = dict(self.bank_dict)
        users = dict(self.user_dict)
        if member.id in users:
            users[member.id]['flow'] -= int(flow)
            bank['flow'] += int(flow)
            acceptor = self.bot.get_user(member.id)
            embed = defaultEmbed(
                "✅ 已成功施展反摩拉克斯的力量",
                f"{interaction.user.mention} 從 {acceptor.mention} 的帳戶裡拿走了 {flow} 枚flow幣"
            )
            await interaction.response.send_message(embed=embed)
            self.saveData(users,'flow')
            self.saveData(bank,'bank')

    @take.error
    async def take_error(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    @app_commands.command(name='make', description='從銀行轉出flow幣給某人')
    @app_commands.rename(member='某人', flow='要給予的flow幣數量')
    @app_commands.checks.has_role('小雪團隊')
    async def make(self, interaction: discord.Interaction, member: Member, flow: int):
        bank = dict(self.bank_dict)
        users = dict(self.user_dict)
        if member.id in users:
            users[member.id]['flow'] += int(flow)
            bank['flow'] -= int(flow)
            acceptor = self.bot.get_user(member.id)
            embed = defaultEmbed(
                "✅ 已成功施展摩拉克斯的力量",
                f"{interaction.user.mention} 從 {acceptor.mention} 的帳戶裡拿走了 {flow} 枚flow幣"
            )
            await interaction.response.send_message(embed=embed)
            self.saveData(users,'flow')
            self.saveData(bank,'bank')

    @make.error
    async def take_error(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    @app_commands.command(name='total', description='查看目前群組帳號及銀行flow幣分配情況')
    async def total(self, interaction:discord.Interaction):
        users = dict(self.user_dict)
        bank = dict(self.bank_dict)
        total = 0
        count = 0
        for user in users:
            discordID = user
            count += 1
            total += users[discordID]['flow']
        flowSum = total+bank['flow']
        await interaction.response.send_message(
            f"目前群組裡共有:\n"
            f"{count}個flow帳號\n"
            f"用戶{total}+銀行{bank['flow']}={flowSum}枚flow幣")

    @app_commands.command(name='flows', description='查看群組內所有flow帳號')
    async def flows(self, interaction:discord.Interaction):
        users = dict(self.user_dict)
        userStr = ""
        count = 1
        for user in users:
            discordID = user
            userStr += f"{count}. {users[discordID]['name']}: {users[discordID]['flow']}\n"
            count += 1
        embed = defaultEmbed("所有flow帳戶", userStr)
        await interaction.response.send_message(embed=embed)

    shop = app_commands.Group(name="shop", description="flow商店")

    @shop.command(name='show',description='顯示商店')
    async def show(self, interaction:discord.Interaction):
        shop = dict(self.shop_dict)
        itemStr = ""
        for item in shop:
            itemID = item
            itemStr = itemStr + \
                f"• {item} - {shop[itemID]['flow']} flow ({shop[itemID]['current']}/{shop[itemID]['max']})\n||{itemID}||\n"
        embed = defaultEmbed("🛒 flow商店", itemStr)
        await interaction.response.send_message(embed=embed)

    @shop.command(name='newitem',description='新增商品')
    @app_commands.rename(item='商品名稱', flow='價格',max='最大購買次數')
    @app_commands.checks.has_role('小雪團隊')
    async def newitem(self, interaction:discord.Interaction, item: str, flow:int, max:int):
        shop = dict(self.shop_dict)
        uuid = str(uuid.uuid4())
        shop[item] = {'uuid': str(uuid), 'flow': int(
            flow), 'current': 0, 'max': int(max)}
        self.saveData(shop,'shop')
        await interaction.response.send_message(f"商品{item}新增成功")

    @newitem.error
    async def take_error(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    async def shop_autocomplete(self,
    interaction: discord.Interaction,
    current: str,) -> List[app_commands.Choice[str]]:
        shop = dict(self.shop_dict)
        return [
            app_commands.Choice(name=shop, value=shop)
            for shop in shop if current.lower() in shop.lower()
        ]

    @shop.command(name='removeitem',description='刪除商品')
    @app_commands.checks.has_role('小雪團隊')
    @app_commands.rename(item='商品')
    @app_commands.describe(item='要移除的商品')
    @app_commands.autocomplete(item=shop_autocomplete)
    async def removeitem(self, interaction:discord.Interaction, item:str):
        shop=dict(self.shop_dict)
        if item in shop:
            del shop[item]
            self.saveData(shop,'shop')
            await interaction.response.send_message("商品刪除成功")

    @removeitem.error
    async def take_error(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    @shop.command(name='buy',description='購買商品')
    @app_commands.rename(item='商品')
    @app_commands.describe(item='要購買的商品')
    @app_commands.autocomplete(item=shop_autocomplete)
    async def buy(self, interaction:discord.Interaction, item:str):
        users = dict(self.user_dict)
        bank = dict(self.bank_dict)
        shop = dict(self.shop_dict)
        logs = dict(self.log_dict)
        discordID = interaction.user.id
        if discordID in users:
            if item not in shop:
                await interaction.response.send_message(embed=errEmbed('找不到該商品!',''))
                return
            else:
                itemPrice = int(shop[item]['flow'])
                if users[discordID]['flow'] < itemPrice:
                    await interaction.response.send_message(embed=errEmbed("你的flow幣不足夠購買這項商品",""))
                    return
                if shop[item]['current'] >= shop[item]['max']:
                    await interaction.response.send_message(embed=errEmbed("這個商品已經售罄了",''))
                    return
                else:
                    shop[item]['current'] += 1
                    logID = str(uuid.uuid4())
                    logs[logID] = {'item': item,
                                'flow': itemPrice, 'buyerID': interaction.user.id}
                    self.saveData(logs,'log')
                    users[discordID]['flow'] -= itemPrice
                    bank['flow'] += itemPrice
                    self.saveData(bank,'bank')
                    self.saveData(users,'flow')
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
        else:
            discordID = interaction.user.id
            user = self.bot.get_user(discordID)
            await self.register(interaction, discordID)

    @shop.command(name='log',description='取得商品購買紀錄')
    @app_commands.checks.has_role('小雪團隊')
    async def log(self, interaction:discord.Interaction):
        await interaction.response.send_message('購買紀錄如下', ephemeral=True)
        logs=dict(self.log_dict)
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

    @log.error
    async def take_error(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)
            

    @shop.command(name='clear',description='將所有商品的購買次數歸零')
    @app_commands.checks.has_role('小雪團隊')
    @app_commands.rename(item='商品')
    @app_commands.describe(item='要清零購買次數的商品')
    @app_commands.autocomplete(item=shop_autocomplete)
    async def clear(self, interaction:discord.Interaction, item:str):
        shop=dict(self.shop_dict)
        if item in shop:
            shop[item]['current'] = 0
            self.saveData(shop,'shop')
            await interaction.response.send_message('已將所有商品的購買次數清零')

    @clear.error
    async def take_error(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    def check_in_find_channel(self,channel_id:int):
        if channel_id != 960861105503232030:
            channel = self.bot.get_channel(960861105503232030)
            return False, f"請在{channel.mention}裡使用此指令"
        else:
            return True, f'成功'

    def check_flow(self, user_id:int,flow:int):
        users = dict(self.user_dict)
        if int(flow) < 0:
            result = errEmbed("發布失敗, 請輸入大於1的flow幣", "")
            return False, result
        elif users[user_id]['flow'] < int(flow):
            result = errEmbed("發布失敗, 請勿輸入大於自己擁有數量的flow幣", "")
            return False, result
        else:
            return True, None

    async def interaction_check(self, interaction:discord.Interaction) -> bool:
        return True or False
        
    class Confirm(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.timeout = None
            with open('data/flow.yaml', 'r', encoding="utf-8") as f:
                self.user_dict = yaml.full_load(f)
            with open('data/find.yaml', 'r', encoding="utf-8") as f:
                self.find_dict = yaml.full_load(f)
            with open('data/confirm.yaml', 'r', encoding="utf-8") as f:
                self.confirm_dict = yaml.full_load(f)

        class OKconfirm(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.timeout = None
                with open('data/confirm.yaml', 'r', encoding="utf-8") as f:
                    self.confirm_dict = yaml.full_load(f)
                with open('data/flow.yaml', 'r', encoding="utf-8") as f:
                    self.user_dict = yaml.full_load(f)

            @discord.ui.button(label='OK', style=discord.ButtonStyle.blurple)
            async def ok_confirm(self, interaction:discord.Interaction, button:discord.ui.button):
                msg = interaction.message
                confirms = dict(self.confirm_dict)
                users = dict(self.user_dict)
                authorID = confirms[msg.id]['authorID']
                receiverID = confirms[msg.id]['receiverID']
                flow = confirms[msg.id]['flow']
                type = confirms[msg.id]['type']
                title = confirms[msg.id]['title']
                if type == 4:
                    if authorID in users:
                        users[authorID]['flow'] += flow
                    if receiverID in users:
                        users[receiverID]['flow'] -= flow
                else:
                    if authorID in users:
                        users[authorID]['flow'] -= flow
                    if receiverID in users:
                        users[receiverID]['flow'] += flow

                author = self.bot.get_user(authorID)
                receiver = self.bot.get_user(receiverID)
                if type == 4:
                    embed = defaultEmbed("🆗 結算成功",
                                        f"幫忙名稱: {title}\n幫助人: {author.mention} **+{flow} flow幣**\n被幫助人: {receiver.mention} **-{flow} flow幣**")
                else:
                    embed = defaultEmbed("🆗 結算成功",
                                        f"委託名稱: {title}\n委託人: {author.mention} **-{flow} flow幣**\n接收人: {receiver.mention} **+{flow} flow幣**")
                await author.send(embed=embed)
                await receiver.send(embed=embed)
                del confirms[msg.id]
                FlowCog.saveData(confirms, 'confirm')
                FlowCog.saveData(users, 'flow')

        @discord.ui.button(label='接受委託', style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            msg = interaction.message
            check = await self.interaction_check(interaction)
            if check == True:
                await interaction.response.send_message('不可以自己接自己的委託哦', ephemeral=True)
                return
            with open('data/find.yaml', 'r', encoding="utf-8") as f:
                finds = yaml.full_load(f)
            users = dict(self.user_dict)
            confirms = dict(self.confirm_dict)
            if msg.id in finds:
                self.stop()
                author = interaction.client.get_user(finds[msg.id]['authorID'])
                acceptUser = interaction.client.get_user(interaction.user.id)
                if finds[msg.id]['type'] == 1:
                    await author.send(f"[成功接受委託] {acceptUser.mention} 接受了你的 {finds[msg.id]['title']} 委託")
                    await acceptUser.send(f"[成功接受委託] 你接受了 {author.mention} 的 {finds[msg.id]['title']} 委託")
                    await interaction.response.send_message(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {finds[msg.id]['title']} 委託")
                elif finds[msg.id]['type'] == 2:
                    await author.send(f"[成功接受素材委託] {acceptUser.mention} 接受了你的 {finds[msg.id]['title']} 素材委託")
                    await author.send(f"{acceptUser.mention}的原神UID是{users[acceptUser.id]['uid']}")
                    await acceptUser.send(f"[成功接受素材委託] 你接受了 {author.mention} 的 {finds[msg.id]['title']} 素材委託")
                    await interaction.response.send_message(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {finds[msg.id]['title']} 素材委託")
                elif finds[msg.id]['type'] == 3:
                    await author.send(f"[成功接受委託] {acceptUser.mention} 接受了你的 {finds[msg.id]['title']} 委託")
                    await acceptUser.send(f"[成功接受委託] 你接受了 {author.mention} 的 {finds[msg.id]['title']} 委託")
                    await interaction.response.send_message(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {finds[msg.id]['title']} 委託")
                elif finds[msg.id]['type'] == 4:
                    await author.send(f"✅ {acceptUser.mention} 接受了你的 {finds[msg.id]['title']} 幫助")
                    await acceptUser.send(f"✅ 你接受了 {author.mention} 的 {finds[msg.id]['title']} 幫助")
                    await interaction.response.send_message(f"✅ {acceptUser.mention} 接受 {author.mention} 的 {finds[msg.id]['title']} 幫助")

                view = self.OKconfirm()

                if finds[msg.id]['type'] == 4:
                    embedDM = defaultEmbed(
                        "結算單", f"當對方完成幫忙的內容時, 請按 🆗來結算flow幣\n按下後, 你的flow幣將會 **- {finds[msg.id]['flow']}**, 對方則會 **+ {finds[msg.id]['flow']}**")
                    dm = await acceptUser.send(embed=embedDM, view=view)
                else:
                    embedDM = defaultEmbed(
                        "結算單", f"當對方完成委託的內容時, 請按 🆗來結算flow幣\n按下後, 你的flow幣將會 **- {finds[msg.id]['flow']}**, 對方則會 **+ {finds[msg.id]['flow']}**")
                    dm = await author.send(embed=embedDM, view=view)

                confirms[dm.id] = {'title': finds[msg.id]['title'], 'authorID': int(
                    finds[msg.id]['authorID']), 'receiverID': interaction.user.id, 'flow': finds[msg.id]['flow'], 'type': finds[msg.id]['type']}
                del finds[msg.id]
                FlowCog.saveData(self, finds, 'find')
                FlowCog.saveData(self, confirms, 'confirm')

    @app_commands.command(name='find', description='發布委託')
    @app_commands.rename(type='委託類型',title='幫助名稱',flow='flow幣數量')
    @app_commands.describe(title='需要什麼幫助?',flow='這個幫助值多少flow幣?')
    @app_commands.choices(type=[
        Choice(name='1類委託 其他玩家進入你的世界(例如: 陪玩, 打素材等)', value=1),
        Choice(name='2類委託 你進入其他玩家的世界(例如: 拿特產)', value=2),
        Choice(name='3類委託 其他委託(例如: 打apex, valorant)', value=3),
        Choice(name='4類委託 可以幫助別人(讓拿素材, 可幫打刀鐔等)', value=4)])
    async def find(self, interaction:discord.Interaction, type:int, title:str, flow:int):
        check, msg = self.check_in_find_channel(interaction.channel.id)
        if check == False:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        if interaction.user.id not in self.user_dict:
            await self.register(interaction, interaction.user.id)
            return
        WLroles = []
        for i in range(1, 9):
            WLroles.append(discord.utils.get(interaction.user.guild.roles, name=f"W{str(i)}"))
            i += 1
        roleForChannel = self.bot.get_channel(962311051683192842)
        roleStr = f'請至{roleForChannel.mention}選擇身份組'
        roleStr = ''
        for r in WLroles:
            if r in interaction.user.roles:
                roleStr = r.name
                break
        guild = self.bot.get_guild(916838066117824553)
        role = discord.utils.get(guild.roles, name=f"委託通知")
        check, msg = self.check_flow(interaction.user.id, flow)
        if check == False:
            await interaction.response.send_message(embed=msg)
            return
        uid = '請用`/setuid`來新增自己的uid'
        if 'uid' in self.user_dict[interaction.user.id]:
            uid = self.user_dict[interaction.user.id]['uid']
        if type==1:
            embed = defaultEmbed(
                f'請求幫助: {title}',
                f'發布者: {interaction.user.mention}\n'
                f'flow幣: {flow}\n'
                f'世界等級: >={roleStr}\n'
                f'發布者UID: {uid}'
            )
        elif type==2:
            embed = defaultEmbed(
            f'請求幫助: {title}',
            f'發布者: {interaction.user.mention}\n'
            f'flow幣: {flow}\n'
            f'世界等級: <={roleStr}\n'
            f'發布者UID: {uid}'
        )
        elif type==3:
            embed = defaultEmbed(
            f'請求幫助: {title}',
            f'發布者: {interaction.user.mention}\n'
            f'flow幣: {flow}'
        )
        elif type==4:
            embed = defaultEmbed(
            f'可以幫忙: {title}',
            f'發布者: {interaction.user.mention}\n'
            f'flow幣: {flow}\n'
            f'發布者世界等級: {roleStr}\n'
            f'發布者UID: {uid}'
        )

        view = self.Confirm()
        await interaction.response.send_message(embed=embed, view=view)
        await interaction.followup.send(content=role.mention)
        msg = await interaction.original_message()
        finds = dict(self.find_dict)
        finds[msg.id] = {'title': title, 'flow': int(flow),
            'author': str(interaction.user), 'authorID': interaction.user.id, 'type': 1}
        self.saveData(finds, 'find')
        await view.wait()
        
    @app_commands.command(name='giveaway', description='設置抽獎')
    @app_commands.checks.has_role('小雪團隊')
    @app_commands.rename(prize='獎品',goal='目標',ticket='參與金額')
    @app_commands.describe(
        prize='獎品是什麼?',
        goal='到達多少flow幣後進行抽獎?',
        ticket='參與者得花多少flow幣參與抽獎?')
    async def giveaway(self, interaction:discord.Interaction,prize:str,goal:int,ticket:int):
        giveaways = dict(self.gv_dict)
        embedGiveaway = defaultEmbed(
            ":tada: 抽獎啦!!!",
            f"獎品: {prize}\n"
            f"目前flow幣: 0/{goal}\n"
            f"參加抽獎要付的flow幣: {ticket}\n\n"
            "註: 按🎉來支付flow幣並參加抽獎\n"
            "抽獎將會在目標達到後開始")
        await interaction.response.send_message("✅ 抽獎設置完成", ephemeral=True)
        guild = self.bot.get_guild(interaction.user.guild.id)
        role = discord.utils.get(guild.roles, name=f"抽獎通知")
        channel = self.bot.get_channel(965517075508498452)
        giveawayMsg = await channel.send(embed=embedGiveaway)
        await channel.send(role.mention)
        await giveawayMsg.add_reaction('🎉')
        giveaways[giveawayMsg.id] = {
            'authorID': int(interaction.user.id),
            'prize': str(prize),
            'goal': int(goal),
            'ticket': int(ticket),
            'current': 0,
            'members': []
        }
        self.saveData(giveaways,'giveaways')

    @giveaway.error
    async def take_error(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    def saveData(self, data:dict, file_name:str):
        with open(f'data/{file_name}.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(data, f)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FlowCog(bot))
