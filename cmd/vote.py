import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import discord, asyncio
import global_vars
import accounts
from discord.ext import commands
global_vars.Global()

class VoteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def vote(self, ctx):
        options = []
        emojis = []
        embedAsk = global_vars.defaultEmbed("是關於什麼的投票?", 
            "例如: ceye的頭像要用什麼")
        global_vars.setFooter(embedAsk)
        embedAsk = await ctx.send(embed=embedAsk)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            message = await self.bot.wait_for('message', 
                timeout= 30.0, 
                check= check)
        except asyncio.TimeoutError:
            await ctx.send(global_vars.timeOutErrorMsg)
            return
        else:
            question = message.content
            await message.delete()
            done = False
            while done == False:
                embed = global_vars.defaultEmbed("請輸入投票的選項，當完成時，請打done", 
                    "例如: 看牙醫的胡桃")
                global_vars.setFooter(embed)
                await embedAsk.edit(embed=embed)
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                try:
                    message = await self.bot.wait_for('message', 
                        timeout= 30.0, 
                        check= check)
                except asyncio.TimeoutError:
                    await ctx.send(global_vars.timeOutErrorMsg)
                    return
                else:
                    option = message.content
                    await message.delete()
                    if option == "done":
                        done = True
                    else:
                        done = False
                        options.append(option)
                        embed = global_vars.defaultEmbed("該選項要使用什麼表情符號來代表?", 
                            "註: 只能使用此群組所擁有的表情符號\n如要新增表情符號，請告知Tedd")
                        global_vars.setFooter(embed)
                        await embedAsk.edit(embed=embed)
                        def check(m):
                            return m.author == ctx.author and m.channel == ctx.channel
                        try:
                            message = await self.bot.wait_for('message', 
                                timeout= 30.0, 
                                check= check)
                        except asyncio.TimeoutError:
                            await ctx.send(global_vars.timeOutErrorMsg)
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

def setup(bot):
    bot.add_cog(VoteCog(bot))