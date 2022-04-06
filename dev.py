import genshin
import discord
import ruamel.yaml as yaml
from discord.ext import commands
from random import randint
from datetime import datetime

intents = discord.Intents.default()
intents.members = True
intents.reactions = True

# find
class Find:
    def __init__(self, name, message_id):
        member = []
        self.name = name
        self.member = member
        self.message_id = message_id

global finds 
finds = []

bot = commands.Bot(command_prefix = '%', help_command=None)

@bot.command()
async def find(ctx, game):
    embed = discord.Embed(title=game, description="find")
    message = await ctx.send(embed=embed)
    await message.add_reaction('✅')

@bot.event
async def on_reaction_add(reaction, user):
    

@bot.event
async def on_reaction_remove(reaction, user):
    channel = bot.get_channel(909595117952856084)
    if reaction.message.channel.id != channel.id:
        return
    if reaction.emoji == "✅":
      await channel.send(f"{user} uncheck")
bot.run("OTU3NjIxNTcwMTI4NDQ5NjI2.YkBclg.ezNtwod-qjrLj3qYJKEaTcxY2sw")