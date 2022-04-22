# shenhe-bot by seria
import discord
import git
import yaml
from discord.ext import commands
import cmd.asset.global_vars as Global
from pathlib import Path

with open(f'cmd/asset/accounts.yaml', 'r', encoding='utf-8') as file:
    users = yaml.full_load(file)

# 前綴, token, intents
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix=['!','！'], help_command=None,
                   intents=intents, case_insensitive=True)
token = Global.bot_token

skip = ['__init__','character_name','classes','global_vars']

for filepath in Path('./cmd').glob('**/*.py'):
    cog_name = Path(filepath).stem
    if cog_name in skip:
        continue
    bot.load_extension(f'cmd.{cog_name}')

@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online, activity=discord.Game(name=f'輸入!help來查看幫助'))
    print("Shenhe has logged in.")
    print("---------------------")


@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.command(help="重整指令包", hidden = True)
@commands.has_role("小雪團隊")
async def reload(ctx, arg):
    g = git.cmd.Git(f"C:/Users/alice/shenhe_bot")
    g.pull()
    await ctx.send("已從源碼更新")
    if arg == 'all':
        for filepath in Path('./cmd').glob('**/*.py'):
            cog_name = Path(filepath).stem
            try:
                bot.reload_extension(f'cmd.{cog_name}')
                await ctx.send(f"已重整 {cog_name} 指令包")
            except Exception as e:
                await ctx.send(f"{cog_name}發生錯誤```{e}```")
    else:
        for filepath in Path('./cmd').glob('**/*.py'):
            cog_name = Path(filepath).stem
            if arg == cog_name:
                try:
                    bot.reload_extension(f'cmd.{cog_name}')
                    await ctx.send(f"已重整 {cog_name} 指令包")
                except Exception as e:
                    await ctx.send(f"{cog_name}發生錯誤```{e}```")


bot.run(token, bot=True, reconnect=True)
