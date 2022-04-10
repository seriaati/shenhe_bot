import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import discord, asyncio, yaml, datetime
import global_vars
global_vars.Global()
from discord.ext import commands
from discord.ext.forms import Form

with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', encoding = 'utf-8') as file:
    users = yaml.full_load(file)

class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role("小雪團隊")
    async def newuser(self, ctx):
        form = Form(ctx, '新增帳號設定流程')
        form.add_question('原神UID?', 'uid')
        form.add_question('用戶名?', 'name')
        form.add_question('discord ID?', 'discordID')
        form.add_question('ltuid?', 'ltuid')
        form.add_question('ltoken?', 'ltoken')

        form.edit_and_delete(True)
        form.set_timeout(60)
        await form.set_color("0xa68bd3")
        result = await form.start()
        dateNow = datetime.datetime.now()
        newUser = {'name': str(result.name), 'uid': int(result.uid), 'discordID': int(result.discordID), 'ltoken': str(result.ltoken), 'ltuid': int(result.ltuid), 'dm': True, 'dmCount': 0, 'dmDate': dateNow}
        users.append(newUser)
        with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', 'w', encoding = 'utf-8') as file:
            yaml.dump(users, file)
        await ctx.send(f"已新增該帳號")

def setup(bot):
    bot.add_cog(OwnerCog(bot))