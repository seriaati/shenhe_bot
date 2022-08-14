from typing import Any
from discord import Interaction
from debug import DefaultView
from discord.ui import Button
from utility.utils import default_embed

class View(DefaultView):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button())
        
class Button(Button):
    def __init__(self):
        super().__init__(emoji='📜', label='更新身份組', custom_id='give_update_role')
    
    async def callback(self, i: Interaction) -> Any:
        role = i.guild.get_role(1006906916678684752)
        if role in i.user.roles:
            await i.user.remove_roles(role)
        else:
            await i.user.add_roles(role)
        embed = default_embed('身份組 Roles', f'{role.mention}: {len(role.members)}')
        await i.response.edit_message(embed=embed)