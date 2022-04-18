import yaml
import discord
import sys
from discord.ext import commands
import global_vars
import getpass
owner = getpass.getuser()
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
global_vars.Global()


class Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Cog(bot))
