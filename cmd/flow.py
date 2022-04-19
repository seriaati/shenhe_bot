from discord.ext.forms import Form, ReactionForm
from discord.ext import commands
from datetime import date
import uuid
import yaml
import inflect
from cmd.asset.global_vars import defaultEmbed, setFooter
import emoji
import discord
import re

with open(f'cmd/asset/flow.yaml', encoding='utf-8') as file:
    users = yaml.full_load(file)
with open(f'cmd/asset/find.yaml', encoding='utf-8') as file:
    finds = yaml.full_load(file)
with open(f'cmd/asset/confirm.yaml', encoding='utf-8') as file:
    confirms = yaml.full_load(file)
with open(f'cmd/asset/bank.yaml', encoding='utf-8') as file:
    bank = yaml.full_load(file)
with open(f'cmd/asset/shop.yaml', encoding='utf-8') as file:
    shop = yaml.full_load(file)
with open(f'cmd/asset/log.yaml', encoding='utf-8') as file:
    logs = yaml.full_load(file)
with open(f'cmd/asset/giveaways.yaml', encoding='utf-8') as file:
    giveaways = yaml.full_load(file)


class FlowCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def register(self, ctx, name, discordID: int):
        dcUser = self.bot.get_user(discordID)
        if not dcUser.bot:
            embed = defaultEmbed("找不到帳號!", "現在申鶴已經幫你辦了一個flow帳號\n請重新執行剛才的操作")
            setFooter(embed)
            today = date.today()
            users[discordID] = {'name': str(name), 'discordID': int(
                discordID), 'flow': 100, 'morning': today}
            bank['flow'] -= 100
            with open(f'cmd/asset/flow.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(users, file)
            with open(f'cmd/asset/bank.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(bank, file)
            await ctx.send(embed=embed, delete_after=5)
        else:
            return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id == 965143582178705459 and payload.emoji.name == "Serialook":
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = discord.utils.get(guild.roles, name=f"委託通知")
            await member.add_roles(role)

        if payload.message_id == 963972447600771092:
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

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
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

    @commands.command()
    async def acc(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        discordID = member.id
        if discordID in users:
            embed = defaultEmbed(
                f"使用者: {users[discordID]['name']}", f"flow幣: {users[discordID]['flow']}")
            setFooter(embed)
            await ctx.send(embed=embed)
        else:
            user = self.bot.get_user(discordID)
            await self.register(ctx, user, discordID)

    @commands.command()
    @commands.has_role("小雪團隊")
    async def roles(self):
        channel = self.bot.get_channel(962311051683192842)
        embed = defaultEmbed("請選擇你的世界等級", " ")
        setFooter(embed)
        message = await channel.send(embed=embed)
        for i in range(1, 9):
            p = inflect.engine()
            word = p.number_to_words(i)
            emojiStr = emoji.emojize(f":{word}:", language='alias')
            await message.add_reaction(str(emojiStr))

    @commands.command()
    @commands.has_role("小雪團隊")
    async def notif_roles(self):
        channel = self.bot.get_channel(962311051683192842)
        embed = defaultEmbed(
            "如果你想收到發布委託通知的話, 請選擇 <:Serialook:959100214747222067> 表情符號", " ")
        setFooter(embed)
        message = await channel.send(embed=embed)
        await message.add_reaction("<:Serialook:959100214747222067>")

    @commands.command()
    async def give(self, ctx, member: discord.Member, argFlow: int):
        if member.id == ctx.author.id:
            await ctx.send(f"<:PaimonSeria:958341967698337854> 還想學土司跟ceye洗錢啊!(不可以自己給自己")
            return
        if argFlow < 0:
            await ctx.send(f"<:PaimonSeria:958341967698337854> 還想學土司跟ceye洗錢啊!(不可以給負數flow幣")
            return
        giverID = int(ctx.author.id)
        acceptorID = int(member.id)

        if giverID in users:
            if users[giverID]['flow'] < int(argFlow):
                embed = defaultEmbed("❌ 交易失敗", "你的flow幣數量不足已承擔這筆交易")
                setFooter(embed)
                await ctx.send(embed=embed)
                return
            else:
                users[giverID]['flow'] -= int(argFlow)
                with open(f'cmd/asset/flow.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(users, file)
        if acceptorID in users:
            embed = defaultEmbed(
                "✅ 交易成功", f"{self.bot.get_user(giverID).mention}: **-{argFlow}**\n{self.bot.get_user(acceptorID).mention}: **+{argFlow}**")
            setFooter(embed)
            await ctx.send(embed=embed)
            users[acceptorID]['flow'] += int(argFlow)
            with open(f'cmd/asset/flow.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(users, file)
        else:
            user = self.bot.get_user(giverID)
            await self.register(ctx, user, giverID)

    @commands.command()
    @commands.has_role("小雪團隊")
    async def take(self, ctx):
        form = Form(ctx, '沒收flow幣', cleanup=True)
        form.add_question('要沒收哪些人的flow幣?(用逗號分隔: @ceye, @ttos)', 'members')
        form.add_question('多少flow幣?', 'flow')
        form.edit_and_delete(True)
        form.set_timeout(60)
        await form.set_color("0xa68bd3")
        result = await form.start()
        memberList = result.members.split(", ")
        for member in memberList:
            # serach ID inside mention
            discordID = int(re.search(r'\d+', member).group())
            if discordID in users:
                users[discordID]['flow'] -= int(result.flow)
                bank['flow'] += int(result.flow)
                acceptor = self.bot.get_user(discordID)
                embed = defaultEmbed(
                    "✅ 已成功施展反摩拉克斯的力量", f"{ctx.author.mention} 從 {acceptor.mention} 的帳戶裡拿走了 {result.flow} 枚flow幣")
                setFooter(embed)
                await ctx.send(embed=embed)
                with open(f'cmd/asset/flow.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(users, file)
                with open(f'cmd/asset/bank.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(bank, file)
                break

    @commands.command()
    @commands.has_role("小雪團隊")
    async def make(self, ctx):
        formFalse = Form(ctx, '發放flow幣', cleanup=True)
        formFalse.add_question('要給哪些人?(用逗號分隔: @小雪, @sueno)', 'members')
        formFalse.add_question('多少flow幣?', 'flow')
        formFalse.edit_and_delete(True)
        formFalse.set_timeout(60)
        await formFalse.set_color("0xa68bd3")
        result = await formFalse.start()
        memberList = result.members.split(", ")
        for member in memberList:
            # search ID in mention
            discordID = int(re.search(r'\d+', member).group())
            if discordID in users:
                users[discordID]['flow'] += int(result.flow)
                bank['flow'] -= int(result.flow)
                acceptor = self.bot.get_user(discordID)
                embed = defaultEmbed(
                    "✅ 已成功施展摩拉克斯的力量", f"{ctx.author.mention}從銀行轉出了 {result.flow}枚flow幣給 {acceptor.mention}")
                setFooter(embed)
                await ctx.send(embed=embed)
                with open(f'cmd/asset/flow.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(users, file)
                with open(f'cmd/asset/bank.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(bank, file)
                break

    @commands.command()
    async def flow(self, ctx):
        embed = defaultEmbed(
            "flow系統", "`!acc`查看flow帳戶\n`!give @user <number>`給flow幣\n`!find`發布委託\n`!shop`商店\n`!shop buy`購買商品")
        setFooter(embed)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_role("小雪團隊")
    async def reset(self, ctx):
        bank['flow'] = 12000
        for user in users:
            discordID = user
            users[discordID]['flow'] = 100
            bank['flow'] -= 100
        embed = defaultEmbed("🔄 已重設世界的一切", f"所有人都回到100flow幣")
        setFooter(embed)
        with open(f'cmd/asset/flow.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(users, file)
        with open(f'cmd/asset/bank.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(bank, file)
        await ctx.send(embed=embed)

    @commands.command()
    async def total(self, ctx):
        total = 0
        count = 0
        for user in users:
            discordID = user
            count += 1
            total += users[discordID]['flow']
        flowSum = total+bank['flow']
        await ctx.send(f"目前群組裡共有:\n{count}個flow帳號\n用戶{total}+銀行{bank['flow']}={flowSum}枚flow幣")

    @commands.command()
    async def flows(self, ctx):
        with open(f'cmd/asset/flow.yaml', encoding='utf-8') as file:
            users = yaml.full_load(file)
        userStr = ""
        count = 1
        for user in users:
            discordID = user
            userStr += f"{count}. {users[discordID]['name']}: {users[discordID]['flow']}\n"
            count += 1
        embed = defaultEmbed("所有flow帳戶", userStr)
        setFooter(embed)
        await ctx.send(embed=embed)

    @commands.group()
    async def shop(self, ctx):
        if ctx.invoked_subcommand is None:
            itemStr = ""
            count = 1
            for item in shop:
                itemID = item
                itemStr = itemStr + \
                    f"{count}. {shop[itemID]['name']} - {shop[itemID]['flow']} flow ({shop[itemID]['current']}/{shop[itemID]['max']})\n||{itemID}||\n"
                count += 1
            embed = defaultEmbed("🛒 flow商店", itemStr)
            setFooter(embed)
            await ctx.send(embed=embed)

    @shop.command()
    @commands.has_role("小雪團隊")
    async def newitem(self, ctx):
        form = Form(ctx, '新增商品', cleanup=True)
        form.add_question('商品名稱?', 'name')
        form.add_question('flow幣價格?', 'flow')
        form.add_question('最大購買次數?', 'max')
        form.edit_and_delete(True)
        form.set_timeout(60)
        await form.set_color("0xa68bd3")
        result = await form.start()
        uuid = str(uuid.uuid4())
        shop[uuid] = {'name': result.name, 'flow': int(
            result.flow), 'current': 0, 'max': int(result.max)}
        with open(f'cmd/asset/shop.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(shop, file)
        await ctx.send(f"商品{result.name}新增成功")

    @shop.command()
    @commands.has_role("小雪團隊")
    async def removeitem(self, ctx, uuidInput):
        if uuidInput in shop:
            del shop[uuidInput]
            with open(f'cmd/asset/shop.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(shop, file)
            await ctx.send("商品刪除成功")

    @shop.command()
    async def buy(self, ctx):
        itemStr = ""
        count = 1
        for item in shop:
            itemID = item
            itemStr = itemStr + \
                f"{count}. {shop[itemID]['name']} - {shop[itemID]['flow']} flow ({shop[itemID]['current']}/{shop[itemID]['max']})\n"
            count += 1
        form = Form(ctx, '要購買什麼商品?(輸入數字)', cleanup=True)
        form.add_question(f'{itemStr}', 'number')
        form.edit_and_delete(True)
        form.set_timeout(60)
        await form.set_color("0xa68bd3")
        result = await form.start()
        shopList = list(shop.items())
        pos = int(result.number) - 1
        discordID = ctx.author.id
        if discordID in users:
            itemPrice = int(shopList[pos][1]['flow'])
            if users[discordID]['flow'] < itemPrice:
                await ctx.send(f"{ctx.author.mention} 你的flow幣不足夠購買這項商品")
                return
            if shopList[pos][1]['current'] >= shopList[pos][1]['max']:
                await ctx.send(f"{ctx.author.mention} 這個商品已經售罄了")
                return

            shopList[pos][1]['current'] += 1
            with open(f'cmd/asset/shop.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(shop, file)
            logID = str(uuid.uuid4())
            logs[logID] = {'item': shopList[pos][1]['name'],
                           'flow': itemPrice, 'buyerID': ctx.author.id}
            with open(f'cmd/asset/log.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(logs, file)
            users[discordID]['flow'] -= itemPrice
            bank['flow'] += itemPrice
            with open(f'cmd/asset/bank.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(bank, file)
            with open(f'cmd/asset/flow.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(users, file)
            await ctx.send(f"商品 {shopList[pos][1]['name']} 購買成功, 詳情請查看私訊")
            await ctx.author.send(f"您已在flow商城購買了 {shopList[1][pos]['name']} 商品, 請將下方的收據截圖並寄給小雪或律律來兌換商品")
            embed = defaultEmbed(
                "📜 購買證明", f"購買人: {ctx.author.mention}\n購買人ID: {ctx.author.id}\n商品: {shopList[pos]['name']}\nUUID: {shopList[pos]['uuid']}\n價格: {shopList[pos]['flow']}")
            setFooter(embed)
            await ctx.author.send(embed=embed)
        else:
            discordID = ctx.author.id
            user = self.bot.get_user(discordID)
            flowCog = self.bot.get_cog('FlowCog')
            await flowCog.register(ctx, user, discordID)

    @shop.command()
    @commands.has_role("小雪團隊")
    async def log(self, ctx):
        for log in logs:
            logID = log
            user = self.bot.get_user(logs[logID]['buyerID'])
            embed = defaultEmbed(
                "購買紀錄", f"商品: {logs[logID]['item']}\n價格: {logs[logID]['flow']}\n購買人: {user.mention}\n購買人ID: {logs[logID]['buyerID']}")
            setFooter(embed)
            await ctx.send(embed=embed)

    @shop.command()
    @commands.has_role("小雪團隊")
    async def clear(self, ctx, uuid):
        if uuid == "all":
            for item in shop:
                itemID = item
                shop[itemID]['current'] = 0
                with open(f'cmd/asset/shop.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(shop, file)
            await ctx.send(f"已將所有商品的購買次數清零")
            return
        elif int(uuid) in shop:
            del shop[uuid]

    @commands.Cog.listener()
    async def on_message(self, message):
        discordID = message.author.id
        channel = self.bot.get_channel(message.channel.id)
        if message.author == self.bot.user:
            return
        if "早安" in message.content:
            today = date.today()
            if discordID in users:
                if users[discordID]['morning'] != today:
                    users[discordID]['flow'] += 1
                    users[discordID]['morning'] = today
                    bank['flow'] -= 1
                    with open(f'cmd/asset/flow.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(users, file)
                    with open(f'cmd/asset/bank.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(bank, file)
                    await message.add_reaction(f"☀️")
            else:
                discordID = message.author.id
                user = self.bot.get_user(message.author.id)
                flowCog = self.bot.get_cog('FlowCog')
                await flowCog.register(channel, user, discordID)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        with open(f'cmd/asset/confirm.yaml', encoding='utf-8') as file:
            confirms = yaml.full_load(file)
        if payload.message_id == 965143582178705459 or payload.message_id == 963972447600771092:
            return
        if payload.emoji.name == '🆗' and payload.user_id != self.bot.user.id:
            if payload.message_id in confirms:
                authorID = confirms[payload.message_id]['authorID']
                receiverID = confirms[payload.message_id]['receiverID']
                flow = confirms[payload.message_id]['flow']
                type = confirms[payload.message_id]['type']
                title = confirms[payload.message_id]['title']
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
                setFooter(embed)
                await author.send(embed=embed)
                await receiver.send(embed=embed)
                del confirms[payload.message_id]
                with open(f'cmd/asset/confirm.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(confirms, file)
                with open(f'cmd/asset/flow.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(users, file)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        with open(f'cmd/asset/flow.yaml', encoding='utf-8') as file:
            users = yaml.full_load(file)
        if payload.message_id == 965143582178705459 or payload.message_id == 963972447600771092:
            return
        channel = self.bot.get_channel(payload.channel_id)
        message = channel.get_partial_message(payload.message_id)
        discordID = payload.user_id
        if discordID not in users:
            user = self.bot.get_user(payload.user_id)
            flowCog = self.bot.get_cog('FlowCog')
            await flowCog.register(channel, user, discordID)
            return
        if payload.emoji.name == '✅' and payload.user_id != self.bot.user.id:
            if payload.message_id in finds:
                if payload.user_id == finds[payload.message_id]['authorID']:
                    userObj = self.bot.get_user(payload.user_id)
                    await channel.send(f"{userObj.mention}不可以自己接自己的委託啦", delete_after=2)
                    return
                else:
                    await message.clear_reaction('✅')
                    author = self.bot.get_user(
                        finds[payload.message_id]['authorID'])
                    acceptUser = self.bot.get_user(payload.user_id)
                    if finds[payload.message_id]['type'] == 1:
                        await author.send(f"[成功接受委託] {acceptUser.mention} 接受了你的 {finds[payload.message_id]['title']} 委託")
                        await acceptUser.send(f"[成功接受委託] 你接受了 {author.mention} 的 {finds[payload.message_id]['title']} 委託")
                        await channel.send(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {finds[payload.message_id]['title']} 委託")
                    elif finds[payload.message_id]['type'] == 2:
                        await author.send(f"[成功接受素材委託] {acceptUser.mention} 接受了你的 {finds[payload.message_id]['title']} 素材委託")
                        await acceptUser.send(f"[成功接受素材委託] 你接受了 {author.mention} 的 {finds[payload.message_id]['title']} 素材委託")
                        await channel.send(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {finds[payload.message_id]['title']} 素材委託")
                    elif finds[payload.message_id]['type'] == 3:
                        await author.send(f"[成功接受委託] {acceptUser.mention} 接受了你的 {finds[payload.message_id]['title']} 委託")
                        await acceptUser.send(f"[成功接受委託] 你接受了 {author.mention} 的 {finds[payload.message_id]['title']} 委託")
                        await channel.send(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {finds[payload.message_id]['title']} 委託")
                    elif finds[payload.message_id]['type'] == 4:
                        await author.send(f"✅ {acceptUser.mention} 接受了你的 {finds[payload.message_id]['title']} 幫助")
                        await acceptUser.send(f"✅ 你接受了 {author.mention} 的 {finds[payload.message_id]['title']} 幫助")
                        await channel.send(f"✅ {acceptUser.mention} 接受 {author.mention} 的 {finds[payload.message_id]['title']} 幫助")

                    if finds[payload.message_id]['type'] == 4:
                        embedDM = defaultEmbed(
                            "結算單", f"當對方完成幫忙的內容時, 請按 🆗來結算flow幣\n按下後, 你的flow幣將會 **- {finds[payload.message_id]['flow']}**, 對方則會 **+ {finds[payload.message_id]['flow']}**")
                        setFooter(embedDM)
                        dm = await acceptUser.send(embed=embedDM)
                    else:
                        embedDM = defaultEmbed(
                            "結算單", f"當對方完成委託的內容時, 請按 🆗來結算flow幣\n按下後, 你的flow幣將會 **- {finds[payload.message_id]['flow']}**, 對方則會 **+ {finds[payload.message_id]['flow']}**")
                        setFooter(embedDM)
                        dm = await author.send(embed=embedDM)
                    await dm.add_reaction('🆗')

                    with open(f'cmd/asset/find.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(finds, file)
                    confirms[dm.id] = {'title': finds[payload.message_id]['title'], 'authorID': int(
                        finds[payload.message_id]['authorID']), 'receiverID': payload.user_id, 'flow': finds[payload.message_id]['flow'], 'type': finds[payload.message_id]['type']}
                    del finds[payload.message_id]
                    with open(f'cmd/asset/confirm.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(confirms, file)

    @commands.command()
    async def find(self, ctx):
        if ctx.channel.id != 960861105503232030:
            channel = self.bot.get_channel(960861105503232030)
            await ctx.send(f"請在{channel.mention}裡使用此指令")
            return
        await ctx.message.delete()
        discordID = ctx.author.id
        if discordID not in users:
            user = self.bot.get_user(discordID)
            flowCog = self.bot.get_cog('FlowCog')
            await flowCog.register(ctx, user, discordID)
            return
        roles = []
        for i in range(1, 9):
            roles.append(discord.utils.get(ctx.guild.roles, name=f"W{str(i)}"))
            i += 1
        roleForChannel = self.bot.get_channel(962311051683192842)
        roleStr = f'請至{roleForChannel.mention}選擇身份組'
        for role in roles:
            if role in ctx.author.roles:
                roleStr = role.name
                break
        embed = defaultEmbed("請選擇委託類別",
                             "1️⃣: 其他玩家進入你的世界(例如: 陪玩, 打素材等)\n2️⃣: 你進入其他玩家的世界(例如: 拿特產)\n3️⃣: 其他委託\n4️⃣: 可以幫助別人(讓拿素材, 可幫打刀鐔等)")
        message = await ctx.send(embed=embed)
        form = ReactionForm(message, self.bot, ctx.author)
        form.add_reaction("1️⃣", 1)
        form.add_reaction("2️⃣", 2)
        form.add_reaction("3️⃣", 3)
        form.add_reaction("4️⃣", 4)
        choice = await form.start()

        guild = self.bot.get_guild(916838066117824553)
        role = discord.utils.get(guild.roles, name=f"委託通知")

        if choice == 1:
            await message.delete()
            formTrue = Form(ctx, '設定流程', cleanup=True)
            formTrue.add_question('需要什麼幫助?(例如: 打刀鐔)', 'title')
            formTrue.add_question('你要付多少flow幣給幫你的人?', 'flow')
            formTrue.edit_and_delete(True)
            formTrue.set_timeout(30)
            await formTrue.set_color("0xa68bd3")
            result = await formTrue.start()

            if int(result.flow) < 0:
                embedResult = defaultEmbed(
                    f"發布失敗, 請輸入大於1的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return
            if users[discordID]['flow'] < int(result.flow):
                embedResult = defaultEmbed(
                    f"發布失敗, 請勿輸入大於自己擁有數量的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return
            if result.flow.isnumeric() == False:
                embedResult = defaultEmbed(
                    f"發布失敗, 請勿輸入非數字的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return

            embed = defaultEmbed(
                f"請求幫助: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n世界等級: >={roleStr}\n按 ✅ 來接受委託")
            setFooter(embed)
            message = await ctx.send(embed=embed)
            await message.add_reaction('✅')
            await ctx.send(role.mention)
            finds[message.id] = {'title': result.title, 'flow': int(
                result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 1}
            with open(f'cmd/asset/find.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(finds, file)

        elif choice == 2:
            await message.delete()
            formFalse = Form(ctx, '設定流程', cleanup=True)
            formFalse.add_question('需要什麼素材?(例如: 緋櫻繡球)', 'title')
            formFalse.add_question('你要付多少flow幣給讓你拿素材的人?', 'flow')
            formFalse.edit_and_delete(True)
            formFalse.set_timeout(30)
            await formFalse.set_color("0xa68bd3")
            result = await formFalse.start()

            if int(result.flow) < 0:
                embedResult = defaultEmbed(
                    f"發布失敗, 請輸入大於1的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return
            if users[discordID]['flow'] < int(result.flow):
                embedResult = defaultEmbed(
                    f"發布失敗, 請勿輸入大於自己擁有數量的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return

            embed = defaultEmbed(
                f"素材請求: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n世界等級: <={roleStr}\n按 ✅ 來接受請求")
            setFooter(embed)
            message = await ctx.send(embed=embed)
            await message.add_reaction('✅')
            await ctx.send(role.mention)
            finds[message.id] = {'title': result.title, 'flow': int(
                result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 2}
            with open(f'cmd/asset/find.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(finds, file)

        elif choice == 3:
            await message.delete()
            formFalse = Form(ctx, '設定流程', cleanup=True)
            formFalse.add_question('要委託什麼?', 'title')
            formFalse.add_question('你要付多少flow幣給接受委託的人?', 'flow')
            formFalse.edit_and_delete(True)
            formFalse.set_timeout(30)
            await formFalse.set_color("0xa68bd3")
            result = await formFalse.start()

            if int(result.flow) < 0:
                embedResult = defaultEmbed(
                    f"發布失敗, 請輸入大於1的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return
            if users[discordID]['flow'] < int(result.flow):
                embedResult = defaultEmbed(
                    f"發布失敗, 請勿輸入大於自己擁有數量的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return

            embed = defaultEmbed(
                f"委託: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n按 ✅ 來接受請求")
            setFooter(embed)
            message = await ctx.send(embed=embed)
            await message.add_reaction('✅')
            await ctx.send(role.mention)
            finds[message.id] = {'title': result.title, 'flow': int(
                result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 3}
            with open(f'cmd/asset/find.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(finds, file)

        elif choice == 4:
            await message.delete()
            formFalse = Form(ctx, '設定流程', cleanup=True)
            formFalse.add_question('你想要幫助什麼?', 'title')
            formFalse.add_question('被你幫助的人要付多少flow幣給你?', 'flow')
            formFalse.edit_and_delete(True)
            formFalse.set_timeout(60)
            await formFalse.set_color("0xa68bd3")
            result = await formFalse.start()

            if int(result.flow) < 0:
                embedResult = defaultEmbed(
                    f"發布失敗, 請輸入大於1的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return
            if users[discordID]['flow'] < int(result.flow):
                embedResult = defaultEmbed(
                    f"發布失敗, 請勿輸入大於自己擁有數量的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return

            embedResult = defaultEmbed(
                f"可以幫忙: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n按 ✅ 來接受幫助")
            setFooter(embedResult)
            message = await ctx.send(embed=embedResult)
            await message.add_reaction('✅')
            await ctx.send(role.mention)
            finds[message.id] = {'title': result.title, 'flow': int(
                result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 4}
            with open(f'cmd/asset/find.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(finds, file)


def setup(bot):
    bot.add_cog(FlowCog(bot))
