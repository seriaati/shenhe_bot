from discord import Interaction, app_commands
from discord.ext import commands
from apps.text_map.utils import get_user_locale
from UI_elements.todo import TodoList
from apps.todo import get_todo_embed
from discord.app_commands import locale_str as _


class Todo(commands.Cog, name='todo'):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='todo', description=_('View your todo list', hash=473))
    async def todo_list(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        embed, disabled = await get_todo_embed(self.bot.db, i.user, i.locale)
        view = TodoList.View(self.bot.db, disabled,
                             i.user, i.locale, user_locale)
        await i.response.send_message(embed=embed, view=view)
        view.message = await i.original_response()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Todo(bot))
