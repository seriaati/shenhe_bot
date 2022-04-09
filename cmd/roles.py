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
        embed = global_vars.defaultEmbed("請選擇你的世界等級", " ")
        global_vars.setFooter(embed)
        message = await channel.send(embed=embed)
        await message.add_reaction('1️⃣')
        await message.add_reaction('2️⃣')
        await message.add_reaction('3️⃣')
        await message.add_reaction('4️⃣')
        await message.add_reaction('5️⃣')
        await message.add_reaction('6️⃣')
        await message.add_reaction('7️⃣')
        await message.add_reaction('8️⃣')

def setup(bot):
    bot.add_cog(RolesCog(bot))