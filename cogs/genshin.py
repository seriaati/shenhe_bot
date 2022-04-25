import asyncio
from datetime import datetime
import discord
import DiscordUtils
import utility.utils as Global
import yaml
from utility.utils import defaultEmbed, errEmbed, setFooter, log
from discord.ext import commands, tasks
from discord.ext.forms import Form
from utility.GenshinApp import genshin_app
import genshin


class GenshinCog(commands.Cog, name="genshin", description="原神相關指令"):
    def __init__(self, bot):
        self.bot = bot
        try:
            with open('data/accounts.yaml', 'r', encoding='utf-8') as f:
                self.user_dict: dict[str, dict[str, str]] = yaml.full_load(f)
        except:
            self.user_dict: dict[str, dict[str, str]] = { }
        self.schedule.start()

    async def getUserData(self, ctx, discordID: int):
        with open(f'data/accounts.yaml', encoding='utf-8') as file:
            users = yaml.full_load(file)
        if discordID in users:
            try:
                cookies = {"ltuid": users[discordID]['ltuid'],
                           "ltoken": users[discordID]['ltoken']}
                uid = users[discordID]['uid']
                username = users[discordID]['name']
                return cookies, uid, username
            except genshin.errors.DataNotPublic:
                await ctx.send(f"你的帳號資料未公開, 輸入`!stuck`來獲取更多資訊")
        else:
            embed = Global.embedNoAccount
            setFooter(embed)
            await ctx.send(embed=embed)
            return

    loop_interval = 10
    @tasks.loop(minutes=loop_interval)
    async def schedule(self):
        now = datetime.now()
        if now.hour == 7 :
            print(log(True, False, 'Schedule', 'Auto claim started'))
            channel = self.bot.get_channel(909595117952856084)
            user_dict = dict(self.user_dict)
            count = 0
            for user_id, value in user_dict.items():
                result = await genshin_app.claimDailyReward(user_id)
                count += 1
                print(log(True, False, 'Schedule', f'Claimed for {user_id}'))
                await channel.send(f'[自動簽到] <@{user_id}> 領取成功')
                await asyncio.sleep(2.5)
            print(log(True, False, 'Schedule', f'Auto claim finished, total: {count}'))

        if 30 <= now.minute < 30 + self.loop_interval:
            print(log(True, False, 'Schedule', 'Resin check started'))
            user_dict = dict(self.user_dict)
            count = 0
            for user_id, value in user_dict.items():
                uid = user_dict[user_id]['uid']
                client, nickname = genshin_app.getUserCookie(user_id)
                try:
                    notes = await client.get_notes(uid)
                    count += 1
                except genshin.errors.DataNotPublic as e:
                    print(log(False, True, 'Notes', f'{user_id}: {e}'))
                    result = errEmbed('你的資料並不是公開的!', '請輸入`!stuck`來取得更多資訊')
                except genshin.errors.GenshinException as e:
                    print(log(False, True, 'Notes', f'{user_id}: {e}'))
                except Exception as e:
                    print(log(False, True, 'Notes', e))
                else:
                    if notes.current_resin >= 140 and value['dmCount'] < 3:
                        if notes.current_resin == notes.max_resin:
                            resin_recover_time = '已滿'
                        else:
                            day_msg = '今天' if notes.resin_recovery_time.day == datetime.now().day else '明天'
                            resin_recover_time = f'{day_msg} {notes.resin_recovery_time.strftime("%H:%M")}'
                        result = defaultEmbed(
                            f"<:danger:959469906225692703> 樹脂數量已超過140",
                            f"<:resin:956377956115157022> 目前樹脂: {notes.current_resin}/{notes.max_resin}\n"
                            f"樹脂回滿時間: {resin_recover_time}"
                        )
                        user = self.bot.get_user(user_id)
                        await user.send(embed=result)
                        value['dmCount'] += 1
                        self.saveUserData(user_dict)
                        await asyncio.sleep(4)
                    else:
                        value['dmCount'] = 0
                        self.saveUserData(user_dict)
            print(log(True, False, 'Schedule', f'Resin check finished, total: {count}'))

    @schedule.before_loop
    async def before_schedule(self):
        await self.bot.wait_until_ready()

    @commands.command(name="check",aliases=['c'],help='查看即時便籤')
    async def _check(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        msg = await ctx.send('讀取中...')
        result = await genshin_app.getRealTimeNotes(member.id)
        await msg.delete()
        await ctx.send(embed=result)

    @commands.command(name='stats',aliases=['s'],help='查看原神個人資料')
    async def _stats(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        msg = await ctx.send('讀取中...')
        result = await genshin_app.getUserStats(member.id)
        await msg.delete()
        await ctx.send(embed=result)

    @commands.command(name='area', help='查看區域探索度')
    async def _area(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        msg = await ctx.send('讀取中...')
        result = await genshin_app.getArea(member.id)
        await msg.delete()
        await ctx.send(embed=result)

    @commands.command(name='claim',help='領取今日hoyolab網頁登入獎勵')
    async def _claim(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        msg = await ctx.send('讀取中...')
        result = await genshin_app.claimDailyReward(member.id)
        await msg.delete()
        await ctx.send(embed=result)

    @commands.command(name='diary',aliases=['d'],help='查看今月摩拉與原石收入')
    async def _diary(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        form = Form(ctx, '月份選擇', cleanup=True)
        form.add_question('要查看今年幾月的收入?', 'month')
        form.set_timeout(60)
        await form.set_color("0xa68bd3")
        result = await form.start()
        msg = await ctx.send('讀取中...')
        result = await genshin_app.getDiary(member.id, result.month)
        await msg.delete()
        await ctx.send(embed=result)

    @commands.command(name='log',help='查看最近25筆原石與摩拉收入紀錄與來源')
    async def _log(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        msg = await ctx.send('讀取中...')
        result = await genshin_app.getDiaryLog(member.id)
        await msg.delete()
        paginator = DiscordUtils.Pagination.CustomEmbedPaginator(
            ctx, remove_reactions=True)
        paginator.add_reaction('◀', "back")
        paginator.add_reaction('▶', "next")
        await paginator.run(result)

    @commands.command(name='char',aliases=['ch'],help='查看所有擁有角色資訊')
    async def _char(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        msg = await ctx.send('讀取中...')
        result = await genshin_app.getUserCharacters(member.id)
        await msg.delete()
        paginator = DiscordUtils.Pagination.CustomEmbedPaginator(
            ctx, remove_reactions=True)
        paginator.add_reaction('⏮️', "first")
        paginator.add_reaction('◀', "back")
        paginator.add_reaction('▶', "next")
        paginator.add_reaction('⏭️', "last")
        await paginator.run(result)

    @commands.command(name='users',help='查看目前所有已註冊原神帳號')
    async def _users(self, ctx):
        print(log(False, False, 'Users', ctx.author.id))
        user_dict = dict(self.user_dict)
        userStr = ""
        count = 0
        for user_id, value in user_dict.items():
            count += 1
            userStr = userStr + \
                f"{count}. {value['name']} - {value['uid']}\n"
        embed = defaultEmbed("所有帳號", userStr)
        await ctx.send(embed=embed)

    @commands.command(name='today',aliases=['td'],help='查看今日原石與摩拉收入')
    async def _today(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        msg = await ctx.send('讀取中...')
        result = await genshin_app.getToday(member.id)
        await msg.delete()
        await ctx.send(embed=result)

    @commands.command(name='abyss',aliases=['abs'],help='查看深淵資料')
    async def _abyss(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        form = Form(ctx, '深淵期份選擇', cleanup=True)
        form.add_question('本期還是上期?', 'season')
        form.set_timeout(60)
        await form.set_color("0xa68bd3")
        result = await form.start()
        previous = True if result.season == '上季' else False
        msg = await ctx.send('讀取中...')
        result = await genshin_app.getAbyss(member.id, previous)
        await msg.delete()
        paginator = DiscordUtils.Pagination.CustomEmbedPaginator(
            ctx, remove_reactions=True)
        paginator.add_reaction('⏮️', "first")
        paginator.add_reaction('◀', "back")
        paginator.add_reaction('▶', "next")
        paginator.add_reaction('⏭️', "last")
        await paginator.run(result)

    @commands.command(hidden=True)
    @commands.has_role("小雪團隊")
    async def newuser(self, ctx):
        with open(f'data/accounts.yaml', encoding='utf-8') as file:
            users = yaml.full_load(file)
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
        client = genshin.Client(cookies)
        client.lang = "zh-tw"
        client.default_game = genshin.Game.GENSHIN
        failed = False
        notPublic = False
        try:
            await client.get_notes(uid)
        except genshin.errors.InvalidCookies:
            failed = True
        except genshin.errors.DataNotPublic:
            notPublic = True
        if not failed:
            if notPublic:
                await ctx.send(f"該帳號資料未公開, 輸入`!stuck`來獲取更多資訊")
            users[int(result.discordID)] = {'name': result.name, 'uid': int(
                result.uid), 'ltoken': result.ltoken, 'ltuid': int(result.ltuid), 'dm': True, 'dmCount': 0, 'dmDate': dateNow}
            with open(f'data/accounts.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(users, file)
            await ctx.send(f"已新增該帳號")
        else:
            await ctx.send("帳號資料錯誤，請檢查是否有輸入錯誤")

    @commands.command(name='register',aliases=['reg'],help='查看註冊原神帳號教學')
    async def _register(self, ctx):
        embed = defaultEmbed('註冊教學', 
            '1. PC或手機使用瀏覽器(不支援Safari,建議使用chrome)\n'
            '開啟Hoyolab登入帳號 https://www.hoyolab.com/\n'
            '2. 在網址列上輸入`java`\n'
            '3. 貼上下方的程式碼, 確保網址開頭變成 `javascript:`\n'
            "```script:d=document.cookie; c=d.includes('account_id') || alert('過期或無效的Cookie,請先登出帳號再重新登入!'); c && document.write(d)```"
            '4. ctrl+A全選並ctrl+C複製後將內容私訊給<@410036441129943050>或<@665092644883398671>\n'
            '並附上原神UID及想要的使用者名稱'
        )
        await ctx.send(embed=embed)

    @commands.command(name='stuck',help='找不到原神帳號資料?')
    async def _stuck(self, ctx):
        embed = defaultEmbed(
            "已經註冊,但有些資料找不到?", "1. 至hoyolab網頁中\n2. 點擊頭像\n3. personal homepage\n4. 右邊會看到genshin impact\n5. 點擊之後看到設定按鈕\n6. 打開 Do you want to enable real time-notes")
        setFooter(embed)
        await ctx.send(embed=embed)

    @commands.command(name='dm',help='查看私訊功能介紹\n`!dm on`或`!dm off`來開關私訊功能')
    async def _dm(self, ctx, *, arg=''):
        with open(f'data/accounts.yaml', encoding='utf-8') as file:
            users = yaml.full_load(file)
        if arg == "":
            embed = defaultEmbed(
                "什麼是私訊提醒功能？", "申鶴每一小時會檢測一次你的樹脂數量, 當超過140的時候,\n申鶴會私訊提醒你,最多提醒三次\n註: 只有已註冊的用戶能享有這個功能")
            setFooter(embed)
            await ctx.send(embed=embed)
        elif arg == "on":
            userID = ctx.author.id
            if userID in users:
                users[userID]['dm'] = True
                with open(f'data/accounts.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(users, file)
                await ctx.send(f"已開啟 {users[userID]['name']} 的私訊功能")
        elif arg == "off":
            userID = ctx.author.id
            if userID in users:
                users[userID]['dm'] = False
                with open(f'data/accounts.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(users, file)
                await ctx.send(f"已關閉 {users[userID]['name']} 的私訊功能")

    @commands.command(name='farm', aliases=['f'], help='顯示今日原神可刷素材及對應角色')
    async def _farm(self, ctx):
        chineseNumber = ['一','二','三','四','五','六','日']
        weekdayGet = datetime.today().weekday()
        weekday = "禮拜"+chineseNumber[weekdayGet]
        embedFarm = defaultEmbed(f"今天({weekday})可以刷的副本材料", " ")
        if weekdayGet == 0 or weekdayGet == 3:
            embedFarm.set_image(
                url="https://media.discordapp.net/attachments/823440627127287839/958862746349346896/73268cfab4b4a112.png")
        elif weekdayGet == 1 or weekdayGet == 4:
            embedFarm.set_image(
                url="https://media.discordapp.net/attachments/823440627127287839/958862746127060992/5ac261bdfc846f45.png")
        elif weekdayGet == 2 or weekdayGet == 5:
            embedFarm.set_image(
                url="https://media.discordapp.net/attachments/823440627127287839/958862745871220796/0b16376c23bfa1ab.png")
        elif weekdayGet == 6:
            embedFarm = defaultEmbed(
                f"今天({weekday})可以刷的副本材料", "禮拜日可以刷所有素材 (❁´◡`❁)")
        setFooter(embedFarm)
        await ctx.send(embed=embedFarm)

    def saveUserData(self, data:dict):
        with open('data/accounts.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(data, f)


def setup(bot):
    bot.add_cog(GenshinCog(bot))
