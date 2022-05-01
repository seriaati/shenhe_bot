import discord
from discord.ext import commands
from discord import Guild, Interaction, app_commands

class RollCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name='roll',description='扭蛋')
    async def roll(self, interaction: discord.Interaction):
        await interaction.response.send_message('尚未完成')

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RollCog(bot))