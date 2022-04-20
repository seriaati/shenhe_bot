# shenhe-bot by seria
import discord
import git
import yaml
from discord.ext import commands
import cmd.asset.global_vars as Global

with open(f'cmd/asset/accounts.yaml', 'r', encoding='utf-8') as file:
    users = yaml.full_load(file)

# 前綴, token, intents
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", help_command=None,
                   intents=intents, case_insensitive=True)
token = Global.bot_token

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
    "cmd.error_handle"
]
if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)


@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online, activity=discord.Game(name=f'輸入!help來查看幫助'))
    print("Shenhe has logged in.")
    print("---------------------")


@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.command()
@commands.has_role("小雪團隊")
async def reload(ctx, arg):
    g = git.cmd.Git(f"C:/Users/alice/shenhe_bot")
    g.pull()
    await ctx.send("已從源碼更新")
    if arg == 'all':
        for extension in initial_extensions:
            try:
                bot.reload_extension(extension)
                await ctx.send(f"已重整 {extension} 指令包")
            except Exception as e:
                await ctx.send(f"{extension}發生錯誤```{e}```")
    else:
        for extension in initial_extensions:
            extStr = f"cmd.{arg}"
            if extStr == extension:
                try:
                    bot.reload_extension(extension)
                    await ctx.send(f"已重整 {extension} 指令包")
                except Exception as e:
                    await ctx.send(f"{extension}發生錯誤```{e}```")


@bot.command()
@commands.has_role("小雪團隊")
async def unload(ctx, arg):
    for extension in initial_extensions:
        exStr = F"cmd.{arg}"
        if exStr == extension:
            try:
                bot.unload_extension(extension)
                await ctx.send(f"已暫時關閉 {extension} 指令包")
            except Exception as e:
                await ctx.send(f"{extension}發生錯誤```{e}```")


@bot.command()
@commands.has_role("小雪團隊")
async def load(ctx, arg):
    for extension in initial_extensions:
        exStr = F"cmd.{arg}"
        if exStr == extension:
            try:
                bot.load_extension(extension)
                await ctx.send(f"已加載 {extension} 指令包")
            except Exception as e:
                await ctx.send(f"{extension}發生錯誤```{e}```")


bot.run(token, bot=True, reconnect=True)
