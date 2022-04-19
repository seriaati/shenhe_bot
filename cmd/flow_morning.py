from discord.ext import commands
from datetime import date
import yaml


with open(f'cmd/asset/flow.yaml', encoding='utf-8') as file:
    users = yaml.full_load(file)
with open(f'cmd/asset/bank.yaml', encoding='utf-8') as file:
    bank = yaml.full_load(file)


class FlowMorningCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        discordID = message.author.id
        channel = self.bot.get_channel(message.channel.id)
        if message.author == self.bot.user:
            return
        if "早安" in message.content:
            today = date.today()
            if discordID in users:
                if user['morning'] != today:
                    user['flow'] += 1
                    bank['flow'] -= 1
                    user['morning'] = today
                    with open(f'cmd/asset/flow.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(users, file)
                    with open(f'cmd/asset/bank.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(bank, file)
                    await message.add_reaction(f"☀️")
            else:
                discordID = message.author.id
                user = self.bot.get_user(message.author.id)
                flowCog = self.bot.get_cog('FlowCog')
                await flowCog.register(channel, user, discordID)


def setup(bot):
    bot.add_cog(FlowMorningCog(bot))
