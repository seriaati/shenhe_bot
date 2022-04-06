from discord.ext import commands

@commands.command()
async def cmd(ctx):
    await ctx.send("cmd_package")

def setup(bot):
    bot.add_command(cmd)