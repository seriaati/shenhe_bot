import wavelink
from discord.ext import commands
from discord import Interaction, app_commands
from utility.config import config
from utility.utils import errEmbed


class MusicCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host='127.0.0.1',
            port=2333,
            password=config.lavalink)

    @app_commands.command(name="play", description="Play Music")
    async def play(self, interaction: Interaction, search: str):
        if interaction.user.voice is None:
            return await interaction.response.send_message(embed=errEmbed('<a:error_animated:982579472060547092> 請在'))
        if not interaction.guild.voice_client:
             vc: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = interaction.guild.voice_client
        track: wavelink.YouTubeTrack = await wavelink.YouTubeTrack.search(search, return_first=True)
        await vc.play(track)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MusicCog(bot))
