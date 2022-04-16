import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import discord, asyncio, yaml, uuid
import global_vars
global_vars.Global()
from discord.ext import commands
from discord.ext.forms import Form
with open(f'C:/Users/{owner}/shenhe_bot/asset/groups.yaml', encoding = 'utf-8') as file:
    groups = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/group_request.yaml', encoding = 'utf-8') as file:
    confirms = yaml.full_load(file)

class GroupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        for confirm in confirms:
            requester = self.bot.get_user(confirm['requesterID'])
            captain = self.bot.get_user(confirm['captainID'])
            if payload.message_id == confirm['msgID']:
                if payload.emoji.name == '✅':
                    for group in groups:
                        if group['name'] == confirm['groupName']:
                            group['members'].append("<@!"+str(ctx.author.id)+">")
                            with open(f'C:/Users/{owner}/shenhe_bot/asset/groups.yaml', 'w', encoding = 'utf-8') as file:
                                yaml.dump(groups, file)
                            embed = global_vars.defaultEmbed(f"✅ {requester.mention} 成功加入 {confirm['groupName']} 小組", f" ")
                            global_vars.setFooter(embed)
                            await captain.send(embed=embed)
                            embed = global_vars.defaultEmbed(f"✅ 你已成功加入 {confirm['groupName']} 小組", f" ")
                            global_vars.setFooter(embed)
                            await requester.send(embed=embed)
                            confirms.remove(confirm)
                            with open(f'C:/Users/{owner}/shenhe_bot/asset/group_request.yaml', 'w', encoding = 'utf-8') as file:
                                yaml.dump(confirms, file)
                if payload.emoji.name == '❌':
                    embed = global_vars.defaultEmbed(f"🥲 你已拒絕 {requester.mention} 加入 {confirm['groupName']} 小組", "")
                    global_vars.setFooter(embed)
                    await captain.send(embed=embed)
                    embed = global_vars.defaultEmbed(f"🥲 你已被拒絕加入 {confirm['groupName']} 小組", "")
                    global_vars.setFooter(embed)
                    await requester.send(embed=embed)
                    confirms.remove(confirm)
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/group_request.yaml', 'w', encoding = 'utf-8') as file:
                        yaml.dump(confirms, file)
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
                    formTrue = Form(ctx, '新增小組流程', cleanup=True)
                    formTrue.add_question('打算創建的小組名稱?', 'name')
                    formTrue.add_question('要加入哪些成員?(用逗號分隔: @小雪, @sueno)', 'members')
                    formTrue.edit_and_delete(True)
                    formTrue.set_timeout(60)
                    await formTrue.set_color("0xa68bd3")
                    result = await formTrue.start()
                    memberAdd = result.members.split(", ")
                    for group in groups:
                        if result.name == group['name']:
                            for member in memberAdd:
                                group['members'].append(memberAdd)
                                with open(f'C:/Users/{owner}/shenhe_bot/asset/groups.yaml', 'w', encoding = 'utf-8') as file:
                                    yaml.dump(groups, file)
                    newGroup = {'name': result.name, "members": members, "authorID": ctx.author.id}
                    groups.append(newGroup)
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/groups.yaml', 'w', encoding = 'utf-8') as file:
                        yaml.dump(groups, file)
                    embed = global_vars.defaultEmbed("✅ 小組創建成功", 
                        f"小組名稱: {result.name}")
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
                if answer == "delete":
                    groupStr = ""
                    for group in groups:
                        groupStr = groupStr + "• " + group['name'] + "\n"
                    embed = global_vars.defaultEmbed("打算刪除的小組名稱?", 
                        f"目前存在的小組: \n{groupStr}")
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
                        for group in groups:
                            if answer == group['name']:
                                found = True
                                groups.remove(group)
                                with open(f'C:/Users/{owner}/shenhe_bot/asset/groups.yaml', 'w', encoding = 'utf-8') as file:
                                    yaml.dump(groups, file)
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
                    for group in groups:
                        memberStr = ""
                        for member in group['members']:
                            memberStr = memberStr + "• " + member + "\n"
                        embed = global_vars.defaultEmbed(f"組名: {group['name']}", 
                            f"組員: \n{memberStr}")
                        global_vars.setFooter(embed)
                        await ctx.send(embed=embed)
                if answer == "add":
                    groupStr = ""
                    for group in groups:
                        groupStr = groupStr + "• " + group['name'] + "\n"
                    embed = global_vars.defaultEmbed(f"要在哪個小組新增成員?", 
                        f"目前存在的小組: \n{groupStr}")
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
                        for group in groups:
                            if answer==group['name']:
                                if group['authorID'] != ctx.author.id:
                                    embed = global_vars.defaultEmbed(f"你不是這個小組的創建人!", 
                                        f"")
                                    global_vars.setFooter(embed)
                                    await ctx.send(embed=embed)
                                    return
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
                                        group['members'].append(member)
                                        with open(f'C:/Users/{owner}/shenhe_bot/asset/groups.yaml', 'w', encoding = 'utf-8') as file:
                                            yaml.dump(groups, file)
                                    memberStr = ""
                                    for member in memberAdd:
                                        memberStr = memberStr + "• " + member + "\n"
                                    embed = global_vars.defaultEmbed("✅ 成員新增成功",
                                        f"小組名稱: {group['name']}\n新增成員:\n {memberStr}")
                                    global_vars.setFooter(embed)
                                    await ctx.send(embed=embed)
                        if found == False:
                            embed = global_vars.embedNoGroup
                            global_vars.setFooter(embed)
                            await ctx.send(embed=embed)
                if answer == "remove":
                    groupStr = ""
                    for group in groups:
                        groupStr = groupStr + "• " + group['name'] + "\n"
                    embed = global_vars.defaultEmbed("要從哪個小組中移除成員?",
                        f"目前存在的小組: \n{groupStr}")
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
                        for group in groups:
                            if answer==group['name']:
                                if group['authorID'] != ctx.author.id:
                                    embed = global_vars.defaultEmbed(f"你不是這個小組的創建人!", 
                                        f"")
                                    global_vars.setFooter(embed)
                                    await ctx.send(embed=embed)
                                    return
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
                                    for member in memberDel:
                                        group['members'].remove(member)
                                    with open(f'C:/Users/{owner}/shenhe_bot/asset/groups.yaml', 'w', encoding = 'utf-8') as file:
                                        yaml.dump(groups, file)
                                    memberStr = ""
                                    for member in memberDel:
                                        memberStr = memberStr + "• " + member + "\n"
                                    embed = global_vars.defaultEmbed(
                                        "✅ 成員移除成功",
                                        f"小組名稱: {group['name']}\n移除成員: \n{memberStr}")
                                    global_vars.setFooter(embed)
                                    await ctx.send(embed=embed)
                        if found == False:
                            embed = global_vars.embedNoGroup
                            global_vars.setFooter(embed)
                            await ctx.send(embed=embed)
                if answer == "join":
                    groupStr = ""
                    for group in groups:
                        groupStr = groupStr + "• " + group['name'] + "\n"
                    embed = global_vars.defaultEmbed("要加入哪個小組?",
                        f"目前存在的小組: \n{groupStr}")
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
                        for group in groups:
                            if answer == group['name']:
                                found = True
                                authorObj = user = self.bot.get_user(int(group['authorID']))
                                confirmMsg = await authorObj.send(f"你要讓 {ctx.author.mention} 加入 {answer} 小組嗎?")
                                await confirmMsg.add_reaction('✅')
                                await confirmMsg.add_reaction('❌')
                                newConfirm = {"msgID": confirmMsg.id, "requesterID": ctx.author.id, "captainID": group['authorID'], "groupName": group['name']}
                                with open(f'C:/Users/{owner}/shenhe_bot/asset/group_request.yaml', 'w', encoding = 'utf-8') as file:
                                    yaml.dump(requests, file)
                        if found == False:
                            embed = global_vars.embedNoGroup
                            global_vars.setFooter(embed)
                            await ctx.send(embed=embed)
                if answer == "leave":
                    groupStr = ""
                    for group in groups:
                        authorMention = "<@!"+str(ctx.author.id)+">"
                        if authorMention in group['members']:
                            groupStr = groupStr + "• " + group['name'] + "\n"
                    embed = global_vars.defaultEmbed("要退出哪個小組?", 
                        f"你目前在的小組有: \n{groupStr}")
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
                        for group in groups:
                            if answer == group['name']:
                                found = True
                                group['members'].remove("<@!"+str(ctx.author.id)+">")
                                with open(f'C:/Users/{owner}/shenhe_bot/asset/groups.yaml', 'w', encoding = 'utf-8') as file:
                                    yaml.dump(groups, file)
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
    async def list(self, ctx):
        for group in groups:
            memberStr = ""
            for member in group['members']:
                memberStr = memberStr + "• " + member + "\n"
            embedList = global_vars.defaultEmbed(f"組名: {group['name']}", f"組員: \n{memberStr}")
            global_vars.setFooter(embedList)
            await ctx.send(embed=embedList)

def setup(bot):
    bot.add_cog(GroupCog(bot))