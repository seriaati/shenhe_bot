# shenhe-bot by seria
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
bot = commands.Bot(command_prefix="!", help_command=None,
                   intents=intents, case_insensitive=True)
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
    "cmd.flow_gv",
    "cmd.error_handle"
]
if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

# 開機時
@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online, activity=discord.Game(name=f'輸入!help來查看幫助'))
    print("Shenhe has logged in.")
    print("---------------------")


@tasks.loop(hours=24)
async def claimLoop():
    for user in users:
        cookies = {"ltuid": user['ltuid'], "ltoken": user['ltoken']}
        uid = user['uid']
        client = genshin.Client(cookies)
        client.default_game = genshin.Game.GENSHIN
        client.lang = "zh-tw"
        client.uids[genshin.Game.GENSHIN] = uid
        try:
            await client.claim_daily_reward()
        except genshin.AlreadyClaimed:
            print(f"{user['name']} already claimed")
        else:
            print(f"claimed for {user['name']}")


@tasks.loop(seconds=600)
async def checkLoop():
    for user in users.items():
        if isinstance(user, type(None)) == True:
            print(f"use is NoneType: {user['name']}")
        else:
            try:
                cookies = {"ltuid": user['ltuid'],
                           "ltoken": user['ltoken']}
                uid = user['uid']
                print("check"+ cookies)
                userObj = bot.get_user(user['discordID'])
                client = genshin.Client(cookies)
                client.default_game = genshin.Game.GENSHIN
                client.lang = "zh-tw"
                client.uids[genshin.Game.GENSHIN] = uid
                notes = await client.get_notes(uid)
                resin = notes.current_resin
                dateNow = datetime.datetime.now()
                diff = dateNow - user['dmDate']
                diffHour = diff.total_seconds() / 3600
                if resin >= 140 and user['dm'] == True and user['dmCount'] < 3 and diffHour >= 1:
                    time = notes.remaining_resin_recovery_time
                    hours, minutes = divmod(time // 60, 60)
                    fullTime = datetime.datetime.now() + datetime.timedelta(hours=hours)
                    printTime = '{:%H:%M}'.format(fullTime)
                    embed = global_vars.defaultEmbed(f"<:danger:959469906225692703>: 目前樹脂數量已經超過140!",
                                                     f"<:resin:956377956115157022> 目前樹脂: {notes.current_resin}/{notes.max_resin}\n於 {hours:.0f} 小時 {minutes:.0f} 分鐘後填滿(即{printTime})\n註: 不想收到這則通知打`!dm off`, 想重新打開打`!dm on`\n註: 部份指令, 例如`!check`可以在私訊運作")
                    global_vars.setFooter(embed)
                    await userObj.send(embed=embed)
                    user['dmCount'] += 1
                    user['dmDate'] = dateNow
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(users, file)
                elif resin < 140:
                    user['dmCount'] = 0
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(users, file)
            except genshin.errors.InvalidCookies:
                pass
            except AttributeError:
                print(f"{user['name']} 可能退群了")

# 等待申鶴準備
@checkLoop.before_loop
async def beforeLoop():
    print('waiting...')
    await bot.wait_until_ready()


@claimLoop.before_loop
async def wait_until_1am():
    now = datetime.datetime.now().astimezone()
    next_run = now.replace(hour=1, minute=0, second=0)
    if next_run < now:
        next_run += datetime.timedelta(days=1)
    await discord.utils.sleep_until(next_run)

checkLoop.start()
claimLoop.start()


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
