#shenhe-bot by seria
import getpass

owner = getpass.getuser()
import sys

sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import datetime

import discord
import genshin
import global_vars
import yaml

global_vars.Global()
import config

config.Token()
from discord.ext import commands, tasks

with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', 'r', encoding = 'utf-8') as file:
    users = yaml.full_load(file)

# 前綴, token, intents
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", help_command=None, intents=intents, case_insensitive=True)
token = config.bot_token

# 指令包
initial_extensions = [
"cmd.genshin",
"cmd.call", 
"cmd.register", 
"cmd.othercmd", 
"cmd.farm", 
"cmd.help",
"cmd.vote",
"cmd.flow",
"cmd.flow_shop",
"cmd.flow_find",
"cmd.flow_confirm",
"cmd.flow_morning",
"cmd.flow_giveaway",
"cmd.error_handle"
]
if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

# 開機時
@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,activity = discord.Game(name=f'輸入!help來查看幫助'))
    print("Shenhe has logged in.")
    print("---------------------")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

@bot.command()
@commands.has_role("小雪團隊")
async def reload(ctx, arg):
    if arg == 'all':
        for extension in initial_extensions:
            try:
                bot.reload_extension(extension)
                await ctx.send(f"已重整 {extension} 指令包")
            except:
                await ctx.send(f"{extension} 指令包有錯誤")
    else:
        for extension in initial_extensions:
            extStr = f"cmd.{arg}"
            if extStr == extension:
                try:
                    bot.reload_extension(extension)
                    await ctx.send(f"已重整 {extension} 指令包")
                except:
                    await ctx.send(f"{extension} 指令包有錯誤")

@bot.command()
@commands.has_role("小雪團隊")
async def unload(ctx, arg):
    for extension in initial_extensions:
        exStr = F"cmd.{arg}"
        if exStr == extension:
            try:
                bot.unload_extension(extension)
                await ctx.send(f"已unload {extension} 指令包")
            except:
                await ctx.send(f"{extension} 指令包無法被取消加載")

@bot.command()
@commands.has_role("小雪團隊")
async def load(ctx, arg):
    for extension in initial_extensions:
        exStr = F"cmd.{arg}"
        if exStr == extension:
            try:
                bot.load_extension(extension)
                await ctx.send(f"已unload {extension} 指令包")
            except:
                await ctx.send(f"{extension} 指令包無法被加載")

bot.run(token, bot=True, reconnect=True)
