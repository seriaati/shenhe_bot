import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import discord, asyncio
import global_vars
global_vars.Global()
import groups 
groups.group()
from discord.ext import commands
from classes import Group 

class GroupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def group(self, ctx):
        if ctx.invoked_subcommand is None:
            embedAsk = global_vars.defaultEmbed("要執行什麼操作?","create: 創建小組\ndelete: 刪除小組\nadd: 新增成員\nremove: 移除成員\njoin: 加入小組\nleave: 退出小組\nlist: 列出所有小組")
            global_vars.setFooter(embedAsk)
            embedAsk = await ctx.send(embed=embedAsk)
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            try:
                message = await self.bot.wait_for('message', timeout= 30.0, check= check)
            except asyncio.TimeoutError:
                await ctx.send(global_vars.timeOutErrorMsg)
                return
            else:
                answer = message.content
                if answer == "create":
                    embed = global_vars.defaultEmbed("打算創建的小組名稱?", 
                        "例如: 可莉炸魚團")
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel
                    try:
                        message = await self.bot.wait_for('message', timeout= 30.0, check= check)
                    except asyncio.TimeoutError:
                        await ctx.send(global_vars.timeOutErrorMsg)
                        return
                    else:
                        answer = message.content
                        groups.groups.append(Group(answer))
                        embed = global_vars.defaultEmbed("✅ 小組創建成功", 
                            f"小組名稱: {answer}")
                        global_vars.setFooter(embed)
                        await ctx.send(embed=embed)
                if answer == "delete":
                    global_vars.groupStr = ""
                    for group in groups.groups:
                        global_vars.groupStr = global_vars.groupStr + "• " + group.name + "\n"
                    embed = global_vars.defaultEmbed("打算刪除的小組名稱?", 
                        f"目前存在的小組: \n{global_vars.groupStr}")
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel
                    try:
                        message = await self.bot.wait_for('message', 
                            timeout= 30.0, check= check)
                    except asyncio.TimeoutError:
                        await ctx.send(global_vars.timeOutErrorMsg)
                        return
                    else:
                        answer = message.content
                        found = False
                        for group in groups.groups:
                            if answer == group.name:
                                found = True
                                groups.groups.remove(group)
                        if found == True:
                            embed = global_vars.defaultEmbed("🗑️ 小組刪除成功", 
                                f"小組名稱: {answer}")
                            global_vars.setFooter(embed)
                            await ctx.send(embed=embed)
                        elif found == False:
                            embed = global_vars.embedNoGroup
                            global_vars.setFooter(embed)
                            await ctx.send(embed=embed)
                if answer == "list":
                    for group in groups.groups:
                        memberStr = ""
                        for member in group.members:
                            memberStr = memberStr + "• " + member + "\n"
                        embed = global_vars.defaultEmbed(f"組名: {group.name}", 
                            f"組員: \n{memberStr}")
                        global_vars.setFooter(embed)
                        await ctx.send(embed=embed)
                if answer == "add":
                    global_vars.groupStr = ""
                    for group in groups.groups:
                        global_vars.groupStr = global_vars.groupStr + "• " + group.name + "\n"
                    embed = global_vars.defaultEmbed(f"要在哪個小組新增成員?", 
                        f"目前存在的小組: \n{global_vars.groupStr}")
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel
                    try:
                        message = await self.bot.wait_for('message', timeout= 30.0, check= check)
                    except asyncio.TimeoutError:
                        await ctx.send(global_vars.timeOutErrorMsg)
                        return
                    else:
                        answer = message.content
                        found = False
                        for group in groups.groups:
                            if answer==group.name:
                                found = True
                                embed = global_vars.defaultEmbed(f"要新增哪些成員?", 
                                    f"如果有多個成員, 請以逗號分割\n例如: @小雪, @Sueno")
                                global_vars.setFooter(embed)
                                await ctx.send(embed=embed)
                                def check(m):
                                    return m.author == ctx.author and m.channel == ctx.channel 
                                try:
                                    message = await self.bot.wait_for('message', timeout= 30.0, check= check)
                                except asyncio.TimeoutError:
                                    await ctx.send(global_vars.timeOutErrorMsg)
                                    return
                                else:
                                    answer = message.content
                                    memberAdd = answer.split(", ")
                                    for member in memberAdd:
                                        group.members.append(member)
                                    memberStr = ""
                                    for member in memberAdd:
                                        memberStr = memberStr + "• " + member + "\n"
                                    embed = global_vars.defaultEmbed("✅ 成員新增成功",
                                        f"小組名稱: {group.name}\n新增成員:\n {memberStr}")
                                    global_vars.setFooter(embed)
                                    await ctx.send(embed=embed)
                        if found == False:
                            embed = global_vars.embedNoGroup
                            global_vars.setFooter(embed)
                            await ctx.send(embed=embed)
                if answer == "remove":
                    global_vars.groupStr = ""
                    for group in groups.groups:
                        global_vars.groupStr = global_vars.groupStr + "• " + group.name + "\n"
                    embed = global_vars.defaultEmbed("要從哪個小組中移除成員?",
                        f"目前存在的小組: \n{global_vars.groupStr}")
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel
                    try:
                        message = await self.bot.wait_for('message', timeout= 30.0, check= check)
                    except asyncio.TimeoutError:
                        await ctx.send(global_vars.timeOutErrorMsg)
                        return
                    else:
                        answer = message.content
                        found = False
                        for group in groups.groups:
                            if answer==group.name:
                                found = True
                                embed = global_vars.defaultEmbed(f"要移除哪些成員?", 
                                    "如果有多個成員, 請以逗號分割\n例如: @小雪, @Sueno")
                                global_vars.setFooter(embed)
                                await ctx.send(embed=embed)
                                def check(m):
                                    return m.author == ctx.author and m.channel == ctx.channel 
                                try:
                                    message = await self.bot.wait_for('message', 
                                        timeout= 30.0, check= check)
                                except asyncio.TimeoutError:
                                    await ctx.send(global_vars.timeOutErrorMsg)
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
                                    embed = global_vars.defaultEmbed(
                                        "✅ 成員移除成功",
                                        f"小組名稱: {group.name}\n移除成員: \n{memberStr}")
                                    global_vars.setFooter(embed)
                                    await ctx.send(embed=embed)
                        if found == False:
                            embed = global_vars.embedNoGroup
                            global_vars.setFooter(embed)
                            await ctx.send(embed=embed)
                if answer == "join":
                    global_vars.groupStr = ""
                    for group in groups.groups:
                        global_vars.groupStr = global_vars.groupStr + "• " + group.name + "\n"
                    embed = global_vars.defaultEmbed("要加入哪個小組?",
                        f"目前存在的小組: \n{global_vars.groupStr}")
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel
                    try:
                        message = await self.bot.wait_for('message', timeout= 30.0, check= check)
                    except asyncio.TimeoutError:
                        await ctx.send(global_vars.timeOutErrorMsg)
                        return
                    else:
                        answer = message.content
                        found = False
                        for group in groups.groups:
                            if answer == group.name:
                                found = True
                                group.members.append("<@!"+str(ctx.author.id)+">")
                                embed = global_vars.defaultEmbed("✅ 成功加入小組", 
                                    f"小組名稱: {answer}")
                                global_vars.setFooter(embed)
                                await ctx.send(embed=embed)
                        if found == False:
                            embed = global_vars.embedNoGroup
                            global_vars.setFooter(embed)
                            await ctx.send(embed=embed)
                if answer == "leave":
                    global_vars.groupStr = ""
                    for group in groups.groups:
                        authorMention = "<@!"+str(ctx.author.id)+">"
                        if authorMention in group.members:
                            global_vars.groupStr = global_vars.groupStr + "• " + group.name + "\n"
                    embed = global_vars.defaultEmbed("要退出哪個小組?", 
                        f"你目前在的小組有: \n{global_vars.groupStr}")
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel
                    try:
                        message = await self.bot.wait_for('message', timeout= 30.0, check= check)
                    except asyncio.TimeoutError:
                        await ctx.send(global_vars.timeOutErrorMsg)
                        return
                    else:
                        answer = message.content
                        found = False
                        for group in groups.groups:
                            if answer == group.name:
                                found = True
                                group.members.remove("<@!"+str(ctx.author.id)+">")
                                embed = global_vars.defaultEmbed("✅ 成功退出小組",
                                    f"小組名稱: {answer}")
                                global_vars.setFooter(embed)
                                await ctx.send(embed=embed)
                        if found == False:
                            embed = global_vars.embedNoGroup
                            global_vars.setFooter(embed)
                            await ctx.send(embed=embed)
        pass
    @group.command()
    async def create(self, ctx):
        embedAsk = global_vars.defaultEmbed("打算創建的小組名稱?","例如: 可莉炸魚團")
        global_vars.setFooter(embedAsk)
        embedAsk = await ctx.send(embed=embedAsk)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            message = await self.bot.wait_for('message', timeout= 30.0, check= check)
        except asyncio.TimeoutError:
            await ctx.send(global_vars.timeOutErrorMsg)
            return
        else:
            answer = message.content
            await message.delete()
            groups.groups.append(Group(answer))
            embed = global_vars.defaultEmbed("✅ 小組創建成功",f"小組名稱: {answer}")
            global_vars.setFooter(embed)
            await embedAsk.edit(embed=embed)

    @group.command()
    async def delete(self, ctx):
        global_vars.groupStr = ""
        for group in groups.groups:
            global_vars.groupStr = global_vars.groupStr + "• " + group.name + "\n"
        embedAsk = global_vars.defaultEmbed("打算刪除的小組名稱?",f"目前存在的小組: \n{global_vars.groupStr}")
        global_vars.setFooter(embedAsk)
        embedAsk = await ctx.send(embed=embedAsk)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            message = await self.bot.wait_for('message', timeout= 30.0, check= check)
        except asyncio.TimeoutError:
            await ctx.send(global_vars.timeOutErrorMsg)
            return
        else:
            answer = message.content
            await message.delete()
            found = False
            for group in groups.groups:
                if answer == group.name:
                    found = True
                    groups.groups.remove(group)
            if found == True:
                embed = global_vars.defaultEmbed("🗑️ 小組刪除成功",f"小組名稱: {answer}")
                global_vars.setFooter(embed)
                await embedAsk.edit(embed=embed)
            elif found == False:
                embed = global_vars.embedNoGroup
                global_vars.setFooter(embed)
                await embedAsk.edit(embed=embed)

    @group.command()
    async def list(self, ctx):
        for group in groups.groups:
            memberStr = ""
            for member in group.members:
                memberStr = memberStr + "• " + member + "\n"
            embedList = global_vars.defaultEmbed(f"組名: {group.name}", f"組員: \n{memberStr}")
            global_vars.setFooter(embedList)
            await ctx.send(embed=embedList)

    @group.command()
    async def add(self, ctx):
        global_vars.groupStr = ""
        for group in groups.groups:
            global_vars.groupStr = global_vars.groupStr + "• " + group.name + "\n"
        embedAsk = global_vars.defaultEmbed(f"要在哪個小組新增成員?",f"目前存在的小組: \n{global_vars.groupStr}")
        global_vars.setFooter(embedAsk)
        embedAsk = await ctx.send(embed=embedAsk)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            message = await self.bot.wait_for('message', timeout= 30.0, check= check)
        except asyncio.TimeoutError:
            await ctx.send(global_vars.timeOutErrorMsg)
            return
        else:
            answer = message.content
            await message.delete()
            found = False
            for group in groups.groups:
                if answer==group.name:
                    found = True
                    embed = global_vars.defaultEmbed(f"要新增哪些成員?",f"如果有多個成員, 請以逗號分割\n例如: @小雪, @Sueno")
                    global_vars.setFooter(embed)
                    await embedAsk.edit(embed=embed)
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel 
                    try:
                        message = await self.bot.wait_for('message', timeout= 30.0, check= check)
                    except asyncio.TimeoutError:
                        await ctx.send(global_vars.timeOutErrorMsg)
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
                embed = global_vars.embedNoGroup
                global_vars.setFooter(embed)
                await embedAsk.edit(embed=embed)

    @group.command()
    async def remove(self, ctx):
        global_vars.groupStr = ""
        for group in groups.groups:
            global_vars.groupStr = global_vars.groupStr + "• " + group.name + "\n"
        embedAsk = global_vars.defaultEmbed(f"要從哪個小組中移除成員?",f"目前存在的小組: \n{global_vars.groupStr}")
        global_vars.setFooter(embedAsk)
        embedAsk = await ctx.send(embed=embedAsk)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            message = await self.bot.wait_for('message', timeout= 30.0, check= check)
        except asyncio.TimeoutError:
            await ctx.send(global_vars.timeOutErrorMsg)
            return
        else:
            answer = message.content
            await message.delete()
            found = False
            for group in groups.groups:
                if answer==group.name:
                    found = True
                    embed = global_vars.defaultEmbed(f"要移除哪些成員?",f"如果有多個成員, 請以逗號分割\n例如: @小雪, @Sueno")
                    global_vars.setFooter(embed)
                    await embedAsk.edit(embed=embed)
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel 
                    try:
                        message = await self.bot.wait_for('message', timeout= 30.0, check= check)
                    except asyncio.TimeoutError:
                        await ctx.send(global_vars.timeOutErrorMsg)
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
                        embed = global_vars.defaultEmbed("✅ 成員移除成功",
                            f"小組名稱: {group.name}\n移除成員: \n{memberStr}")
                        global_vars.setFooter(embed)
                        await message.delete()
            if found == False:
                embed = global_vars.embedNoGroup
                global_vars.setFooter(embed)
                await embedAsk.edit(embed=embed)

    @group.command()
    async def join(self, ctx):
        global_vars.groupStr = ""
        for group in groups.groups:
            global_vars.groupStr = global_vars.groupStr + "• " + group.name + "\n"
        embedAsk = global_vars.defaultEmbed(f"要加入哪個小組?",
            f"目前存在的小組: \n{global_vars.groupStr}")
        global_vars.setFooter(embedAsk)
        embedAsk = await ctx.send(embed=embedAsk)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            message = await self.bot.wait_for('message', timeout= 30.0, check= check)
        except asyncio.TimeoutError:
            await ctx.send(global_vars.timeOutErrorMsg)
            return
        else:
            answer = message.content
            await message.delete()
            found = False
            for group in groups.groups:
                if answer == group.name:
                    found = True
                    group.members.append("<@!"+str(ctx.author.id)+">")
                    embed = global_vars.defaultEmbed(f"✅ 成功加入小組",
                        f"小組名稱: {answer}")
                    global_vars.setFooter(embed)
                    await embedAsk.edit(embed=embed)
            if found == False:
                embed = global_vars.embedNoGroup
                global_vars.setFooter(embed)
                await embedAsk.edit(embed=embed)

    @group.command()
    async def leave(self, ctx):
        global_vars.groupStr = ""
        for group in groups.groups:
            authorMention = "<@!"+str(ctx.author.id)+">"
            if authorMention in group.members:
                global_vars.groupStr = global_vars.groupStr + "• " + group.name + "\n"
        embedAsk = global_vars.defaultEmbed(f"要退出哪個小組?", 
            f"你目前在的小組有: \n{global_vars.groupStr}")
        global_vars.setFooter(embedAsk)
        embedAsk = await ctx.send(embed=embedAsk)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            message = await self.bot.wait_for('message', 
                timeout= 30.0, check= check)
        except asyncio.TimeoutError:
            await ctx.send(global_vars.timeOutErrorMsg)
            return
        else:
            answer = message.content
            await message.delete()
            found = False
            for group in groups.groups:
                if answer == group.name:
                    found = True
                    group.members.remove("<@!"+str(ctx.author.id)+">")
                    embed = global_vars.defaultEmbed("✅ 成功退出小組",
                        f"小組名稱: {answer}")
                    global_vars.setFooter(embed)
                    await embedAsk.edit(embed=embed)
            if found == False:
                embed = global_vars.embedNoGroup
                global_vars.setFooter(embed)
                await embedAsk.edit(embed=embed)

def setup(bot):
    bot.add_cog(GroupCog(bot))