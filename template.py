from discord.ext import commands


class Cog(commands.Cog, name='name', description='desc'):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Cog(bot))
