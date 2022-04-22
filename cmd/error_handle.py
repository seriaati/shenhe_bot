import sys
import traceback
import genshin

import discord
from discord.ext import commands

from cmd.asset.global_vars import defaultEmbed, errEmbed


class CommandErrorHandler(commands.Cog, name='err_handle', description='錯誤處理器', hidden=True):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return
        ignored = (commands.CommandNotFound, )
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send(f'{ctx.command} 已被小雪關閉')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f'{ctx.command} 無法在私訊中使用')
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == 'tag list':
                await ctx.send('找不到該使用者, 請重新確認')

        elif isinstance(error, commands.MissingRole):
            await ctx.send("你不是小雪團隊的一員!")

        elif isinstance(error, genshin.AlreadyClaimed):
            pass

        else:
            foo = traceback.format_exception(type(error), error, error.__traceback__)
            print("".join(foo))
            embed = errEmbed(f"指令錯誤: {ctx.command}",
            f'```{type(error).__name__}: {error}```\n'
            '如果你見到這個畫面, 請將輸入的指令與上方的錯誤私訊給小雪')
            await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def do_repeat(self, ctx, *, inp: str):
        await ctx.send(inp)

    @do_repeat.error
    async def do_repeat_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'inp':
                await ctx.send("You forgot to give me input to repeat!")


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
