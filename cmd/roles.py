import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import discord, asyncio
import global_vars
global_vars.Global()
from discord.ext import commands

class RolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roles(self, ctx):
        channel = self.bot.get_channel(962311051683192842)
        text = "test"
        message = await channel.send(text)
        await message.add_reaction('🍞')

def setup(bot):
    bot.add_cog(RolesCog(bot))