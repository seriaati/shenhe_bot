from discord.ext import commands
from random import randint
from cmd.asset.global_vars import defaultEmbed, setFooter


class OtherCMDCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if "機率" in message.content:
            value = randint(1, 100)
            await message.channel.send(f"{value}%")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        public = self.bot.get_channel(916951131022843964)
        await public.send("<@!459189783420207104> 櫃姊兔兔請準備出動!有新人要來了!")

    @commands.command()
    async def ping(self, ctx):
        await ctx.send('🏓 Pong! {0}s'.format(round(self.bot.latency, 1)))

    @commands.command()
    async def cute(self, ctx, arg):
        string = arg
        await ctx.send(f"{string}真可愛~❤")

    @commands.command()
    async def say(self, ctx, *, name='', msg=''):
        await ctx.message.delete()
        await ctx.send(f"{name} {msg}")

    @commands.command()
    async def flash(self, ctx):
        await ctx.send("https://media.discordapp.net/attachments/823440627127287839/960177992942891038/IMG_9555.jpg")

    @commands.command()
    async def randnumber(self, ctx, arg1, arg2):
        value = randint(int(arg1), int(arg2))
        await ctx.send(str(value))

    @commands.command()
    async def marry(self, ctx, arg1, arg2):
        await ctx.send(f"{arg1} ❤ {arg2}")

    @commands.command()
    async def getid(self, ctx):
        embed = defaultEmbed(
            "如何取得discord ID?", "1. 打開dc設定\n2.「進階」\n3. 把「開發者模式」打開\n4. 右鍵使用者頭像, 便可以看到「copy ID」")
        setFooter(embed)
        await ctx.send(embed=embed)

    @commands.command()
    async def version(self, ctx):
        await ctx.message.delete()
        embed = defaultEmbed(
            f"申鶴 v1.0.4",
            "**原神系統**\n• 中文角色名稱\n• `!floor`來查看深淵不同層數的使用角色"
        )
        setFooter(embed)
        await ctx.send(embed=embed)

    @commands.command()
    async def quote(self, ctx):
        msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        await ctx.send(msg.content)

    @commands.command()
    @commands.has_role("小雪團隊")
    async def cleanup(self, ctx, arg):
        channel = ctx.channel
        deleted = await channel.purge(limit=int(arg))
        await channel.send('已移除 {} 個訊息'.format(len(deleted)), delete_after=3)


def setup(bot):
    bot.add_cog(OtherCMDCog(bot))
