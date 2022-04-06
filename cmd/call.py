from discord.ext import commands

@commands.command()
async def turtle(ctx):
    await ctx.send("律律🐢")

@commands.command()
async def rabbit(ctx):
    await ctx.send("可愛的🐰兔")

@commands.command()
async def 小雪(ctx):
    await ctx.send("又聰明又可愛的成熟女孩子- tedd")

@commands.command()
async def ttos(ctx):
    await ctx.send("好吃的巧克力土司")

@commands.command()
async def maple(ctx):
    await ctx.send("中學生楓")

@commands.command()
async def flow(ctx):
    await ctx.send("樂心助人又帥氣的flow哥哥")

@commands.command()
async def tedd(ctx):
    await ctx.send("沈默寡言但內心很善良也很帥氣的tedd哥哥")

@commands.command()
async def airplane(ctx):
    await ctx.send("✈仔")

@commands.command()
async def snow(ctx):
    await ctx.send("❄小雪國萬歲！")

def setup(bot):
    bot.add_command(turtle)
    bot.add_command(rabbit)
    bot.add_command(小雪)
    bot.add_command(ttos)
    bot.add_command(maple)
    bot.add_command(flow)
    bot.add_command(tedd)
    bot.add_command(airplane)
    bot.add_command(snow)