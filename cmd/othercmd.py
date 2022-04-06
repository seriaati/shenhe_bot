from discord.ext import commands

@commands.command()
async def cute(ctx, arg):
    string = arg
    await ctx.send(f"{string}真可愛~❤")

@commands.command()
async def say(ctx, * , name='', msg=''):
    await ctx.message.delete()
    await ctx.send(f"{name} {msg}")

@commands.command()
async def flash(ctx):
    await ctx.send("https://media.discordapp.net/attachments/823440627127287839/960177992942891038/IMG_9555.jpg")

def setup(bot):
    bot.add_command(cute)
    bot.add_command(say)
    bot.add_command(flash)