import aiosqlite
from utility.apps.text_map.TextMap import text_map
from utility.apps.text_map.utils import get_user_locale
from debug import DefaultView
from typing import Any, Dict
from discord import ButtonStyle, Embed, Interaction, Locale, Member, SelectOption
from discord.ui import Select, Button
from data.game.GOModes import hitModes
from enkanetwork import EnkaNetworkResponse
from pyppeteer.browser import Browser

from utility.utils import calculateDamage, default_embed, error_embed, getCharacter

class View(DefaultView):
    def __init__(self, embeds: Dict[int, Embed], artifact_embeds: dict[int, Embed], character_options: list[SelectOption], data: EnkaNetworkResponse, browser: Browser, eng_data: EnkaNetworkResponse, author: Member, db: aiosqlite.Connection, locale: Locale, user_locale: str):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.artifact_embeds = artifact_embeds
        self.character_options = character_options
        self.character_id = None
        self.browser = browser
        self.author = author
        self.data = data
        self.eng_data = eng_data
        self.db = db
        self.add_item(ViewArtifacts(text_map.get(92, locale, user_locale)))
        self.add_item(CalculateDamageButton())
        self.add_item(PageSelect(character_options, text_map.get(157, locale, user_locale)))
        self.children[0].disabled = True
        self.children[1].disabled = True

    async def interaction_check(self, i: Interaction) -> bool:
        user_locale = await get_user_locale(i.user.id, self.db)
        if self.author.id != i.user.id:
            await i.response.send_message(embed=error_embed().set_author(name=text_map.get(143, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        return self.author.id == i.user.id

class PageSelect(Select):
    def __init__(self, character_options: list[SelectOption], plceholder: str):
        super().__init__(placeholder=plceholder, options=character_options)

    async def callback(self, i: Interaction) -> Any:
        disabled = True if self.values[0] == '0' else False
        self.view.children[0].disabled = disabled
        self.view.children[1].disabled = disabled
        self.view.character_id = self.values[0]
        await i.response.edit_message(embed=self.view.embeds[self.values[0]], view=self.view)

class ViewArtifacts(Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=ButtonStyle.blurple)

    async def callback(self, i: Interaction) -> Any:
        self.disabled = True
        await i.response.edit_message(embed=self.view.artifact_embeds[self.view.character_id], view=self.view)

class CalculateDamageButton(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.blurple, label='計算傷害', disabled=True)

    async def callback(self, i: Interaction) -> Any:
        view = DamageCalculator(self.view)
        reactionMode_elements = ['Pyro', 'Cryo', 'Hydro', 'pyro', 'cryo']
        for item in view.children:
            item.disabled = True
        view.children[0].disabled = False
        await i.response.edit_message(embed=default_embed('<a:LOADER:982128111904776242> 計算傷害中', '約需 5 至 10 秒'), view=view)
        embed = await calculateDamage(self.view.eng_data, self.view.browser, self.view.character_id, 'critHit', i.user)
        for item in view.children:
            item.disabled = False
        view.children[4].disabled = True
        character_element = getCharacter(self.view.character_id)['element']
        if character_element in reactionMode_elements or view.infusionAura in reactionMode_elements:
            view.children[4].disabled = False
        await i.edit_original_message(embed=embed, view=view)

class DamageCalculator(DefaultView):
    def __init__(self, enka_view: View):
        super().__init__(timeout=None)
        # defining damage calculation variables
        self.enka_view = enka_view
        self.hitMode = 'critHit'
        self.reactionMode = ''
        self.infusionAura = ''
        self.team = []

        # producing select options
        reactionMode_options = [SelectOption(label='無反應', value='none')]
        element = getCharacter(self.enka_view.character_id)['element']
        if element == 'Cryo' or self.infusionAura == 'cryo':
            reactionMode_options.append(
                SelectOption(label='融化', value='cryo_melt'))
        elif element == 'Pyro' or self.infusionAura == 'pyro':
            reactionMode_options.append(SelectOption(
                label='蒸發', value='pyro_vaporize'))
            reactionMode_options.append(
                SelectOption(label='融化', value='pyro_melt'))
        elif element == 'Hydro':
            reactionMode_options.append(SelectOption(
                label='蒸發', value='hydro_vaporize'))

        team_options = []
        option: SelectOption
        for option in self.enka_view.character_options:
            if str(option.value) == str(self.enka_view.character_id):
                continue
            team_options.append(SelectOption(
                label=option.label, value=option.value, emoji=option.emoji))
        del team_options[0]

        # adding items
        self.add_item(GoBack())
        for index in range(0, 3):
            self.add_item(HitMode(index))
        self.add_item(ReactionMode(reactionMode_options))
        self.add_item(InfusionAura())
        if len(team_options) >= 1:
            self.add_item(TeamSelect(team_options))

    async def interaction_check(self, i: Interaction) -> bool:
        user_locale = await get_user_locale(i.user.id, self.enka_view.db)
        if self.enka_view.author.id != i.user.id:
            await i.response.send_message(embed=error_embed(message='指令: `/profile`').set_author(name=text_map.get(143, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        return self.enka_view.author.id == i.user.id

class GoBack(Button):
    def __init__(self):
        super().__init__(emoji='<:left:982588994778972171>')

    async def callback(self, i: Interaction):
        for item in self.view.enka_view.children:
            item.disabled = False
        await i.response.edit_message(embed=self.view.enka_view.embeds[self.view.enka_view.character_id], view=self.view.enka_view)

class HitMode(Button):
    def __init__(self, index: int):
        super().__init__(style=ButtonStyle.blurple,
                            label=(list(hitModes.values())[index]))
        self.index = index

    async def callback(self, i: Interaction) -> Any:
        self.view.hitMode = (list(hitModes.keys()))[self.index]
        await returnDamage(self.view, i)

class ReactionMode(Select):
    def __init__(self, options: list[SelectOption]):
        super().__init__(placeholder='選擇元素反應', options=options)

    async def callback(self, i: Interaction) -> Any:
        self.view.reactionMode = '' if self.values[0] == 'none' else self.values[0]
        await returnDamage(self.view, i)

class InfusionAura(Select):
    def __init__(self):
        options = [SelectOption(label='無附魔', value='none'), SelectOption(
            label='火元素附魔', description='班尼特六命', value='pyro'), SelectOption(label='冰元素附魔', description='重雲E', value='cryo')]
        super().__init__(placeholder='選擇近戰元素附魔', options=options)

    async def callback(self, i: Interaction) -> Any:
        self.view.infusionAura = '' if self.values[0] == 'none' else self.values[0]
        await returnDamage(self.view, i)

class TeamSelect(Select):
    def __init__(self, options):
        super().__init__(placeholder='選擇隊友', options=options,
                            max_values=3 if len(options) >= 3 else len(options))

    async def callback(self, i: Interaction) -> Any:
        self.view.team = self.values
        await returnDamage(self.view, i)
        
async def returnDamage(view: DamageCalculator, i: Interaction):
    for item in view.children:
        item.disabled = True
    view.children[0].disabled = False
    await i.response.edit_message(embed=default_embed('<a:LOADER:982128111904776242> 計算中', '約需 5 至 10 秒'), view=view)
    embed = await calculateDamage(view.enka_view.eng_data, view.enka_view.browser, view.enka_view.character_id, view.hitMode, i.user, view.reactionMode, view.infusionAura, view.team, )
    for item in view.children:
        item.disabled = False
    reactionMode_disabled = True
    character_element = getCharacter(
        view.enka_view.character_id)['element']
    reactionMode_elements = ['Pyro', 'Cryo', 'Hydro', 'pyro', 'cryo']
    if character_element in reactionMode_elements or view.infusionAura in reactionMode_elements:
        reactionMode_disabled = False
    view.children[4].disabled = reactionMode_disabled
    await i.edit_original_message(embed=embed, view=view)