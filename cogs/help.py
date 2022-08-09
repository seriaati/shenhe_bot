from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from debug import DefaultView
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
            SelectOption(label=text_map.get(492, locale, user_locale),
                         emoji='✅'),
            SelectOption(label=text_map.get(493, locale, user_locale),
                         emoji='2️⃣'),
            SelectOption(label=text_map.get(494, locale, user_locale),
                         emoji='❄️'),
        ]
        super().__init__(placeholder=text_map.get(495, locale, user_locale), options=options)
        self.bot = bot

    async def callback(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        cogs = ['genshin', 'wish', 'calc', 'todo', 'waifu', 'others']
        for index, option in enumerate(self.options):
            if option.value == self.values[0]:
                selected_option = option
                index = index
                break
        embed = default_embed(
            f'{selected_option.emoji} {selected_option.label}', selected_option.description)
        commands = self.bot.get_cog(cogs[index]).__cog_app_commands__
        for command in commands:
            if len(command.checks) != 0:
                continue
            hash = command._locale_description.extras['hash']
            value = ''
            try:
                value = text_map.get(hash, i.locale, user_locale)
            except (ValueError, KeyError):
                value = command.description
            embed.add_field(
                name=f'`/{command.name}`',
                value=value
            )
        await i.response.send_message(embed=embed, ephemeral=True)


class DropdownView(DefaultView):
    def __init__(self, bot: commands.Bot, locale: Locale, user_locale: str | None):
        super().__init__()
        self.add_item(Dropdown(bot, locale, user_locale))


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help', description=_("Get an overview of shenhe commands", hash=486))
    async def help(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        view = DropdownView(self.bot, i.locale, user_locale)
        await i.response.send_message(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
