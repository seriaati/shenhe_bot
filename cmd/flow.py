from discord.ext.forms import Form
from discord.ext import commands
from datetime import date
import yaml
import inflect
import global_vars
import emoji
import discord
import re
import sys
import getpass

owner = getpass.getuser()

sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')


global_vars.Global()

with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', encoding='utf-8') as file:
    users = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/find.yaml', encoding='utf-8') as file:
    finds = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/confirm.yaml', encoding='utf-8') as file:
    confirms = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', encoding='utf-8') as file:
    bank = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/shop.yaml', encoding='utf-8') as file:
    shop = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/log.yaml', encoding='utf-8') as file:
    logs = yaml.full_load(file)


class FlowCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def register(self, name, id):
        dcUser = self.bot.get_user(id)
        if not dcUser.bot:
            today = date.today()
            newUser = {'name': str(name), 'discordID': int(
                id), 'flow': 100, 'morning': today}
            bank['flow'] -= 100
            users.append(newUser)
            with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(users, file)
            with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(bank, file)
        else:
            return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id == 965143582178705459:
            if payload.emoji.name == "Serialook":
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
        if payload.message_id == 963972447600771092:
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
        elif payload.message_id == 965143582178705459:
            if payload.emoji.name == "Serialook":
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                role = discord.utils.get(guild.roles, name=f"委託通知")
                await member.remove_roles(role)

    @commands.command()
    async def acc(self, ctx, *, member: discord.Member = None):
        with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', encoding='utf-8') as file:
            users = yaml.full_load(file)
        member = member or ctx.author
        found = False
        for user in users:
            if user['discordID'] == member.id:
                found = True
                embed = global_vars.defaultEmbed(
                    f"使用者: {user['name']}", f"flow幣: {user['flow']}")
                global_vars.setFooter(embed)
                await ctx.send(embed=embed)
        if found == False:
            if not member.bot:
                discordID = member.id
                user = self.bot.get_user(discordID)
                await self.register(user, discordID)
                await ctx.send("你本來沒有帳號, 現在申鶴幫你做了一個, 再打`!acc`一次試試看")
            else:
                return

    @commands.command()
    @commands.has_role("小雪團隊")
    async def roles(self, ctx):
        channel = self.bot.get_channel(962311051683192842)
        embed = global_vars.defaultEmbed("請選擇你的世界等級", " ")
        global_vars.setFooter(embed)
        message = await channel.send(embed=embed)
        for i in range(1, 9):
            p = inflect.engine()
            word = p.number_to_words(i)
            emojiStr = emoji.emojize(f":{word}:", language='alias')
            await message.add_reaction(str(emojiStr))

    @commands.command()
    @commands.has_role("小雪團隊")
    async def notif_roles(self, ctx):
        channel = self.bot.get_channel(962311051683192842)
        embed = global_vars.defaultEmbed(
            "如果你想收到發布委託通知的話, 請選擇 <:Serialook:959100214747222067> 表情符號", " ")
        global_vars.setFooter(embed)
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
        found = False
        for user in users:
            if user['discordID'] == member.id:
                found = True
        if found == False:
            if not member.bot:
                discordID = member.id
                user = self.bot.get_user(discordID)
                await self.register(user, discordID)
            else:
                return
        for user in users:
            if user['discordID'] == ctx.author.id:
                if user['flow'] < int(argFlow):
                    embed = global_vars.defaultEmbed("❌交易失敗", "自己都不夠了還想給人ww")
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
                    return
                else:
                    user['flow'] -= int(argFlow)
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(users, file)
            if user['discordID'] == member.id:
                user['flow'] += int(argFlow)
                acceptor = self.bot.get_user(member.id)
                embed = global_vars.defaultEmbed(
                    "✅ 交易成功", f"{ctx.author.mention}給了{acceptor.mention} {str(argFlow)}枚flow幣")
                with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(users, file)
                global_vars.setFooter(embed)
                await ctx.send(embed=embed)

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
            id = int(re.search(r'\d+', member).group())
            for user in users:
                if user['discordID'] == id:
                    user['flow'] -= int(result.flow)
                    bank['flow'] += int(result.flow)
                    acceptor = self.bot.get_user(id)
                    embed = global_vars.defaultEmbed(
                        "✅ 已成功施展反摩拉克斯的力量", f"{ctx.author.mention} 從 {acceptor.mention} 的帳戶裡拿走了 {result.flow} 枚flow幣")
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(users, file)
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding='utf-8') as file:
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
            id = int(re.search(r'\d+', member).group())
            for user in users:
                if user['discordID'] == id:
                    user['flow'] += int(result.flow)
                    bank['flow'] -= int(result.flow)
                    acceptor = self.bot.get_user(id)
                    embed = global_vars.defaultEmbed(
                        "✅ 已成功施展摩拉克斯的力量", f"{ctx.author.mention}從銀行轉出了 {result.flow}枚flow幣給 {acceptor.mention}")
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(users, file)
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(bank, file)
                    break

    @commands.command()
    async def flow(self, ctx):
        embed = global_vars.defaultEmbed(
            "flow系統", "`!acc`查看flow帳戶\n`!give @user <number>`給flow幣\n`!find`發布委託\n`!shop`商店\n`!shop buy`購買商品")
        global_vars.setFooter(embed)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_role("小雪團隊")
    async def reset(self, ctx):
        bank['flow'] = 12000
        for user in users:
            user['flow'] = 100
            bank['flow'] -= 100
        embed = global_vars.defaultEmbed("🔄 已重設世界的一切", f"所有人都回到100flow幣")
        global_vars.setFooter(embed)
        with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(users, file)
        with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(bank, file)
        await ctx.send(embed=embed)

    @commands.command()
    async def total(self, ctx):
        total = 0
        count = 0
        for user in users:
            count += 1
            total += user['flow']
        flowSum = total+bank['flow']
        await ctx.send(f"目前群組裡共有:\n{count}個flow帳號\n用戶{total}+銀行{bank['flow']}={flowSum}枚flow幣")

    @commands.command()
    async def flows(self, ctx):
        userStr = ""
        count = 1
        for user in users:
            userStr += f"{count}. {user['name']} -{user['flow']}\n"
            count += 1
        embed = global_vars.defaultEmbed("所有flow帳戶", userStr)
        global_vars.setFooter(embed)
        await ctx.send(embed=embed)
        
def setup(bot):
    bot.add_cog(FlowCog(bot))
