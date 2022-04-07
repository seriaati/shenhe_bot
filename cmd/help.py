import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import discord
import global_vars
global_vars.Global()
from discord.ext import commands

@commands.command()
async def help(ctx):
    embedHelp = global_vars.defaultEmbed("所有指令", "`!help`呼叫這個界面")
    embedHelp.add_field(name = "➜ 原神資料(需註冊)", value="`!register`註冊帳號\n`!users`所有帳號和uid\n`!check`樹脂等資料\n`!abyss`深淵資料\n`!stats`原神其他資料\n`!claim`領取網頁登入獎勵\n`!farm`今天可刷素材\n`!diary`本月原石摩拉獲取量\n`!log`詳細原石摩拉獲取資訊\n`!redeem`兌換兌換碼\n`!char`查看角色")
    embedHelp.add_field(name = "➜ 呼叫!", value = "`!airplane`呼叫飛機仔!\n`!rabbit`呼叫兔兔!\n`!snow`小雪國萬歲!\n`!小雪`呼叫小雪!\n`!turtle`呼叫律律龜!\n`!flow`呼叫flow!\n`!tedd`呼叫tedd!\n`!ttos`呼叫土司!\n`!maple`呼叫楓!")
    embedHelp.add_field(name = "➜ 趣味", value = "`!cute <人物>`可愛~\n`!say <使用者> <訊息>`\n向@使用者傳達「訊息」\n`!flash`防放閃指令\n`!vote`發起投票")
    embedHelp.add_field(name = "➜ 其他功能", value = "`!group`小組指令組界面\n`$help`音樂功能\n注意:音樂功能的前綴為`$`")
    global_vars.setFooter(embedHelp)
    await ctx.send(embed=embedHelp)

@commands.command()
async def adminhelp(ctx):
    embedHelp = global_vars.defaultEmbed("管理員指令", "`!adminhelp`呼叫此界面\n`!dm`私訊提醒功能\n`!stuck`hoyo資料沒打開\n`!reload`更新封包\n`!check_loop`打開私訊功能")
    global_vars.setFooter(embedHelp)
    await ctx.send(embedHelp)

def setup(bot):
    bot.add_command(help)
    bot.add_command(adminhelp)