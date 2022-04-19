import yaml
import discord
from discord.ext import commands
import asset.global_vars as Global
from asset.global_vars import defaultEmbed, setFooter


class Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Cog(bot))
