# shenhe-bot by seria

from pathlib import Path

import aiosqlite
from discord import Message, Intents, Status, Game
from discord.ext import commands

from cogs.flow import FlowCog
from cogs.gvaway import GiveAwayCog
from cogs.roles import ReactionRoles
from cogs.welcome import WelcomeCog
from utility.config import config
from utility.utils import log
from utility.db_utils import DbUtils

print("main or dev?")
user = input()
if user == "main":
    token = config.main
    prefix = ['!', '！']
    guild = 778804551972159489
    application_id = 956049912699715634
    debug_toggle = False
else:
    token = config.dev
    prefix = ['!']
    guild = 778804551972159489
    application_id = 957621570128449626
    debug_toggle = True

# 前綴, token, intents
intents = Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True


class ShenheBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=prefix,
            intents=intents,
            application_id=application_id,
            owner_ids=[289597294075183114, 410036441129943050, 831883841417248778]
        )

    async def setup_hook(self) -> None:
        self.db = await aiosqlite.connect('main.db')
        self.debug_toggle = debug_toggle
        await self.load_extension('jishaku')
        for filepath in Path('./cogs').glob('**/*.py'):
            cog_name = Path(filepath).stem
            # if cog_name == 'fish':
            #     pass
            await self.load_extension(f'cogs.{cog_name}')
            print(log(True, False, 'Cog', f'Loaded {cog_name}'))
        self.add_view(FlowCog.AcceptView(self.db, self))
        self.add_view(FlowCog.ConfirmView(self.db, self))
        self.add_view(GiveAwayCog.GiveAwayView(self.db, self))
        self.add_view(ReactionRoles.RoleSelection())
        self.add_view(ReactionRoles.RoleSelection.WorldLevelView())
        self.add_view(WelcomeCog.AcceptRules(self.db))
        self.add_view(WelcomeCog.StartTutorial(self.db))
        self.add_view(WelcomeCog.Welcome(None))

    async def on_ready(self):
        await self.change_presence(
            status=Status.online,
            activity=Game(name=f'/help')
        )
        print(log(True, False, 'Bot', f'Logged in as {self.user}'))

    async def on_message(self, message: Message):
        if message.author.id == self.user.id:
            return
        await self.process_commands(message)

    async def close(self) -> None:
        await self.db.close()
        return await super().close()


bot = ShenheBot()
bot.run(token)
