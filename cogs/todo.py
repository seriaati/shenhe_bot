from discord import Interaction, app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands

from apps.genshin.custom_model import ShenheBot
from apps.text_map.utils import get_user_locale
from apps.todo.todo_app import get_todo_embed, return_todo
from UI_elements.todo import TodoList


class Todo(commands.Cog, name="todo"):
    def __init__(self, bot):
        self.bot: ShenheBot = bot

    @app_commands.command(name="todo", description=_("View your todo list", hash=473))
    async def todo_list(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        result, disabled = await get_todo_embed(
            self.bot.db, i.user, i.locale, self.bot.session
        )
        view = TodoList.View(self.bot.db, disabled, i.user, i.locale, user_locale)
        await return_todo(result, i, view, self.bot.db)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Todo(bot))
