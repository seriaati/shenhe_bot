import getpass

owner = getpass.getuser()
import sys

sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import discord
import global_vars
import yaml

global_vars.Global()
from discord.ext import commands


class FlowGiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(FlowGiveawayCog(bot))
