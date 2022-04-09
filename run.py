#shenhe-bot by seria
import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import os, discord, asyncio, genshin, yaml, datetime
import global_vars
global_vars.Global()
import config
config.Token()
from discord.ext import commands
from discord.ext import tasks
from random import randint

with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', encoding = 'utf-8') as file:
    users = yaml.full_load(file)

# 前綴, token, intents
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", help_command=None, intents=intents, case_insensitive=True)
token = config.bot_token

# 指令包
initial_extensions = [
"cmd.genshin_stuff",
"cmd.call", 
"cmd.register", 
"cmd.othercmd", 
"cmd.farm", 
"cmd.help",
"cmd.vote",
"cmd.group",
"cmd.redeem",
"cmd.ownercmd",
"cmd.flow",
"cmd.roles"
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

# 私訊提醒功能
@tasks.loop(seconds=600) # 10 min
async def checkLoop():
    for user in users:
        try:
            cookies = {"ltuid": user['ltuid'], "ltoken": user['ltoken']}
            uid = user['uid']
            username = user['name']
            userid = bot.get_user(user['discordID'])
            client = genshin.GenshinClient(cookies)
            client.lang = "zh-tw"
            notes = await client.get_notes(uid)
            resin = notes.current_resin
            dateNow = datetime.datetime.now()
            diff = dateNow - user['dmDate']
            diffHour = diff.total_seconds() / 3600
            if resin >= 140 and user['dm'] == True and user['dmCount'] <= 3 and diffHour >= 1:
                print("已私訊 "+str(userid))
                time = notes.until_resin_recovery
                hours, minutes = divmod(time // 60, 60)
                embed=global_vars.defaultEmbed(f"<:danger:959469906225692703>: 目前樹脂數量已經超過140!",f"<:resin:956377956115157022> 目前樹脂: {notes.current_resin}/{notes.max_resin}\n於 {hours:.0f} 小時 {minutes:.0f} 分鐘後填滿\n註: 如果你不想要收到這則通知, 請私訊或tag小雪\n註: 部份指令, 例如`!check`可以在私訊運作")
                global_vars.setFooter(embed)
                await userid.send(embed=embed)
                user['dmCount'] += 1
                user['dmDate'] = dateNow
                with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', 'w', encoding = 'utf-8') as file:
                    yaml.dump(users, file)
                await client.close()
            elif resin < 140:
                user['dmCount'] = 0
                with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', 'w', encoding = 'utf-8') as file:
                    yaml.dump(users, file)
            await client.close()
        except genshin.errors.InvalidCookies:
            # print (f"{user['name']}帳號壞掉了")
            await client.close()
        
# 等待申鶴準備
@checkLoop.before_loop
async def beforeLoop():
    print('waiting...')
    await bot.wait_until_ready()

checkLoop.start()
# 偵測機率字串
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if "機率" in message.content:
        value = randint(1,100)
        await message.channel.send(f"{value}%")
    await bot.process_commands(message)

# 新人加入
@bot.event
async def on_member_join(member):
    public = bot.get_channel(916951131022843964)
    await public.send("<@!459189783420207104> 櫃姊兔兔請準備出動!有新人要來了!")

@bot.command()
@commands.is_owner()
async def reload(ctx, *, arg=''):
    if arg == '':
        for extension in initial_extensions:
            bot.reload_extension(extension)
            await ctx.send(f"已重整 {extension} 指令包")
    else:
        for extension in initial_extensions:
            extStr = f"cmd.{arg}"
            if extStr == exnteion:
                bot.reload_exnteion(extension)
                await ctx.send(f"已重整 {extension} 指令包")

bot.run(token, bot=True, reconnect=True)