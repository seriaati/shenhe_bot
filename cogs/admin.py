import pickle
import platform

from discord.ext import commands
from diskcache import FanoutCache

from dev.models import BotModel, DefaultEmbed
from utils import dm_embed


class AdminCog(commands.Cog, name="admin"):
    def __init__(self, bot):
        self.bot: BotModel = bot
        if platform.system() == "Linux":
            import pm2py  # type: ignore

            self.pm2 = pm2py.PM2()

    @commands.is_owner()
    @commands.command(name="pm2")
    async def pm2_command(self, ctx: commands.Context, *, action: str):
        process_name = "shenhe_testing" if self.bot.debug else "shenhe_bot"
        if action == "list":
            process_list = self.pm2.list()
            await ctx.send(f"```{process_list}```")
        elif action == "restart":
            await ctx.send(f"Applied action: restart on {process_name}")
            self.pm2.restart(process_name)
        elif action == "stop":
            await ctx.send(f"Applied action: stop on {process_name}")
            self.pm2.stop(process_name)
        elif action == "start":
            await ctx.send(f"Applied action: start on {process_name}")
            self.pm2.start(process_name)
        elif action == "delete":
            await ctx.send(f"Applied action: delete on {process_name}")
            self.pm2.delete(process_name)
        else:
            await ctx.send(f"Invalid action: {action}")

    @commands.is_owner()
    @commands.command(name="maintenance")
    async def maintenance(self, ctx: commands.Context):
        self.bot.maintenance = not self.bot.maintenance
        await ctx.send(f"maintenance mode is now {self.bot.maintenance}")

    @commands.is_owner()
    @commands.command(name="sync")
    async def sync(self, ctx: commands.Context):
        await self.bot.tree.sync()
        await ctx.send("commands synced")

    @commands.is_owner()
    @commands.command(name="dm")
    async def direct_message(
        self, ctx: commands.Context, user: commands.UserConverter, *, message: str
    ):
        embed = DefaultEmbed(message)
        embed.set_author(
            name=ctx.author.name + "#" + ctx.author.discriminator,
            icon_url=ctx.author.display_avatar.url,
        )
        success = await dm_embed(user, embed)  # type: ignore
        if not success:
            await ctx.send("failed to send message")
        else:
            await ctx.send("message sent")

    @commands.is_owner()
    @commands.command(name="transfer-enka-cache")
    async def transfer_enka_cache(self, ctx: commands.Context, uid: int):
        await ctx.send("getting old cache...")
        en_cache = FanoutCache("data/cache/enka_eng_cache")
        cache = FanoutCache("data/cache/enka_data_cache")
        en_cache_data = en_cache.get(uid)
        cache_data = cache.get(uid)
        await self.bot.pool.execute(
            "INSERT OR REPLACE INTO enka_cache (uid, en_data, data) VALUES ($1, $2, $3)",
            uid,
            pickle.dumps(en_cache_data),
            pickle.dumps(cache_data),
        )
        await ctx.send("done")

    @commands.is_owner()
    @commands.command(name="disable")
    async def disable_command(self, ctx: commands.Context, command: str):
        if command not in self.bot.all_commands:
            await ctx.send("command not found")
            return

        if command in self.bot.disabled_commands:
            self.bot.disabled_commands.remove(command)
            await ctx.send("command enabled")
        else:
            self.bot.disabled_commands.append(command)
            await ctx.send("command disabled")

    @commands.is_owner()
    @commands.command(name="flush")
    async def flush_log(self, ctx: commands.Context):
        with open("log.log", "w") as f:
            f.write("")
        await ctx.send("log flushed")


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(AdminCog(bot))
