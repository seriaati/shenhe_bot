import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import discord, yaml, datetime, genshin
import global_vars
from discord.ext import commands
from discord.ext.forms import Form
global_vars.Global()

with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', encoding = 'utf-8') as file:
    users = yaml.full_load(file)

class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def register(self, ctx):
        embedRegister = global_vars.defaultEmbed("註冊教學", 
            "1. 去 https://www.hoyolab.com/home 然後登入\n2. 按F12\n3. 點擊console，將下方的指令貼上後按ENTER\n```javascript:(()=>{_=(n)=>{for(i in(r=document.cookie.split(';'))){var a=r[i].split('=');if(a[0].trim()==n)return a[1]}};c=_('account_id')||alert('無效的cookie,請重新登錄!');c&&confirm('將cookie複製到剪貼版？')&&copy(document.cookie)})();```\n4. 將複製的訊息私訊給<@410036441129943050>或<@665092644883398671>並附上你的原神UID及想要的使用者名稱\n註: 如果顯示無效的cookie，請重新登入, 如果仍然無效，請用無痕視窗登入")
        global_vars.setFooter(embedRegister)
        embed = global_vars.defaultEmbed("註冊帳號有什麼好處?", 
            global_vars.whyRegister)
        global_vars.setFooter(embed)
        await ctx.send(embed=embedRegister)
        await ctx.send(embed=embed)

    @commands.command()
    async def whyregister(self, ctx):
        embed = global_vars.defaultEmbed("註冊帳號有什麼好處?", 
            global_vars.whyRegister)
        global_vars.setFooter(embed)
        await ctx.send(embed=embed)

    @commands.command()
    async def stuck(self, ctx):
        embed = global_vars.defaultEmbed("已經註冊,但有些資料找不到?", 
            "1. 至hoyolab網頁中\n2. 點擊頭像\n3. personal homepage\n4. 右邊會看到genshin impact\n5. 點擊之後看到設定按鈕\n6. 打開 Do you want to enable real time-notes")
        global_vars.setFooter(embed)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_role("小雪團隊")
    async def newuser(self, ctx):
        form = Form(ctx, '新增帳號設定流程', cleanup=True)
        form.add_question('原神UID?', 'uid')
        form.add_question('用戶名?', 'name')
        form.add_question('discord ID?', 'discordID')
        form.add_question('ltuid?', 'ltuid')
        form.add_question('ltoken?', 'ltoken')
        form.edit_and_delete(True)
        form.set_timeout(60)
        await form.set_color("0xa68bd3")
        result = await form.start()
        dateNow = datetime.datetime.now()
        cookies = {"ltuid": result.ltuid, "ltoken": result.ltoken}
        uid = result.uid
        client = genshin.GenshinClient(cookies)
        failed = False
        try:
            notes = await client.get_notes(uid)
        except genshin.errors.InvalidCookies:
            failed = True
            await client.close()
        if failed == True:
            await ctx.send("帳號資料錯誤，請檢查是否有輸入錯誤")
        elif failed == False:
            newUser = {'name': str(result.name), 'uid': int(result.uid), 'discordID': int(result.discordID), 'ltoken': str(result.ltoken), 'ltuid': int(result.ltuid), 'dm': True, 'dmCount': 0, 'dmDate': dateNow}
            users.append(newUser)
            cookies = {"ltuid": int(result.ltuid), "ltoken": str(result.ltuid)}
            client = genshin.GenshinClient(cookies)
            signed_in, claimed_rewards = await client.get_reward_info()
            await client.claim_daily_reward()
            await client.close()
            with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', 'w', encoding = 'utf-8') as file:
                yaml.dump(users, file)
            await ctx.send(f"已新增該帳號並領取今日獎勵")

    @commands.command()
    async def dm(self, ctx, *, arg=''):
        if arg == "":
            embed = global_vars.defaultEmbed("什麼是私訊提醒功能？","申鶴每一小時會檢測一次你的樹脂數量，當超過140的時候，\n申鶴會私訊提醒你，最多提醒三次\n註: 只有已註冊的用戶能享有這個功能")
            global_vars.setFooter(embed)
            await ctx.send(embed=embed)
        elif arg == "on":
            for user in users:
                if user['discordID']==ctx.author.id:
                    user['dm'] = True
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', 'w', encoding = 'utf-8') as file:
                        yaml.dump(users, file)
                    await ctx.send(f"已開啟 {user['name']} 的私訊功能")
        elif arg == "off":
            for user in users:
                if user['discordID']==ctx.author.id:
                    user['dm'] = False
                    with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', 'w', encoding = 'utf-8') as file:
                        yaml.dump(users, file)
                    await ctx.send(f"已關閉 {user['name']} 的私訊功能")
def setup(bot):
    bot.add_cog(RegisterCog(bot))