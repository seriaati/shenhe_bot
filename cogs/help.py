import json
from typing import Dict

import aiofiles
from discord import Interaction, Locale, SelectOption, app_commands, utils
from discord.app_commands import locale_str as _
from discord.ext import commands
from discord.ui import Select

import config
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseView
from utility.utils import DefaultEmbed


class Dropdown(Select):
    def __init__(self, locale: Locale | str):
        options = [
            SelectOption(label=text_map.get(487, locale), emoji="🌟", value="genshin"),
            SelectOption(
                label=text_map.get(488, locale),
                description=text_map.get(489, locale),
                emoji="🌠",
                value="wish",
            ),
            SelectOption(
                label=text_map.get(490, locale),
                description=text_map.get(491, locale),
                emoji="<:CALCULATOR:999540912319369227>",
                value="calc",
            ),
            SelectOption(label=text_map.get(202, locale), emoji="✅", value="todo"),
            SelectOption(label=text_map.get(494, locale), emoji="❄️", value="others"),
        ]
        super().__init__(placeholder=text_map.get(495, locale), options=options)

        self.locale = locale

    async def callback(self, i: Interaction):
        locale = self.locale

        bot: commands.Bot = i.client  # type: ignore
        cog = bot.get_cog(self.values[0])
        assert cog

        selected_option = utils.get(self.options, value=self.values[0])
        assert selected_option
        embed = DefaultEmbed(f"{selected_option.emoji} {selected_option.label}")

        async with aiofiles.open("command_map.json", "r") as f:
            command_map: Dict[str, int] = json.loads(await f.read())

        for command in cog.walk_app_commands():
            assert command._locale_description

            if cog.__cog_is_app_commands_group__:
                mention = f"</{self.values[0]} {command.name}:{command_map.get(self.values[0])}>"
            else:
                mention = f"</{command.name}:{command_map.get(command.name)}>"
            embed.add_field(
                name=mention,
                value=text_map.get(command._locale_description.extras["hash"], locale),
                inline=False,
            )

        await i.response.edit_message(embed=embed)


class DropdownView(BaseView):
    def __init__(self, locale: Locale | str):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(Dropdown(locale))


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help", description=_("View a list of all commands", hash=486)
    )
    async def help(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, i.client.pool)  # type: ignore
        view = DropdownView(user_locale or i.locale)
        await i.response.send_message(view=view)
        view.message = await i.original_response()


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(HelpCog(bot))
