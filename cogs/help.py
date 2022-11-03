from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseView
from discord import Interaction, Locale, SelectOption, app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands
from discord.ui import Select
from utility.utils import default_embed


class Dropdown(Select):
    def __init__(self, bot: commands.Bot, locale: Locale, user_locale: str | None):
        options = [
            SelectOption(label=text_map.get(487, locale, user_locale),
                         emoji='🌟'),
            SelectOption(label=text_map.get(488, locale, user_locale),
                         description=text_map.get(489, locale, user_locale),
                         emoji='🌠'),
            SelectOption(label=text_map.get(490, locale, user_locale),
                         description=text_map.get(491, locale, user_locale),
                         emoji='<:CALCULATOR:999540912319369227>'),
            SelectOption(label=text_map.get(202, locale, user_locale),
                         emoji='✅'),
            SelectOption(label=text_map.get(494, locale, user_locale),
                         emoji='❄️'),
        ]
        super().__init__(placeholder=text_map.get(495, locale, user_locale), options=options)
        self.bot = bot

    async def callback(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        cogs = ['genshin', 'wish', 'calc', 'todo', 'others']
        for index, option in enumerate(self.options):
            if option.value == self.values[0]:
                selected_option = option
                index = index
                break
        command_cog = self.bot.get_cog(cogs[index])
        commands = command_cog.__cog_app_commands__
        is_group = command_cog.__cog_is_app_commands_group__
        group_name = command_cog.__cog_group_name__
        app_commands = await self.bot.tree.fetch_commands()
        app_command_dict = {}
        for app_command in app_commands:
            app_command_dict[app_command.name] = app_command.id
            
        embed = default_embed(
            f'{selected_option.emoji} {selected_option.label}')
        for command in commands:
            try:
                hash = command._locale_description.extras['hash']
            except KeyError:
                value = command.description
            else:
                value = ''
                try:
                    value = text_map.get(hash, i.locale, user_locale)
                except (ValueError, KeyError):
                    value = command.description
            if is_group:
                embed.add_field(
                    name=f'</{group_name} {command.name}:{app_command_dict[group_name]}>',
                    value=value
                )
            else:
                embed.add_field(
                    name=f'</{command.name}:{app_command_dict[command.name]}>',
                    value=value
                )
        await i.response.send_message(embed=embed, ephemeral=True)


class DropdownView(BaseView):
    def __init__(self, bot: commands.Bot, locale: Locale, user_locale: str | None):
        super().__init__()
        self.add_item(Dropdown(bot, locale, user_locale))


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help', description=_("Get an overview of shenhe's commands", hash=486))
    async def help(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        view = DropdownView(self.bot, i.locale, user_locale)
        await i.response.send_message(view=view)
        view.message = await i.original_response()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
