# shenhe-bot by seria

import discord
import git
from discord.ext import commands
from utility.config import config
from utility.utils import log
from pathlib import Path

print("main or dev?")
user = input()
if user == "main":
    token = config.main
    prefix = ['!', '！']
    guild = 916838066117824553
    application_id = 956049912699715634
else:
    token = config.dev
    prefix = ['%']
    guild = 778804551972159489
    application_id = 957621570128449626

# 前綴, token, intents
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True

class ShenheBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=prefix,
            intents=intents,
            application_id=application_id
        )

    async def setup_hook(self) -> None:
        await self.load_extension('jishaku')
        for filepath in Path('./cogs').glob('**/*.py'):
            cog_name = Path(filepath).stem
            await self.load_extension(f'cogs.{cog_name}')
            print(log(True, False,'Cog', f'Loaded {cog_name}'))
        if guild != None:
            test_guild = discord.Object(id=guild)
            self.tree.clear_commands(guild=test_guild)
            # await self.tree.sync()

    async def on_ready(self):
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name=f'輸入斜線來查看所有指令')
        )
        print(log(True, False, 'Bot', 'Logged in as {0.user}'.format(self)))

    async def on_message(self, message):
        await self.process_commands(message)

bot = ShenheBot()
bot.run(token)