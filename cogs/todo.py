from discord import Interaction, app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands

from apps.genshin.custom_model import ShenheBot
from ui.todo import TodoList


class Todo(commands.Cog, name="todo"):
    def __init__(self, bot):
        self.bot: ShenheBot = bot

    @app_commands.command(name="todo", description=_("View your todo list", hash=473))
    async def todo_list(self, i: Interaction):
        await TodoList.return_todo(i)


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(Todo(bot))
