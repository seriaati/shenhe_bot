import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from utility.utils import log


class CallCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='call', description='呼叫某個群友')
    @app_commands.rename(person='某人')
    @app_commands.describe(person='要呼叫誰呢?')
    @app_commands.choices(person=[
        Choice(name='turtle', value=0),
        Choice(name='rabbit', value=1),
        Choice(name='小雪', value=2),
        Choice(name='綾霞', value=3),
        Choice(name='ttos', value=4),
        Choice(name='maple', value=5),
        Choice(name='tedd', value=6),
        Choice(name='airplane', value=7),
        Choice(name='小羽', value=7)])
    async def call(self, interaction: discord.Interaction, person: int):
        if person == 0:
            await interaction.response.send_message("梨滷味")
        elif person == 1:
            await interaction.response.send_message("胡堂主的朋友，兔堂主")
        elif person == 2:
            await interaction.response.send_message("「又聰明又可愛的成熟女孩子」 - tedd")
        elif person == 3:
            await interaction.response.send_message("努力工作的變態策劃")
        elif person == 4:
            await interaction.response.send_message("好吃的巧克力土司")
        elif person == 5:
            await interaction.response.send_message("可愛的楓！")
        elif person == 6:
            await interaction.response.send_message("沈默寡言但內心很善良也很帥氣的tedd哥哥")
        elif person == 7:
            await interaction.response.send_message("✈仔")
        elif person == 8:
            await interaction.response.send_message("可愛的小羽！")

    @app_commands.command(name='snow', description='小雪國萬歲!')
    async def snow(self, interaction: discord.Interaction):
        await interaction.response.send_message("❄ 小雪國萬歲！")

    @app_commands.command(name='rabbit', description='兔兔島萬歲!')
    async def rabbit(self, interaction: discord.Interaction):
        await interaction.response.send_message("🐰 兔兔島萬歲！")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CallCog(bot))
