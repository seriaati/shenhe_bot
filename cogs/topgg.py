import os

import topgg
from discord.ext import commands, tasks
from dotenv import load_dotenv

from dev.models import BotModel
from utils import log

load_dotenv()


class TopggStats(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: BotModel = bot

    async def cog_load(self) -> None:
        if not self.bot.debug:
            self.update_stats.start()

    async def cog_unload(self) -> None:
        if not self.bot.debug:
            self.update_stats.cancel()

    @tasks.loop(minutes=30)
    async def update_stats(self) -> None:
        """This function runs every 30 minutes to automatically update the server count."""
        topgg_token = os.getenv("TOPGG_TOKEN")
        if topgg_token is None:
            log.info("[Top.gg] No token found, skipping post")
            return

        topggpy = topgg.DBLClient(  # type: ignore
            self.bot, topgg_token, post_shard_count=True, autopost=True
        )
        try:
            await topggpy.post_guild_count(
                len(self.bot.guilds), self.bot.shard_count, self.bot.shard_id
            )
            log.info(f"[Top.gg] Posted server count ({len(self.bot.guilds)})")
        except Exception as e:  # skipcq: PYL-W0703
            log.warning(f"[Top.gg] Failed to post server count ({e})")


async def setup(bot) -> None:
    await bot.add_cog(TopggStats(bot))
