import getpass

owner = getpass.getuser()
import sys

sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import global_vars

global_vars.Global()
from random import randint

from discord.ext import commands


class OtherCMDCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if "機率" in message.content:
            value = randint(1,100)
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
    async def say(self, ctx, * , name='', msg=''):
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
        embed = global_vars.defaultEmbed("如何取得discord ID?", "1. 打開dc設定\n2.「進階」\n3. 把「開發者模式」打開\n4. 右鍵使用者頭像, 便可以看到「copy ID」")
        global_vars.setFooter(embed)
        await ctx.send(embed=embed)
        
def setup(bot):
    bot.add_cog(OtherCMDCog(bot))
