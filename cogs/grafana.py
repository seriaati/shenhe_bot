from discord.ext.prometheus import PrometheusCog
from discord.ext import commands

class GrafanaCog(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(PrometheusCog(bot, port=7654))