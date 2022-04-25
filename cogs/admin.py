import git
from discord.ext import commands
from pathlib import Path
from os.path import dirname
from utility.utils import log


class AdminCommands(commands.Cog, name='admin', description='管理員指令'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden = True)
    @commands.has_role("小雪團隊")
    async def pull(self, ctx):
        project_root = dirname(dirname(__file__))
        g = git.cmd.Git(project_root)
        g.pull()
        print(log(True, False, 'Pull', 'Pulled from github'))
        await ctx.send("已從源碼更新")

def setup(bot):
    bot.add_cog(AdminCommands(bot))
