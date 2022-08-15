from discord.ext import commands

class User:
    def __init__(self, user_id: int, bot: commands.bot) -> None:
        self.user_id = user_id
        self.bot = bot 
        self.user = None
        self.uid = None 
        self.genshin_client = None
        
    # async def fetch_data():
        