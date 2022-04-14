import random as rand
import discord
import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import global_vars
from discord.ext import commands

class RPSCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    reactions = ['✊', '🖐️', '✌️']

    @commands.command()
    async def rps(self, ctx):
        embed = global_vars.defaultEmbed("剪刀石頭布", "請選一個!")
        global_vars.setFooter(embed)
        msg = await ctx.send(embed=embed)
        for reaction in self.reactions: await msg.add_reaction(reaction)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, ev: discord.RawReactionActionEvent):
        if ev.user_id != self.bot.user.id:
            await self.bot.http.delete_message(ev.channel_id, ev.message_id)
            msg = "哈哈, 申鶴贏了!" if str(ev.emoji) == rand.choice(self.reactions) \
                else "可惡, 沒想到居然輸給你了..."
            embed = global_vars.defaultEmbed("誰贏了呢?", f"{msg}\n你出了: {str(ev.emoji)}\n申鶴出了: {rand.choice(self.reactions)}")
            global_vars.setFooter(embed)
            await self.bot.get_channel(ev.channel_id).send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(RPSCog(bot))