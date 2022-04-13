import random as rand
import discord
from discord.ext import commands

from utils import EmbedBuilder

class Commands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    reactions = ['<:fasrock:701479480618909726>', '<:faspaper:701479480543150090>', '<:fasscissors:701479480593744002>']

    @commands.command(name='rps')
    async def _rps(self, ctx):
        msg = await ctx.send(embed=EmbedBuilder.embed(title=f"Rock Paper Scissor",
                                                      description=f"Please react, which item you want to choose..",
                                                      color=EmbedBuilder.randcolor()), delete_after=60)
        for reaction in self.reactions: await msg.add_reaction(reaction)
        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, ev: discord.RawReactionActionEvent):
        if ev.user_id != self.bot.user.id:
            await self.bot.http.delete_message(ev.channel_id, ev.message_id)
            msg = "The bot has won.... Try again!" if str(ev.emoji) == rand.choice(self.reactions) \
                else "You have won... Congratulation!"
            await self.bot.get_channel(ev.channel_id).send(
                embed=EmbedBuilder.embed(title=f"Rock Paper Scissor", description=msg, color=EmbedBuilder.randcolor()),
                delete_after=60)

def setup(bot: commands.Bot):
    bot.add_cog(Commands(bot))