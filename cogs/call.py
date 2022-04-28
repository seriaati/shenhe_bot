from discord import app_commands
from discord.ext import commands
from utility.utils import log
import discord


class CallCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    group = app_commands.Group(name="call", description="呼叫某個群友")

    @group.command(name='turtle',description='呼叫律律')
    async def turtle(self, interaction: discord.Interaction):
        print(log(False, False, 'Call', interaction.user.id))
        await interaction.response.send_message("律律🐢")

    @group.command(name='rabbit',description='呼叫兔兔')
    async def rabbit(self, interaction: discord.Interaction):
        print(log(False, False, 'Call', interaction.user.id))
        await interaction.response.send_message("可愛的🐰兔")

    @group.command(name='小雪',description='呼叫小雪')
    async def 小雪(self, interaction: discord.Interaction):
        print(log(False, False, 'Call', interaction.user.id))
        await interaction.response.send_message("「又聰明又可愛的成熟女孩子」 - tedd")

    @group.command(name='ttos',description='呼叫吐司')
    async def ttos(self, interaction: discord.Interaction):
        print(log(False, False, 'Call', interaction.user.id))
        await interaction.response.send_message("好吃的巧克力土司")

    @group.command(name='maple',description='呼叫楓')
    async def maple(self, interaction: discord.Interaction):
        print(log(False, False, 'Call', interaction.user.id))
        await interaction.response.send_message("可愛的楓！")

    @group.command(name='tedd',description='呼叫Tedd')
    async def tedd(self, interaction: discord.Interaction):
        print(log(False, False, 'Call', interaction.user.id))
        await interaction.response.send_message("沈默寡言但內心很善良也很帥氣的tedd哥哥")

    @group.command(name='airplane',description='呼叫機機仔')
    async def airplane(self, interaction: discord.Interaction):
        print(log(False, False, 'Call', interaction.user.id))
        await interaction.response.send_message("✈仔")

    @app_commands.command(name='snow',description='小雪國萬歲!')
    async def snow(self, interaction: discord.Interaction):
        print(log(False, False, 'Call', interaction.user.id))
        await interaction.response.send_message("❄小雪國萬歲！")

    @group.command(name='小羽',description='呼叫小羽')
    async def 小羽(self, interaction: discord.Interaction):
        """呼叫小羽"""
        print(log(False, False, 'Call', interaction.user.id))
        await interaction.response.send_message("可愛的小羽！")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CallCog(bot))