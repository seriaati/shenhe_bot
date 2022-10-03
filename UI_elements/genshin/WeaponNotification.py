from typing import List
from UI_base_models import BaseView
import config
from discord.ui import Button, Select
from discord import SelectOption, Interaction

class View(BaseView):
    def __init__(self):
        super().__init__(timeout=config.mid_timeout)

class GOBackReminder(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>", row=2)
    
    async def callback(self, i: Interaction):
        pass

class GOBack(Button):
    def __init__(self):
        super().__init__(emoji="<:left:982588994778972171>", row=2)
    
    async def callback(self, i: Interaction):
        pass


class WeaponTypeButton(Button):
    def __init__(self, emoji: str, label: str, weapon_type: str):
        super().__init__(emoji=emoji, label=label)
        self.weapon_type = weapon_type
        
    async def callback(self, i: Interaction):
        pass

class WeaponSelect(Select):
    def __init__(self, options: List[SelectOption]):
        super().__init__(options=options)
        
    async def callback(self, i: Interaction):
        pass
    
async def return_weapon_notification_embed(i: Interaction):
    pass