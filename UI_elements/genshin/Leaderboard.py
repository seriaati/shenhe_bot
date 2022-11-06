import config
from UI_base_models import BaseView
from discord import Interaction, Locale
from discord.ui import Select


class View(BaseView):
    def __init__(self, locale: Locale | str):
        super().__init__(timeout=config.mid_timeout)
        self.locale = locale


class CategorySelect(Select):
    def __init__(self, locale: Locale | str):
        super().__init__(placeholder="Choose a leaderbaord category")
        
    async def callback(self, i: Interaction):
        pass

class TypeSelect(Select):
    def __init__(self, locale: Locale | str):
        super().__init__(placeholder="Choose a leaderbaord type")
        
    async def callback(self, i: Interaction):
        pass

class ChestTypeSelect(Select):
    def __init__(self, locale: Locale | str):
        super().__init__(placeholder="Choose a chest type")
        
    async def callback(self, i: Interaction):
        pass

class CharacterStatSelect(Select):
    def __init__(self, locale: Locale | str):
        super().__init__(placeholder="Choose a character stat")
        
    async def callback(self, i: Interaction):
        pass

class ArtifactSubStatSelect(Select):
    def __init__(self, locale: Locale | str):
        super().__init__(placeholder="Choose a substat")
        
    async def callback(self, i: Interaction):
        pass
    
class AbyssStatSelect(Select):
    def __init__(self, locale: Locale | str):
        super().__init__(placeholder="Choose an abyss stat")
        
    async def callback(self, i: Interaction):
        pass

class WishStatSelect(Select):
    def __init__(self, locale: Locale | str):
        super().__init__(placeholder="Choose a wish stat")
        
    async def callback(self, i: Interaction):
        pass