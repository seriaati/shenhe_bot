from discord import Message
from discord.ext import commands

from utility.utils import errEmbed
class SeseCog(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.debug: bool = self.bot.debug_toggle

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.id == self.bot.user.id:
            return
        sese_channel = self.bot.get_channel(984792329426714677) if self.debug else self.bot.get_channel(965842415913152522)
        if message.channel == sese_channel and len(message.attachments) != 0:
            for attachment in message.attachments:
                if not attachment.is_spoiler():
                    await message.delete()
                    await message.channel.send(embed=errEmbed('在色色台發圖片請spoiler!'), delete_after=3)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SeseCog(bot))