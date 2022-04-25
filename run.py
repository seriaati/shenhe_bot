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
else:
    token = config.dev
    prefix = ['%']

# 前綴, token, intents
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix=prefix, help_command=None,
                   intents=intents, case_insensitive=True)


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

@bot.command(hidden = True)
@commands.has_role("小雪團隊")
async def reload(ctx):
    g = git.cmd.Git('C:\Users\alice\shenhe_bot')
    g.pull()
    print(log(True, False, 'Pull', 'Pulled from github'))
    await ctx.send("已從源碼更新")
    for filepath in Path('./cogs').glob('**/*.py'):
        cog_name = Path(filepath).stem
        bot.reload_extension(f'cogs.{cog_name}')
        print(log(True, False,'Cog', f'Reloaded {cog_name}'))
    await ctx.send("Reloaded all Cogs")


bot.run(token, bot=True, reconnect=True)
