from discord.ext import commands
from utility.utils import log


class CallCog(commands.Cog, name='call', description='呼叫相關'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help='呼叫律律')
    async def turtle(self, ctx):
        print(log(False, False, 'Call', f'{ctx.author} used command !turtle'))
        await ctx.send("律律🐢")

    @commands.command(help='呼叫兔兔')
    async def rabbit(self, ctx):
        print(log(False, False, 'Call', f'{ctx.author} used command !rabbit'))
        await ctx.send("可愛的🐰兔")

    @commands.command(help='呼叫小雪')
    async def 小雪(self, ctx):
        print(log(False, False, 'Call', f'{ctx.author} used command !小雪'))
        await ctx.send("又聰明又可愛的成熟女孩子- tedd")

    @commands.command(help='呼叫土司')
    async def ttos(self, ctx):
        print(log(False, False, 'Call', f'{ctx.author} used command !ttos'))
        await ctx.send("好吃的巧克力土司")

    @commands.command(help='呼叫楓')
    async def maple(self, ctx):
        print(log(False, False, 'Call', f'{ctx.author} used command !maple'))
        await ctx.send("可愛的楓！")

    @commands.command(help='呼叫tedd')
    async def tedd(self, ctx):
        print(log(False, False, 'Call', f'{ctx.author} used command !tedd'))
        await ctx.send("沈默寡言但內心很善良也很帥氣的tedd哥哥")

    @commands.command(help='呼叫飛機仔')
    async def airplane(ctx):
        print(log(False, False, 'Call',
              f'{ctx.author} used command !airplane'))
        await ctx.send("✈仔")

    @commands.command(help='小雪國萬歲!')
    async def snow(self, ctx):
        print(log(False, False, 'Call', f'{ctx.author} used command !snow'))
        await ctx.send("❄小雪國萬歲！")

    @commands.command(help='呼叫小羽')
    async def 小羽(self, ctx):
        print(log(False, False, 'Call', f'{ctx.author} used command !小羽'))
        await ctx.send("可愛的小羽！")


def setup(bot):
    bot.add_cog(CallCog(bot))
