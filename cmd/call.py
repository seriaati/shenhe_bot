import discord
from discord.ext import commands

class CallCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def turtle(self, ctx):
        await ctx.send("律律🐢")

    @commands.command()
    async def rabbit(self, ctx):
        await ctx.send("可愛的🐰兔")

    @commands.command()
    async def 小雪(self, ctx):
        await ctx.send("又聰明又可愛的成熟女孩子- tedd")

    @commands.command()
    async def ttos(self, ctx):
        await ctx.send("好吃的巧克力土司")

    @commands.command()
    async def maple(self, ctx):
        await ctx.send("中學生楓")

    # @commands.command()
    # async def flow(self, ctx):
    #     await ctx.send("樂心助人又帥氣的flow哥哥")

    @commands.command()
    async def tedd(self, ctx):
        await ctx.send("沈默寡言但內心很善良也很帥氣的tedd哥哥")

    @commands.command()
    async def airplane(ctx):
        await ctx.send("✈仔")

    @commands.command()
    async def snow(self, ctx):
        await ctx.send("❄小雪國萬歲！")

def setup(bot):
    bot.add_cog(CallCog(bot))