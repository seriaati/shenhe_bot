from discord.ext.forms import Form
from discord.ext import commands
from datetime import date
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
        with open(f'cmd/asset/flow.yaml', encoding='utf-8') as file:
            users = yaml.full_load(file)
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


def setup(bot):
    bot.add_cog(FlowCog(bot))
