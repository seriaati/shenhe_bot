#shenhe-bot by seria
#genshin verion = 2.6

import importlib
import genshin
import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import os
import discord
import asyncio
import DiscordUtils
import global_vars
import config
from discord.ext import commands
from discord.ext import tasks
from random import randint
global_vars.Global()
config.Token()

# 前綴, token, intents
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", help_command=None, intents=intents, case_insensitive=True)
token = config.bot_token

bot.load_extension("cmd.genshin_stuff")
bot.load_extension("cmd.call")
bot.load_extension("cmd.register")
bot.load_extension("cmd.othercmd")
bot.load_extension("cmd.farm")
bot.load_extension("cmd.help")
bot.load_extension("cmd.cmd")

# 私訊提醒功能
@tasks.loop(seconds=3600) # 1 hour
async def checkLoop():
    for user in global_vars.users:
        try:
            cookies = {"ltuid": user.ltuid, "ltoken": user.ltoken}
            uid = user.uid
            username = user.username
            userid = bot.get_user(user.discordID)
            client = genshin.GenshinClient(cookies)
            client.lang = "zh-tw"
            notes = await client.get_notes(uid)
            resin = notes.current_resin

            if resin >= 140 and user.dm == True and user.count <= 2:
                print("已私訊 "+str(userid))
                time = notes.until_resin_recovery
                hours, minutes = divmod(time // 60, 60)
                embed=global_vars.defaultEmbed(f"<:danger:959469906225692703>: 目前樹脂數量已經超過140!",f"<:resin:956377956115157022> 目前樹脂: {notes.current_resin}/{notes.max_resin}\n於 {hours:.0f} 小時 {minutes:.0f} 分鐘後填滿\n註: 如果你不想要收到這則通知, 請私訊或tag小雪\n註: 所有指令在私訊都能正常運作, 例如`!check`")
                global_vars.setFooter(embed)
                await userid.send(embed=embed)
                user.count = user.count+1
                await client.close()
            elif resin < 140:
                user.count = 0
            await client.close()

        except genshin.errors.InvalidCookies:
            print ("吐司帳號壞掉了")
            await client.close()

# 等待申鶴準備
@checkLoop.before_loop
async def beforeLoop():
    print('waiting...')
    await bot.wait_until_ready()

# 開機時
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online,activity = discord.Game(name=f'輸入!help來查看幫助'))
    print("Shenhe has logged in.")
    print("---------------------")

# 偵測機率字串
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if "機率" in message.content:
        value = randint(1,100)
        await message.channel.send(f"{value}%")
    await bot.process_commands(message)

# 新人加入
@bot.event
async def on_member_join(member):
    public = bot.get_channel(916951131022843964)
    await public.send("<@!459189783420207104> 櫃姊兔兔請準備出動!有新人要來了!")

# ping
@bot.command()
async def ping(ctx):
    await ctx.send('🏓 Pong! {0}ms'.format(round(bot.latency, 1)))

@bot.command()
async def vote(ctx):
    options = []
    emojis = []
    embedAsk = global_vars.defaultEmbed("是關於什麼的投票?","例如: ceye的頭像要用什麼")
    global_vars.setFooter(embedAsk)
    embedAsk = await ctx.send(embed=embedAsk)
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    try:
        message = await bot.wait_for('message', timeout= 30.0, check= check)
    except asyncio.TimeoutError:
        await ctx.send(timeOutErrorMsg)
        return
    else:
        question = message.content
        await message.delete()
        done = False
        while done == False:
            embed = global_vars.defaultEmbed("請輸入投票的選項，當完成時，請打done","例如: 看牙醫的胡桃")
            global_vars.setFooter(embed)
            await embedAsk.edit(embed=embed)
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            try:
                message = await bot.wait_for('message', timeout= 30.0, check= check)
            except asyncio.TimeoutError:
                await ctx.send(timeOutErrorMsg)
                return
            else:
                option = message.content
                await message.delete()
                if option == "done":
                    done = True
                else:
                    done = False
                    options.append(option)
                    embed = global_vars.defaultEmbed("該選項要使用什麼表情符號來代表?","註: 只能使用此群組所擁有的表情符號\n如要新增表情符號，請告知Tedd")
                    global_vars.setFooter(embed)
                    await embedAsk.edit(embed=embed)
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel
                    try:
                        message = await bot.wait_for('message', timeout= 30.0, check= check)
                    except asyncio.TimeoutError:
                        await ctx.send(timeOutErrorMsg)
                        return
                    else:
                        emoji = message.content
                        await message.delete()
                        emojis.append(emoji)
                        done = False
        optionStr = ""
        count = 0
        for option in options:
            optionStr = optionStr + emojis[count] + " : " + option + "\n"
            count = count + 1
        embedPoll = global_vars.defaultEmbed(question,optionStr)
        global_vars.setFooter(embedPoll)
        await embedAsk.edit(embed=embedPoll)
        for emoji in emojis:
            await embedAsk.add_reaction(emoji)

@bot.command()
@commands.is_owner()
async def loop_start(ctx):
    checkLoop.start()
    await ctx.send("loop_start")

@bot.command()
@commands.is_owner()
async def reload(ctx, arg):
    bot.reload_extension(f"cmd.{arg}")
    await ctx.send(f"reloded {arg}")

@bot.command()
@commands.is_owner()
async def reload_user(ctx):
    importlib.reload(global_vars)

@bot.group()
async def group(ctx):
    if ctx.invoked_subcommand is None:
        embedAsk = global_vars.defaultEmbed("要執行什麼操作?","create: 創建小組\ndelete: 刪除小組\nadd: 新增成員\nremove: 移除成員\njoin: 加入小組\nleave: 退出小組\nlist: 列出所有小組")
        global_vars.setFooter(embedAsk)
        embedAsk = await ctx.send(embed=embedAsk)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            message = await bot.wait_for('message', timeout= 30.0, check= check)
        except asyncio.TimeoutError:
            await ctx.send(timeOutErrorMsg)
            return
        else:
            answer = message.content
            if answer == "create":
                embed = discord.Embed(title = "打算創建的小組名稱?",description="例如: 可莉炸魚團",color=purpleColor)
                global_vars.setFooter(embed)
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                try:
                    message = await bot.wait_for('message', timeout= 30.0, check= check)
                except asyncio.TimeoutError:
                    await ctx.send(timeOutErrorMsg)
                    return
                else:
                    answer = message.content
                    groups.append(Group(answer))
                    embed = discord.Embed(title = "✅ 小組創建成功",
                            description=f"小組名稱: {answer}", color=purpleColor)
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
            if answer == "delete":
                groupStr = ""
                for group in groups:
                    groupStr = groupStr + "• " + group.name + "\n"
                embed = discord.Embed(title = "打算刪除的小組名稱?",description=f"目前存在的小組: \n{groupStr}",color=purpleColor)
                global_vars.setFooter(embed)
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                try:
                    message = await bot.wait_for('message', timeout= 30.0, check= check)
                except asyncio.TimeoutError:
                    await ctx.send(timeOutErrorMsg)
                    return
                else:
                    answer = message.content
                    found = False
                    for group in groups:
                        if answer == group.name:
                            found = True
                            groups.remove(group)
                    if found == True:
                        embed = global_vars.defaultEmbed("🗑️ 小組刪除成功",f"小組名稱: {answer}")
                        global_vars.setFooter(embed)
                        await ctx.send(embed=embed)
                    elif found == False:
                        embed = embedNoGroup
                        global_vars.setFooter(embed)
                        await ctx.send(embed=embed)
            if answer == "list":
                for group in groups:
                    memberStr = ""
                    for member in group.members:
                        memberStr = memberStr + "• " + member + "\n"
                    embed = discord.Embed(title = f"組名: {group.name}", description=f"組員: \n{memberStr}", color=purpleColor)
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
            if answer == "add":
                groupStr = ""
                for group in groups:
                    groupStr = groupStr + "• " + group.name + "\n"
                embed = discord.Embed(title = f"要在哪個小組新增成員?", description=f"目前存在的小組: \n{groupStr}", color=purpleColor)
                global_vars.setFooter(embed)
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                try:
                    message = await bot.wait_for('message', timeout= 30.0, check= check)
                except asyncio.TimeoutError:
                    await ctx.send(timeOutErrorMsg)
                    return
                else:
                    answer = message.content
                    found = False
                    for group in groups:
                        if answer==group.name:
                            found = True
                            embed = discord.Embed(title = f"要新增哪些成員?", description=f"如果有多個成員, 請以逗號分割\n例如: @小雪, @Sueno", color=purpleColor)
                            global_vars.setFooter(embed)
                            await ctx.send(embed=embed)
                            def check(m):
                                return m.author == ctx.author and m.channel == ctx.channel 
                            try:
                                message = await bot.wait_for('message', timeout= 30.0, check= check)
                            except asyncio.TimeoutError:
                                await ctx.send(timeOutErrorMsg)
                                return
                            else:
                                answer = message.content
                                memberAdd = answer.split(", ")
                                for member in memberAdd:
                                    group.members.append(member)
                                memberStr = ""
                                for member in memberAdd:
                                    memberStr = memberStr + "• " + member + "\n"
                                embed = discord.Embed(title = "✅ 成員新增成功",description=f"小組名稱: {group.name}\n新增成員:\n {memberStr}", color=purpleColor)
                                global_vars.setFooter(embed)
                                await ctx.send(embed=embed)
                    if found == False:
                        embed = embedNoGroup
                        global_vars.setFooter(embed)
                        await ctx.send(embed=embed)
            if answer == "remove":
                groupStr = ""
                for group in groups:
                    groupStr = groupStr + "• " + group.name + "\n"
                embed = discord.Embed(title = f"要從哪個小組中移除成員?", description=f"目前存在的小組: \n{groupStr}", color = purpleColor)
                global_vars.setFooter(embed)
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                try:
                    message = await bot.wait_for('message', timeout= 30.0, check= check)
                except asyncio.TimeoutError:
                    await ctx.send(timeOutErrorMsg)
                    return
                else:
                    answer = message.content
                    found = False
                    for group in groups:
                        if answer==group.name:
                            found = True
                            embed = discord.Embed(title = f"要移除哪些成員?", description=f"如果有多個成員, 請以逗號分割\n例如: @小雪, @Sueno", color=purpleColor)
                            global_vars.setFooter(embed)
                            await ctx.send(embed=embed)
                            def check(m):
                                return m.author == ctx.author and m.channel == ctx.channel 
                            try:
                                message = await bot.wait_for('message', timeout= 30.0, check= check)
                            except asyncio.TimeoutError:
                                await ctx.send(timeOutErrorMsg)
                                return
                            else:
                                answer = message.content
                                memberDel = answer.split(", ")
                                print(memberDel)
                                for member in memberDel:
                                    group.members.remove(member)
                                memberStr = ""
                                for member in memberDel:
                                    memberStr = memberStr + "• " + member + "\n"
                                embed = discord.Embed(title = "✅ 成員移除成功",description=f"小組名稱: {group.name}\n移除成員: \n{memberStr}", color=purpleColor)
                                global_vars.setFooter(embed)
                                await ctx.send(embed=embed)
                    if found == False:
                        embed = embedNoGroup
                        global_vars.setFooter(embed)
                        await ctx.send(embed=embed)
            if answer == "join":
                groupStr = ""
                for group in groups:
                    groupStr = groupStr + "• " + group.name + "\n"
                embed = discord.Embed(title = f"要加入哪個小組?", description=f"目前存在的小組: \n{groupStr}", color=purpleColor)
                global_vars.setFooter(embed)
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                try:
                    message = await bot.wait_for('message', timeout= 30.0, check= check)
                except asyncio.TimeoutError:
                    await ctx.send(timeOutErrorMsg)
                    return
                else:
                    answer = message.content
                    found = False
                    for group in groups:
                        if answer == group.name:
                            found = True
                            group.members.append("<@!"+str(ctx.author.id)+">")
                            embed = discord.Embed(title = "✅ 成功加入小組",description=f"小組名稱: {answer}", color=purpleColor)
                            global_vars.setFooter(embed)
                            await ctx.send(embed=embed)
                    if found == False:
                        embed = embedNoGroup
                        global_vars.setFooter(embed)
                        await ctx.send(embed=embed)
            if answer == "leave":
                groupStr = ""
                for group in groups:
                    authorMention = "<@!"+str(ctx.author.id)+">"
                    if authorMention in group.members:
                        groupStr = groupStr + "• " + group.name + "\n"
                embed = discord.Embed(title = f"要退出哪個小組?", description=f"你目前在的小組有: \n{groupStr}", color=purpleColor)
                global_vars.setFooter(embed)
                await ctx.send(embed=embed)
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                try:
                    message = await bot.wait_for('message', timeout= 30.0, check= check)
                except asyncio.TimeoutError:
                    await ctx.send(timeOutErrorMsg)
                    return
                else:
                    answer = message.content
                    found = False
                    for group in groups:
                        if answer == group.name:
                            found = True
                            group.members.remove("<@!"+str(ctx.author.id)+">")
                            embed = discord.Embed(title = "✅ 成功退出小組",description=f"小組名稱: {answer}", color=purpleColor)
                            global_vars.setFooter(embed)
                            await ctx.send(embed=embed)
                    if found == False:
                        embed = embedNoGroup
                        global_vars.setFooter(embed)
                        await ctx.send(embed=embed)

@group.command()
async def create(ctx):
    embedAsk = global_vars.defaultEmbed("打算創建的小組名稱?","例如: 可莉炸魚團")
    global_vars.setFooter(embedAsk)
    embedAsk = await ctx.send(embed=embedAsk)
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    try:
        message = await bot.wait_for('message', timeout= 30.0, check= check)
    except asyncio.TimeoutError:
        await ctx.send(timeOutErrorMsg)
        return
    else:
        answer = message.content
        await message.delete()
        groups.append(Group(answer))
        embed = global_vars.defaultEmbed("✅ 小組創建成功",f"小組名稱: {answer}")
        global_vars.setFooter(embed)
        await embedAsk.edit(embed=embed)

@group.command()
async def delete(ctx):
    groupStr = ""
    for group in groups:
        groupStr = groupStr + "• " + group.name + "\n"
    embedAsk = global_vars.defaultEmbed("打算刪除的小組名稱?",f"目前存在的小組: \n{groupStr}")
    global_vars.setFooter(embedAsk)
    embedAsk = await ctx.send(embed=embedAsk)
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    try:
        message = await bot.wait_for('message', timeout= 30.0, check= check)
    except asyncio.TimeoutError:
        await ctx.send(timeOutErrorMsg)
        return
    else:
        answer = message.content
        await message.delete()
        found = False
        for group in groups:
            if answer == group.name:
                found = True
                groups.remove(group)
        if found == True:
            embed = global_vars.defaultEmbed("🗑️ 小組刪除成功",f"小組名稱: {answer}")
            global_vars.setFooter(embed)
            await embedAsk.edit(embed=embed)
        elif found == False:
            embed = embedNoGroup
            global_vars.setFooter(embed)
            await embedAsk.edit(embed=embed)

@group.command()
async def list(ctx):
    for group in groups:
        memberStr = ""
        for member in group.members:
            memberStr = memberStr + "• " + member + "\n"
        embedList = global_vars.defaultEmbed(f"組名: {group.name}", f"組員: \n{memberStr}")
        global_vars.setFooter(embedList)
        await ctx.send(embed=embedList)

@group.command()
async def add(ctx):
    groupStr = ""
    for group in groups:
        groupStr = groupStr + "• " + group.name + "\n"
    embedAsk = global_vars.defaultEmbed(f"要在哪個小組新增成員?",f"目前存在的小組: \n{groupStr}")
    global_vars.setFooter(embedAsk)
    embedAsk = await ctx.send(embed=embedAsk)
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    try:
        message = await bot.wait_for('message', timeout= 30.0, check= check)
    except asyncio.TimeoutError:
        await ctx.send(timeOutErrorMsg)
        return
    else:
        answer = message.content
        await message.delete()
        found = False
        for group in groups:
            if answer==group.name:
                found = True
                embed = global_vars.defaultEmbed(f"要新增哪些成員?",f"如果有多個成員, 請以逗號分割\n例如: @小雪, @Sueno")
                global_vars.setFooter(embed)
                await embedAsk.edit(embed=embed)
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel 
                try:
                    message = await bot.wait_for('message', timeout= 30.0, check= check)
                except asyncio.TimeoutError:
                    await ctx.send(timeOutErrorMsg)
                    return
                else:
                    answer = message.content
                    await message.delete()
                    memberAdd = answer.split(", ")
                    for member in memberAdd:
                        group.members.append(member)
                    memberStr = ""
                    for member in memberAdd:
                        memberStr = memberStr + "• " + member + "\n"
                    embed = global_vars.defaultEmbed("✅ 成員新增成功",f"小組名稱: {group.name}\n新增成員:\n {memberStr}")
                    global_vars.setFooter(embed)
                    await embedAsk.edit(embed=embed)
        if found == False:
            embed = embedNoGroup
            global_vars.setFooter(embed)
            await embedAsk.edit(embed=embed)

@group.command()
async def remove(ctx):
    groupStr = ""
    for group in groups:
        groupStr = groupStr + "• " + group.name + "\n"
    embedAsk = global_vars.defaultEmbed(f"要從哪個小組中移除成員?",f"目前存在的小組: \n{groupStr}")
    global_vars.setFooter(embedAsk)
    embedAsk = await ctx.send(embed=embedAsk)
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    try:
        message = await bot.wait_for('message', timeout= 30.0, check= check)
    except asyncio.TimeoutError:
        await ctx.send(timeOutErrorMsg)
        return
    else:
        answer = message.content
        await message.delete()
        found = False
        for group in groups:
            if answer==group.name:
                found = True
                embed = global_vars.defaultEmbed(f"要移除哪些成員?",f"如果有多個成員, 請以逗號分割\n例如: @小雪, @Sueno")
                global_vars.setFooter(embed)
                await embedAsk.edit(embed=embed)
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel 
                try:
                    message = await bot.wait_for('message', timeout= 30.0, check= check)
                except asyncio.TimeoutError:
                    await ctx.send(timeOutErrorMsg)
                    return
                else:
                    answer = message.content
                    await message.delete()
                    memberDel = answer.split(", ")
                    for member in memberDel:
                        group.members.remove(member)
                    memberStr = ""
                    for member in memberDel:
                        memberStr = memberStr + "• " + member + "\n"
                    embed = global_vars.defaultEmbed("✅ 成員移除成功",f"小組名稱: {group.name}\n移除成員: \n{memberStr}")
                    global_vars.setFooter(embed)
                    await message.delete()
        if found == False:
            embed = embedNoGroup
            global_vars.setFooter(embed)
            await embedAsk.edit(embed=embed)

@group.command()
async def join(ctx):
    groupStr = ""
    for group in groups:
        groupStr = groupStr + "• " + group.name + "\n"
    embedAsk = global_vars.defaultEmbed(f"要加入哪個小組?",f"目前存在的小組: \n{groupStr}")
    global_vars.setFooter(embedAsk)
    embedAsk = await ctx.send(embed=embedAsk)
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    try:
        message = await bot.wait_for('message', timeout= 30.0, check= check)
    except asyncio.TimeoutError:
        await ctx.send(timeOutErrorMsg)
        return
    else:
        answer = message.content
        await message.delete()
        found = False
        for group in groups:
            if answer == group.name:
                found = True
                group.members.append("<@!"+str(ctx.author.id)+">")
                embed = global_vars.defaultEmbed(f"✅ 成功加入小組",f"小組名稱: {answer}")
                global_vars.setFooter(embed)
                await embedAsk.edit(embed=embed)
        if found == False:
            embed = embedNoGroup
            global_vars.setFooter(embed)
            await embedAsk.edit(embed=embed)

@group.command()
async def leave(ctx):
    groupStr = ""
    for group in groups:
        authorMention = "<@!"+str(ctx.author.id)+">"
        if authorMention in group.members:
            groupStr = groupStr + "• " + group.name + "\n"
    embedAsk = discord.Embed(title = f"要退出哪個小組?", description=f"你目前在的小組有: \n{groupStr}", color=purpleColor)
    global_vars.setFooter(embedAsk)
    embedAsk = await ctx.send(embed=embedAsk)
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    try:
        message = await bot.wait_for('message', timeout= 30.0, check= check)
    except asyncio.TimeoutError:
        await ctx.send(timeOutErrorMsg)
        return
    else:
        answer = message.content
        await message.delete()
        found = False
        for group in groups:
            if answer == group.name:
                found = True
                group.members.remove("<@!"+str(ctx.author.id)+">")
                embed = global_vars.defaultEmbed("✅ 成功退出小組",f"小組名稱: {answer}")
                global_vars.setFooter(embed)
                await embedAsk.edit(embed=embed)
        if found == False:
            embed = embedNoGroup
            global_vars.setFooter(embed)
            await embedAsk.edit(embed=embed)

if __name__ == "__main__":
    bot.run(token)