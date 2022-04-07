import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import genshin, discord
import global_vars
import accounts
from classes import User 
from discord.ext import commands
global_vars.Global()
accounts.account()

class RedeemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def redeem(self, ctx,* , code=''):
        if code != "all":
            found = False
            if code == "":
                embedError = global_vars.defaultEmbed("請輸入兌換碼", 
                    " ")
                global_vars.setFooter(embedError)
                await ctx.send(embed=embedError)
                return
            for user in accounts.users:
                if ctx.author.id==user.discordID:
                    found = True
                    cookies = {"ltuid": user.ltuid, "ltoken": user.ltoken}
                    uid = user.uid
                    username = user.username
            if found == False:
                embed = global_vars.embedNoAccount
                global_vars.setFooter(embed)
                await ctx.send(embed=embed)
                return

            # 取得資料
            client = genshin.GenshinClient(cookies)
            client.lang = "zh-tw"

            # 兌換
            try:
                await client.redeem_code(code)
                embedResult = global_vars.defaultEmbed(f"✅ 兌換成功: {username}", 
                    f"🎉 恭喜你!\n已幫你兌換:\n{code}")
                global_vars.setFooter(embedResult)
                await client.close()
                await ctx.send(embed=embedResult)
            except Exception as e:
                embedResult = global_vars.defaultEmbed(f"❌ 兌換失敗: {username}", 
                    f" ")
                global_vars.setFooter(embedResult)
                await client.close()
                await ctx.send(embed=embedResult)
        else:
            embedAsk = global_vars.defaultEmbed(f"👋 你好，大好人", 
                f"請輸入要幫大家兌換的兌換碼")
            global_vars.setFooter(embedAsk)
            await ctx.send(embed=embedAsk)
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            try:
                message = await self.bot.wait_for('message', timeout= 30.0, check= check)
            except asyncio.TimeoutError:
                await ctx.send(timeOutErrorMsg)
                return
            else:
                code = message.content
                for user in accounts.users:
                    cookies = {"ltuid": user.ltuid, "ltoken": user.ltoken}
                    username = user.username

                    client = genshin.GenshinClient(cookies)
                    client.lang = "zh-tw"

                    try:
                        await client.redeem_code(code)
                        embedResult = global_vars.defaultEmbed(f"✅ 兌換成功: {username}", 
                            f"🎉 恭喜你!\n已幫你兌換:\n{code}")
                        global_vars.setFooter(embedResult)
                        await client.close()
                        await ctx.send(embed=embedResult)
                    except Exception as e:
                        embedResult = global_vars.defaultEmbed(f"❌ 兌換失敗: {username}", 
                            f" ")
                        global_vars.setFooter(embedResult)
                        await client.close()
                        await ctx.send(embed=embedResult)

def setup(bot):
    bot.add_cog(RedeemCog(bot))