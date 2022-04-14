import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import discord
import global_vars
global_vars.Global()
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        embed = global_vars.defaultEmbed("所有指令", "`!help`呼叫這個界面")
        embed.add_field(name = "➜ 原神資料(需註冊)", 
            value="`!register`註冊帳號\n`!users`所有帳號和uid\n`!check`樹脂等資料\n`!abyss`深淵資料\n`!stats`原神其他資料\n`!claim`領取網頁登入獎勵\n`!diary`本月原石摩拉獲取量\n`!log`詳細原石摩拉獲取資訊\n`!redeem`兌換兌換碼\n`!char`查看角色\n`!area`區域探索度\n`!today`今日原石摩拉收入")
        embed.add_field(name = "➜ 呼叫!", 
            value = "`!airplane`呼叫飛機仔!\n`!rabbit`呼叫兔兔!\n`!snow`小雪國萬歲!\n`!小雪`呼叫小雪!\n`!turtle`呼叫律律龜!\n`!flow`呼叫flow!\n`!tedd`呼叫tedd!\n`!ttos`呼叫土司!\n`!maple`呼叫楓!")
        embed.add_field(name = "➜ 趣味", 
            value = "`!cute <人物>`可愛~\n`!say`讓申鶴說話\n`!flash`防放閃指令\n`!vote`發起投票\n`!marry`結婚owo")
        embed.add_field(name = "➜ 其他功能", 
            value = "`!group`小組指令組界面\n`!flow`flow功能界面\n`!farm`原神今日可刷素材")
        # embed.add_field(name = "➜ 小遊戲(可賺flow幣)", 
        #     value = "`!rps`剪刀石頭布")
        global_vars.setFooter(embed)
        await ctx.send(embed=embed)

    @commands.command()
    async def adminhelp(self, ctx):
        embed = global_vars.defaultEmbed("管理員指令", 
            "`!adminhelp`呼叫此界面\n`!dm`私訊提醒功能\n`!stuck`hoyo資料沒打開\n`!reload`更新封包\n`!check_loop`打開私訊功能")
        global_vars.setFooter(embed)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(HelpCog(bot))