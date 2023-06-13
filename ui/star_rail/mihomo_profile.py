from typing import List
from apps.db.tables.user_settings import Settings
from apps.draw.main_funcs import draw_hsr_profile_card_v1
from apps.text_map import text_map, MIHOMO_LANGS
from dev.base_ui import BaseSelect, BaseView
from dev.config import mid_timeout
from dev.asset import overview_emoji, trailblazer_ids
from dev.models import DefaultEmbed, DrawInput, Inter
from discord import ui
import discord
import mihomo


class View(BaseView):
    def __init__(self):
        super().__init__(timeout=mid_timeout)
        self.uid: int
        self.data: mihomo.StarrailInfoParsed
        self.lang: str

    async def start(self, i: Inter, uid: int, lang: str):
        self.author = i.user
        self.uid = uid
        self.lang = lang

        mihomo_lang = MIHOMO_LANGS.get(lang, mihomo.Language.EN)
        client = mihomo.MihomoAPI(mihomo_lang)
        self.data = await client.fetch_user(uid, replace_icon_name_with_url=True)

        self.add_components()
        embed = self.make_player_embed()
        await i.followup.send(embed=embed, view=self)
        self.message = await i.original_response()

    def make_player_embed(self) -> DefaultEmbed:
        player = self.data.player
        embed = DefaultEmbed(player.name)
        if player.signature:
            embed.description = player.signature

        embed.add_field(name="UID", value=str(player.uid))
        embed.add_field(name=text_map.get(794, self.lang), value=str(player.level))
        embed.add_field(name=text_map.get(795, self.lang), value=player.world_level)
        embed.set_thumbnail(url=self.data.player.avatar.icon)

        return embed

    def add_components(self):
        self.add_item(OverviewButton(text_map.get(43, self.lang)))
        options: List[discord.SelectOption] = []
        for c in self.data.characters:
            name = (
                c.name if c.id not in trailblazer_ids else text_map.get(793, self.lang)
            )
            options.append(discord.SelectOption(label=name, value=str(c.id)))
        self.add_item(CharacterSelect(text_map.get(157, self.lang), options))


class OverviewButton(ui.Button):
    def __init__(self, label: str):
        super().__init__(
            style=discord.ButtonStyle.blurple, label=label, emoji=overview_emoji, row=0
        )
        self.view: View

    async def callback(self, i: Inter):
        embed = self.view.make_player_embed()
        await i.response.edit_message(embed=embed, attachments=[])


class CharacterSelect(BaseSelect):
    def __init__(self, placeholder: str, options: List[discord.SelectOption]):
        super().__init__(placeholder=placeholder, options=options, row=1)
        self.view: View

    async def callback(self, i: Inter):
        await self.loading(i)
        character_id = self.values[0]
        character = discord.utils.get(self.view.data.characters, id=character_id)
        if character is None:
            raise ValueError(f"Character with id {character_id} not found")

        dark_mode = await i.client.db.settings.get(i.user.id, Settings.DARK_MODE)
        draw_input = DrawInput(
            i.client.loop, i.client.session, self.view.lang, dark_mode
        )
        bytes_obj = await draw_hsr_profile_card_v1(draw_input, character)

        bytes_obj.seek(0)
        file = discord.File(bytes_obj, filename="card.png")
        self.options = self.original_options
        await i.edit_original_response(embed=None, attachments=[file], view=self.view)
