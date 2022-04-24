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
    async def reload(self, ctx, arg):
        project_root = dirname(dirname(__file__))
        g = git.cmd.Git(project_root)
        g.pull()
        await ctx.send("已從源碼更新")
        if arg == 'all':
            for filepath in Path('./cogs').glob('**/*.py'):
                cog_name = Path(filepath).stem
                try:
                    self.bot.reload_extension(f'cmd.{cog_name}')
                    await ctx.send(f"已重整 {cog_name} 指令包")
                    print(log(True, 'Cog', f'Reloaded {cog_name} cog'))
                    
                except Exception as e:
                    await ctx.send(f"{cog_name}發生錯誤```{e}```")
                    print(log(True, True,'Cog', f'{cog_name} cannot be reloaded'))
                    print(e)
        else:
            for filepath in Path('./cogs').glob('**/*.py'):
                cog_name = Path(filepath).stem
                if arg == cog_name:
                    try:
                        self.bot.reload_extension(f'cmd.{cog_name}')
                        await ctx.send(f"已重整 {cog_name} 指令包")
                        print(log(True, False,'Cog', f'Reloaded {cog_name} cog'))
                    except Exception as e:
                        await ctx.send(f"{cog_name}發生錯誤```{e}```")
                        print(log(True, True,'Cog', f'{cog_name} cannot be reloaded'))
                        print(e)


def setup(bot):
    bot.add_cog(AdminCommands(bot))
