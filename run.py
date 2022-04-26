# shenhe-bot by seria

import discord
import git
from discord.ext import slash
from utility.config import config
from utility.utils import log
from pathlib import Path

print("main or dev?")
user = input()
if user == "main":
    token = config.main
    prefix = ['!', '！']
else:
    token = config.dev
    prefix = ['%']

# 前綴, token, intents
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
bot = slash.SlashBot(
    command_prefix=prefix, description='', help_command=None,
    debug_guild=916838066117824553,
    resolve_not_fetch=False, fetch_if_not_get=True
)


for filepath in Path('./cogs').glob('**/*.py'):
    cog_name = Path(filepath).stem
    bot.load_extension(f'cogs.{cog_name}')
    print(log(True, False,'Cog', f'Loaded {cog_name}'))


@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online, activity=discord.Game(name=f'輸入!help來查看幫助'))
    print(log(True, False, 'Bot', 'Logged in as {0.user}'.format(bot)))


@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.slash_cmd(default_permission=False)
async def reload(ctx: slash.Context):
    """重整指令包"""
    await ctx.respond(deferred=True)
    g = git.cmd.Git('C:/Users/alice/shenhe_bot')
    g.pull()
    print(log(True, False, 'Pull', 'Pulled from github'))
    await ctx.respond("已從源碼更新", ephemeral=True)
    for filepath in Path('./cogs').glob('**/*.py'):
        cog_name = Path(filepath).stem
        bot.reload_extension(f'cogs.{cog_name}')
        print(log(True, False,'Cog', f'Reloaded {cog_name}'))
    await ctx.respond("Reloaded all Cogs", ephemeral=True)

@bot.event
async def on_slash_permissions():
    reload.add_perm(bot.app_info.owner, True, None)
    await bot.register_permissions()


bot.run(token)
