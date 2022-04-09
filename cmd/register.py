import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import discord
import global_vars
from discord.ext import commands
global_vars.Global()

class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def register(self, ctx):
        embedRegister = global_vars.defaultEmbed("註冊教學", 
            "1. 去 https://www.hoyolab.com/home 然後登入\n2. 按F12\n3. 點擊console，將下方的指令貼上\n```javascript:(()=>{_=(n)=>{for(i in(r=document.cookie.split(';'))){var a=r[i].split('=');if(a[0].trim()==n)return a[1]}};c=_('account_id')||alert('無效的cookie,請重新登錄!');c&&confirm('將cookie複製到剪貼版？')&&copy(document.cookie)})();```\n4. 將複製的訊息私訊給小雪\n註: 如果顯示無效的cookie，請重新登入, 如果仍然無效，請用無痕視窗登入")
        global_vars.setFooter(embedRegister)
        embed = global_vars.defaultEmbed("註冊帳號有什麼好處?", 
            "• `!abyss`炫耀你的深淵傷害(或被嘲笑)\n• `!check`查看目前的派遣、樹脂、塵歌壺等狀況\n• `!char`炫耀你擁有的角色\n• `!stats`證明你是大佬\n• `!diary`看看這個月要不要課\n• 自動領取hoyolab網頁登入獎勵\n• 樹脂提醒功能(詳情請打`!dm`)")
        global_vars.setFooter(embed)
        await ctx.send(embed=embedRegister)
        await ctx.send(embed=embed)

    @commands.command()
    async def stuck(self, ctx):
        embed = global_vars.defaultEmbed("已經註冊,但有些資料找不到?", 
            "1. 至hoyolab網頁中\n2. 點擊頭像\n3. personal homepage\n4. 右邊會看到genshin impact\n5. 點擊之後看到設定按鈕\n6. 打開 Do you want to enable real time-notes")
        global_vars.setFooter(embed)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(RegisterCog(bot))