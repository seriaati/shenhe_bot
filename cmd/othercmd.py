import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import global_vars
global_vars.Global()
import yaml, discord
from discord.ext import commands
from random import randint

with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', encoding = 'utf-8') as file:
    users = yaml.full_load(file)

class OtherCMDCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    async def ping(self, ctx):
        await ctx.send('🏓 Pong! {0}ms'.format(round(self.bot.latency, 1)))

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
    async def marry(self, ctx, arg1, arg2):
        if type(arg1) == discord.Member and type(arg2) != discord.Member:
            mention = arg1.mention
            embed = global_vars.defaultEmbed(f"{mention} ❤ {arg2}","")
        elif type(arg2) == discord.Member and type(arg1) != discord.Member:
            mention = arg2.mention
            embed = global_vars.defaultEmbed(f"{arg1} ❤ {mention}","")
        else:
            embed = global_vars.defaultEmbed(f"{arg1} ❤ {arg2}","")
        global_vars.setFooter(embed)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(OtherCMDCog(bot))