import json
from typing import Dict, List, Union

import aiofiles
import discord
from discord import ui, utils

import dev.config as config
import dev.models as models
from apps.text_map import text_map
from dev.base_ui import BaseView
from utils import divide_chunks
from utils.paginators import GeneralPaginator


class Dropdown(ui.Select):
    def __init__(self, lang: discord.Locale | str):
        options = [
            discord.SelectOption(
                label=text_map.get(487, lang), emoji="🌟", value="genshin"
            ),
            discord.SelectOption(
                label=text_map.get(488, lang),
                description=text_map.get(489, lang),
                emoji="🌠",
                value="wish",
            ),
            discord.SelectOption(
                label=text_map.get(490, lang),
                description=text_map.get(491, lang),
                emoji="<:CALCULATOR:999540912319369227>",
                value="calc",
            ),
            discord.SelectOption(
                label=text_map.get(202, lang), emoji="✅", value="todo"
            ),
            discord.SelectOption(
                label=text_map.get(494, lang), emoji="❄️", value="others"
            ),
        ]
        super().__init__(placeholder=text_map.get(495, lang), options=options)

        self.lang = lang

    async def callback(self, i: models.Inter):
        await i.response.defer()
        lang = self.lang

        cog = i.client.get_cog(self.values[0])
        if not cog:
            raise AssertionError

        selected_option = utils.get(self.options, value=self.values[0])
        if not selected_option:
            raise AssertionError

        fields: List[models.EmbedField] = []
        embeds: List[discord.Embed] = []

        async with aiofiles.open("command_map.json", "r") as f:
            command_map: Dict[str, int] = json.loads(await f.read())

        for command in cog.walk_app_commands():
            if not command._locale_description:  # skipcq: PYL-W0212
                raise AssertionError

            if cog.__cog_is_app_commands_group__:
                mention = f"</{self.values[0]} {command.name}:{command_map.get(self.values[0])}>"
            else:
                mention = f"</{command.name}:{command_map.get(command.name)}>"
            fields.append(
                models.EmbedField(
                    name=mention,
                    value=text_map.get(
                        command._locale_description.extras["hash"],  # skipcq: PYL-W0212
                        lang,
                    ),
                )
            )

        div_fields: List[List[models.EmbedField]] = list(divide_chunks(fields, 6))
        for div_field in div_fields:
            embed = models.DefaultEmbed(
                f"{selected_option.emoji} {selected_option.label}"
            )
            for field in div_field:
                embed.add_field(name=field.name, value=field.value, inline=False)
            embeds.append(embed)

        await GeneralPaginator(i, embeds, [self]).start(edit=True)


class HelpView(BaseView):
    def __init__(self, lang: Union[discord.Locale, str]):
        super().__init__(timeout=config.mid_timeout)
        self.add_item(Dropdown(lang))
