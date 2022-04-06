import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import global_vars
from discord.ext import commands
from datetime import datetime
global_vars.Global()

@commands.command()
async def farm(ctx):
    weekdayGet = datetime.today().weekday()
    if weekdayGet == 0:
        weekday = "禮拜一"
    elif weekdayGet == 1:
        weekday = "禮拜二"
    elif weekdayGet == 2:
        weekday = "禮拜三"
    elif weekdayGet == 3:
        weekday = "禮拜四"
    elif weekdayGet == 4:
        weekday = "禮拜五"
    elif weekdayGet == 5:
        weekday = "禮拜六"
    elif weekdayGet == 6:
        weekday = "禮拜日"
    embedFarm=defaultEmbed(f"今天({weekday})可以刷的副本材料"," ")
    if weekdayGet == 0 or weekdayGet == 3:
        # monday or thursday
        embedFarm.set_image(url="https://media.discordapp.net/attachments/823440627127287839/958862746349346896/73268cfab4b4a112.png")
    elif weekdayGet == 1 or weekdayGet == 4:
        # tuesday or friday
        embedFarm.set_image(url="https://media.discordapp.net/attachments/823440627127287839/958862746127060992/5ac261bdfc846f45.png")
    elif weekdayGet == 2 or weekdayGet == 5:
        # wednesday or saturday
        embedFarm.set_image(url="https://media.discordapp.net/attachments/823440627127287839/958862745871220796/0b16376c23bfa1ab.png")
    elif weekdayGet == 6:
        embedFarm=defaultEmbed(f"今天({weekday})可以刷的副本材料","禮拜日可以刷所有素材 (❁´◡`❁)")
    setFooter(embedFarm)
    await ctx.send(embed=embedFarm)

def setup(bot):
    bot.add_command(farm)