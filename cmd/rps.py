import random as rand
import discord, yaml, getpass, datetime
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import global_vars
from discord.ext import commands

with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', encoding = 'utf-8') as file:
    users = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', encoding = 'utf-8') as file:
    bank = yaml.full_load(file)

class RPSCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    reactions = ['✊', '🖐️', '✌️']

    @commands.command()
    async def rps(self, ctx):
        embed = global_vars.defaultEmbed("剪刀石頭布vs申鶴", "「選擇下方的一個手勢吧...」")
        global_vars.setFooter(embed)
        msg = await ctx.send(embed=embed)
        for reaction in self.reactions: await msg.add_reaction(reaction)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, ev: discord.RawReactionActionEvent):
        if ev.user_id != self.bot.user.id and ev.message_id != 963970685770805288:
            await self.bot.http.delete_message(ev.channel_id, ev.message_id)
            msg = ""
            if str(ev.emoji) == rand.choice(self.reactions):
                # msg = "「我輸了嗎...?」 :anger:"
                msg = "=="
            elif str(ev.emoji) != rand.choice(self.reactions):
                msg = "!="
            else:
                msg = "else"
            embed = global_vars.defaultEmbed("誰贏了呢?", f"{msg}\n你出了: {str(ev.emoji)}\n申鶴出了: {rand.choice(self.reactions)}")
            global_vars.setFooter(embed)
            win = False
            if msg == "「我輸了嗎...?」 :anger:":
                win = True
            found = False
            for user in users:
                if user['discordID']==ev.user_id:
                    found = True
                    break
            if found == False:
                discordID = ev.user_id
                user = self.bot.get_user(ev.user_id)
                newUser = {'name': str(user), 'discordID': int(discordID), 'flow': 100}
                bank['flow'] -= 100
                users.append(newUser)
                with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
                    yaml.dump(users, file)
                with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding = 'utf-8') as file:
                    yaml.dump(bank, file)
            for user in users:
                dateNow = datetime.datetime.now()
                if 'rps' not in user:
                    print("rps no in user")
                    user['rps'] = 1
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
                        yaml.dump(users, file)
                if 'rpsDate' not in user:
                    user['rpsDate'] = dateNow
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
                        yaml.dump(users, file)
                diffDays = abs((dateNow - user['rpsDate']).days)
                if diffDays >= 1 and user['rps']<= 10 and win == True:
                    user['flow'] += 1
                    user['rps'] += 1
                    user['rpsDate'] = dateNow
                    bank['flow'] -=1
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
                        yaml.dump(users, file)
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding = 'utf-8') as file:
                        yaml.dump(bank, file)
            await self.bot.get_channel(ev.channel_id).send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(RPSCog(bot))