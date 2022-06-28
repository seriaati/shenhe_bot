# shenhe-bot by seria

import getpass
import traceback
from pathlib import Path

import aiohttp
import aiosqlite
from discord import Game, Intents, Interaction, Message, Status, app_commands
from discord.ext import commands
from pyppeteer import launch

from cogs.flow import FlowCog
from cogs.gvaway import GiveAwayCog
from cogs.roles import ReactionRoles
from cogs.welcome import WelcomeCog
from debug import DebugView
from utility.config import config
from utility.db_utils import DbUtils
from utility.utils import errEmbed, log

user_name = getpass.getuser()
if user_name == "alice":
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
            owner_ids=[289597294075183114,
                       410036441129943050, 831883841417248778]
        )

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()
        self.db = await aiosqlite.connect('main.db')
        self.browser = await launch({'headless': True, 'autoClose': False, "args": ['--proxy-server="direct://"', '--proxy-bypass-list=*', '--no-sandbox', '--start-maximized']})
        self.debug_toggle = debug_toggle
        await self.load_extension('jishaku')
        for filepath in Path('./cogs').glob('**/*.py'):
            cog_name = Path(filepath).stem
            await self.load_extension(f'cogs.{cog_name}')
        self.add_view(FlowCog.AcceptView(self.db, self))
        self.add_view(FlowCog.ConfirmView(self.db, self))
        self.add_view(GiveAwayCog.GiveAwayView(self.db, self))
        self.add_view(ReactionRoles.RoleSelection())
        self.add_view(ReactionRoles.RoleSelection.WorldLevelView())
        self.add_view(ReactionRoles.NationalityChooser([1, 2, 3]))
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
        await self.browser.close()
        return await super().close()


bot = ShenheBot()
tree = bot.tree


@tree.error
async def err_handle(i: Interaction, e: app_commands.AppCommandError):
    if isinstance(e, app_commands.errors.MissingRole):
        embed = errEmbed(
            '<a:error_animated:982579472060547092> 權限不足', '你不是小雪團隊的一員')
        if i.response._responded:
            await i.edit_original_message(embed=embed)
        else:
            await i.response.send_message(embed=embed, ephemeral=True)
    else:
        seria = i.client.get_user(410036441129943050)
        view = DebugView(traceback.format_exc())
        embed = errEmbed(
            '<a:error_animated:982579472060547092> 未知錯誤', f'```py\n{e}\n```')
        if i.response._responded:
            await i.edit_original_message(content=f'{seria.mention} 系統已將錯誤回報給小雪, 請耐心等待修復', embed=embed, view=view)
        else:
            await i.response.send_message(content=f'{seria.mention} 系統已將錯誤回報給小雪, 請耐心等待修復', embed=embed, view=view)
bot.run(token)
