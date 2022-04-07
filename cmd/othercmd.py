import global_vars
global_vars.Global()
from discord.ext import commands
from random import randint

class OtherCMDCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def cute(self, ctx, arg):
        string = arg
        await ctx.send(f"{string}真可愛~❤")

    @commands.command()
    async def say(self, ctx, * , name='', msg=''):
        await ctx.message.delete()
        await ctx.send(f"{name} {msg}")

    @commands.command()
    async def flash(self, ctx):
        await ctx.send("https://media.discordapp.net/attachments/823440627127287839/960177992942891038/IMG_9555.jpg")

    @commands.command()
    async def randnumber(self, ctx, arg1, arg2):
        value = randint(int(arg1), int(arg2))
        await ctx.send(str(value))

    @commands.command()
    async def dm(self, ctx):
        embed = global_vars.defaultEmbed("什麼是私訊提醒功能？","申鶴每一小時會檢測一次你的樹脂數量，當超過140的時候，\n申鶴會私訊提醒你，最多提醒三次\n註: 只有已註冊的用戶能享有這個功能")
        global_vars.setFooter(embed)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(OtherCMDCog(bot))