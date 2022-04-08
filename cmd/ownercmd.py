import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import discord, asyncio, yaml
import global_vars
global_vars.Global()
from discord.ext import commands

with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', encoding = 'utf-8') as file:
    users = yaml.full_load(file)

class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, arg):
        self.bot.reload_extension(f"cmd.{arg}")
        await ctx.send(f"已重整 {arg} 指令包")

    @commands.command()
    @commands.is_owner()
    async def newuser(self, ctx):
        await ctx.send("原神uid?")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            message = await self.bot.wait_for('message', 
                timeout= 30.0, 
                check= check) #等待答案，最多30秒
        except asyncio.TimeoutError:
            await ctx.send(global_vars.timeOutErrorMsg) #傳送錯誤訊息（超過30秒
            return
        else:
            uid = message.content
            await message.delete()
            await ctx.send("ltuid?")
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            try:
                message = await self.bot.wait_for('message', 
                    timeout= 30.0, 
                    check= check) #等待答案，最多30秒
            except asyncio.TimeoutError:
                await ctx.send(global_vars.timeOutErrorMsg) #傳送錯誤訊息（超過30秒
                return
            else:
                ltuid = message.content
                await message.delete()
                await ctx.send("ltoken?")
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                try:
                    message = await self.bot.wait_for('message', 
                        timeout= 30.0, 
                        check= check) #等待答案，最多30秒
                except asyncio.TimeoutError:
                    await ctx.send(global_vars.timeOutErrorMsg) #傳送錯誤訊息（超過30秒
                    return
                else:
                    ltoken = message.content
                    await messaage.delete()
                    await ctx.send("用戶名?")
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel
                    try:
                        message = await self.bot.wait_for('message', 
                            timeout= 30.0, 
                            check= check) #等待答案，最多30秒
                    except asyncio.TimeoutError:
                        await ctx.send(global_vars.timeOutErrorMsg) #傳送錯誤訊息（超過30秒
                        return
                    else:
                        name = message.content
                        await message.delete()
                        await ctx.send("discord ID?")
                        def check(m):
                            return m.author == ctx.author and m.channel == ctx.channel
                        try:
                            message = await self.bot.wait_for('message', 
                                timeout= 30.0, 
                                check= check) #等待答案，最多30秒
                        except asyncio.TimeoutError:
                            await ctx.send(global_vars.timeOutErrorMsg) #傳送錯誤訊息（超過30秒
                            return
                        else:
                            discordID = message.content
                            await message.delete()
                            await ctx.send(f"正確?\nuid: {uid}\nltuid: {ltuid}\nltoken: {ltoken}\nusername: {name}\ndiscordID: {discordID}")
                            try:
                                message = await self.bot.wait_for('message', 
                                    timeout= 30.0, 
                                    check= check) #等待答案，最多30秒
                            except asyncio.TimeoutError:
                                await ctx.send(global_vars.timeOutErrorMsg) #傳送錯誤訊息（超過30秒
                                return
                            else:
                                answer = message.content
                                await message.delete()
                                if answer == "yes":
                                    newUser = {'name': name, 'discordID': discordID, 'ltoken': ltoken, 'ltuid': ltuid, 'dm': True, 'dmCount': 0}
                                    users.append(newUser)
                                    with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', 'w', encoding = 'utf-8') as file:
                                        yaml.dump(users, file)
                                    await ctx.send("已新增")
                                else:
                                    await ctx.send("已退出")
                                    return

def setup(bot):
    bot.add_cog(OwnerCog(bot))