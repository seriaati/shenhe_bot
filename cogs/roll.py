import discord
from discord.ext import commands
from discord import Guild, Interaction, app_commands

class RollCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.blue_gif = 'https://media.discordapp.net/attachments/968783693814587423/970226962650001418/IMG_0482.gif'
        self.purple_gif = 'https://media.discordapp.net/attachments/968783693814587423/970226962356391966/IMG_0477.gif'
        self.gold_gif = 'https://images-ext-2.discordapp.net/external/R7xaFvgvsuXs1sd2SK8x2hIKze9lDMFX8ofdg7Hgim4/https/media.tenor.com/Nc7Fgo43GLwAAAPo/genshin-gold-genshin-wish.mp4'

    @app_commands.command(name='roll',description='扭蛋')
    async def roll(self, interaction: discord.Interaction):
        await interaction.response.send_message('尚未完成')
        

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RollCog(bot))