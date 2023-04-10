import os

import topgg
from discord.ext import commands, tasks
from dotenv import load_dotenv

from utility import log

load_dotenv()


class TopggStats(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.update_stats.start()

    async def cog_unload(self) -> None:
        self.update_stats.cancel()

    @tasks.loop(minutes=30)
    async def update_stats(self) -> None:
        """This function runs every 30 minutes to automatically update the server count."""
        topgg_token = os.getenv("TOPGG_TOKEN")
        if topgg_token is None:
            log.info("[Top.gg] No token found, skipping post")
            return

        topggpy = topgg.DBLClient(
            self.bot, topgg_token, post_shard_count=True, autopost=True
        )
        try:
            await topggpy.post_guild_count()
            log.info(f"[Top.gg] Posted server count ({self.bot.guild_count})")
        except Exception as e:  # skipcq: PYL-W0703
            log.error(f"[Top.gg] Failed to post server count ({e})")


async def setup(bot) -> None:
    await bot.add_cog(TopggStats(bot))
