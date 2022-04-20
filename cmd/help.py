from discord.ext import commands
from cmd.asset.global_vars import defaultEmbed, setFooter


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        embed = defaultEmbed("所有指令", "`!help`呼叫這個界面")
        embed.add_field(name="➜ 原神資料(需註冊)",
                        value="`!register`註冊帳號\n`!users`所有帳號和uid\n`!check`樹脂等資料\n`!abyss`深淵資料\n`!stats`原神其他資料\n`!claim`領取網頁登入獎勵\n`!diary`本月原石摩拉獲取量\n`!log`詳細原石摩拉獲取資訊\n`!char`查看角色\n`!area`區域探索度\n`!today`今日原石摩拉收入")
        embed.add_field(name="➜ 呼叫!",
                        value="`!airplane`呼叫飛機仔!\n`!rabbit`呼叫兔兔!\n`!snow`小雪國萬歲!\n`!小雪`呼叫小雪!\n`!turtle`呼叫律律龜!\n`!tedd`呼叫tedd!\n`!ttos`呼叫土司!\n`!maple`呼叫楓!")
        embed.add_field(name="➜ 趣味",
                        value="`!cute <人物>`可愛~\n`!say`讓申鶴說話\n`!flash`防放閃指令\n`!vote`發起投票\n`!marry`結婚owo")
        embed.add_field(name="➜ 其他功能",
                        value="`!flow`flow功能界面\n`!farm`原神今日可刷素材")
        setFooter(embed)
        await ctx.send(embed=embed)

    @commands.command()
    async def adminhelp(self, ctx):
        embed = defaultEmbed("管理員指令", "`!adminhelp`呼叫此界面")
        embed.add_field(name="➜ 原神與指令包",
                        value="`!reload <name>`\n更新 <name> 指令包\n`!newuser`註冊原神帳號\n`!reload genshin`\n重整原神指令包")
        embed.add_field(name="➜ 常見問題",
                        value="`!dm`私訊提醒功能\n`!stuck`原神資料沒打開\n`!getid`如何取得dc ID?\n`!whyregister`\n註冊帳號有什麼好處?")
        embed.add_field(name="➜ flow幣",
                        value="`!reset`重置flow幣\n`!take`沒收flow幣(至銀行)\n`!make`給予flow幣(從銀行)")
        embed.add_field(name="➜ 商店",
                        value="`!shop clear <uuid>`清除 <uuid> 商品的購買次數\n`!shop clear all`清除所有商品的購買次數\n`!shop log`查看購買紀錄\n`!shop removeitem <uuid>`移除商品\n`!shop newitem`新增商品")
        embed.add_field(name="➜ 抽獎",
                        value="`!gv`抽獎")
        setFooter(embed)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(HelpCog(bot))
