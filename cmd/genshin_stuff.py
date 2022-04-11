import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import genshin, discord, DiscordUtils, yaml
import global_vars
global_vars.Global()
from classes import Character
from discord.ext import commands
import psyco
psyco.full()

with open(f'C:/Users/{owner}/shenhe_bot/asset/accounts.yaml', encoding = 'utf-8') as file:
    users = yaml.full_load(file)

class GenshinCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def check(self, ctx, *, name: discord.Member = None):
        name = name or ctx.author
        found = False
        for user in users:
            if name.id==user['discordID']:
                found = True
                cookies = {"ltuid": user['ltuid'], "ltoken": user['ltoken']}
                uid = user['uid']
                username = user['name']
                break
        if found == False:
            embed = global_vars.embedNoAccount
            global_vars.setFooter(embed)
            await ctx.send(embed=embed)
            return
        # 從cookie取得資料
        client = genshin.GenshinClient(cookies)
        client.lang = "zh-tw"
        notes = await client.get_notes(uid)
        # 有沒有做派遣?
        # 無
        if not notes.expeditions:
            hr = 0
            mn = 0
            exTime = 0
        # 有
        else:
            unfinExp = []
            for expedition in notes.expeditions:
                if(expedition.status=="Ongoing"):
                    unfinExp.append(expedition.remaining_time)
            #全部的派遣都做完了嗎?
            # 對
            if not unfinExp:
                hr = 0
                mn = 0
            # 還沒, 計算最快剩餘時間
            else:
                exTime = min(unfinExp, default="EMPTY")
                hr, mn = divmod(exTime // 60,60)
        # 計算樹脂填滿剩餘時間
        time = notes.until_resin_recovery
        hours, minutes = divmod(time // 60, 60)
        # 送出結果embed
        embedCheck=global_vars.defaultEmbed(f"使用者: {username}",f"<:resin:956377956115157022> 目前樹脂: {notes.current_resin}/{notes.max_resin}\n於 {hours:.0f} 小時 {minutes:.0f} 分鐘後填滿\n<:daily:956383830070140938> 已完成的每日數量: {notes.completed_commissions}/{notes.max_comissions}\n<:realm:956384011750613112> 目前塵歌壺幣數量: {notes.current_realm_currency}/{notes.max_realm_currency}\n<:expedition:956385168757780631> 已結束的探索派遣數量: {sum(expedition.finished for expedition in notes.expeditions)}/{len(notes.expeditions)}\n最快結束的派遣時間: {hr:.0f}小時 {mn:.0f}分鐘")
        global_vars.setFooter(embedCheck)
        await ctx.send(embed=embedCheck)
        await client.close()
    @commands.command()
    async def stats(self, ctx, *, name: discord.Member = None):
        name = name or ctx.author
        found = False
        for user in users:
            if name.id==user['discordID']:
                found = True
                cookies = {"ltuid": user['ltuid'], "ltoken": user['ltoken']}
                uid = user['uid']
                username = user['name']
                break
        if found == False:
            embed = global_vars.embedNoAccount
            global_vars.setFooter(embed)
            await ctx.send(embed=embed)
            return
        #取得資料
        client = genshin.GenshinClient(cookies)
        client.lang = "zh-tw"
        genshinUser = await client.get_partial_user(uid)
        days = genshinUser.stats.days_active
        char = genshinUser.stats.characters
        achieve = genshinUser.stats.achievements
        anemo = genshinUser.stats.anemoculi
        geo = genshinUser.stats.geoculi
        electro = genshinUser.stats.electroculi
        comChest = genshinUser.stats.common_chests
        exChest = genshinUser.stats.exquisite_chests
        luxChest = genshinUser.stats.luxurious_chests
        abyss = genshinUser.stats.spiral_abyss
        waypoint = genshinUser.stats.unlocked_waypoints
        embedStats=global_vars.defaultEmbed(f"使用者: {username}", 
            f":calendar: 活躍天數: {days}\n<:expedition:956385168757780631> 角色數量: {char}/48\n📜 成就數量:{achieve}/586\n🗺 已解鎖傳送錨點數量: {waypoint}\n🌙 深淵已達: {abyss}層\n<:anemo:956719995906322472> 風神瞳: {anemo}/66\n<:geo:956719995440730143> 岩神瞳: {geo}/131\n<:electro:956719996262821928> 雷神瞳: {electro}/181\n⭐ 一般寶箱: {comChest}\n🌟 稀有寶箱: {exChest}\n✨ 珍貴寶箱: {luxChest}")
        global_vars.setFooter(embedStats)
        await ctx.send(embed=embedStats)
        await client.close()
    @commands.command()
    async def area(self, ctx, *, name: discord.Member = None):
        name = name or ctx.author
        name = name or ctx.author
        found = False
        for user in users:
            if name.id==user['discordID']:
                found = True
                cookies = {"ltuid": user['ltuid'], "ltoken": user['ltoken']}
                uid = user['uid']
                username = user['name']
                break
        if found == False:
            embed = global_vars.embedNoAccount
            global_vars.setFooter(embed)
            await ctx.send(embed=embed)
            return
        #取得資料
        client = genshin.GenshinClient(cookies)
        client.lang = "zh-tw"
        genshinUser = await client.get_partial_user(uid)
        explorations = genshinUser.explorations
        exploreStr = ""
        offeringStr = ""
        for exploration in explorations:
            name = exploration.name 
            percentage = exploration.percentage
            offerings = exploration.offerings
            exploreStr += f"{name}: {percentage}%\n"
            for offering in offerings:
                offeringName = offering.name 
                offeringLevel = offering.level
                offeringStr += f"{offeringName}: Lvl {offeringLevel}\n"
        embed = global_vars.defaultEmbed(f"區域探索度: {username}",f"{exploreStr}\n{offeringStr}")
        global_vars.setFooter(embed)
        await ctx.send(embed=embed)
        await client.close()

    @commands.command()
    async def claim(self, ctx, *, name=''):
        # 有無輸入參數?
        # claim all
        if name=='all':
            author = ctx.author.id
            for user in users:
                cookies = {"ltuid": user['ltuid'], "ltoken": user['ltoken']}
                username = user['name']
                client = genshin.GenshinClient(cookies)
                client.lang = "zh-tw"
                signed_in, claimed_rewards = await client.get_reward_info()
                # 領獎勵
                try:
                    reward = await client.claim_daily_reward()
                except genshin.AlreadyClaimed:
                    embed = global_vars.defaultEmbed(f"使用者: {username}",f"❌ 已經拿過今天的每日獎勵啦! 貪心鬼<@{author}>\n📘 這個月已領取的每日獎勵數量: {claimed_rewards}")
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
                else:
                    embed = global_vars.defaultEmbed(f"使用者: {username}",f"✅ 幫你拿到了 {reward.amount}x {reward.name}\n📘 這個月已領取的每日獎勵數量: {claimed_rewards}")
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
                await client.close()
        # 非all
        elif name != "all":
            # !claim name
            if name != "":
                found = False
                for user in users:
                    if name == "<@!"+str(user['discordID'])+">":
                        found = True
                        cookies = {"ltuid": user['ltuid'], "ltoken": user['ltoken']}
                        uid = user['uid']
                        username = user['name']
                        break
                if found == False:
                    embed = global_vars.embedNoAccount
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
            # !claim blank
            elif name == "":
                found = False
                for user in users:
                    if ctx.author.id==user['discordID']:
                        found = True
                        cookies = {"ltuid": user['ltuid'], "ltoken": user['ltoken']}
                        uid = user['uid']
                        username = user['name']
                        break
                if found == False:
                    embed = global_vars.embedNoAccount
                    global_vars.setFooter(embed)
                    await ctx.send(embed=embed)
            # 取得資料
            client = genshin.GenshinClient(cookies)
            client.lang = "zh-tw"
            signed_in, claimed_rewards = await client.get_reward_info()
            # 領取每日獎勵
            try:
                reward = await client.claim_daily_reward()
            except genshin.AlreadyClaimed:
                embed = global_vars.defaultEmbed(f"使用者: {username}",f"❌ 已經拿過今天的每日獎勵啦! 貪心鬼{username}\n📘 這個月已領取的每日獎勵數量: {claimed_rewards}")
                global_vars.setFooter(embed)
                await ctx.send(embed=embed)
            else:
                embed = global_vars.defaultEmbed(f"使用者: {username}",f"✅ 幫你拿到了 {reward.amount}x {reward.name}\n📘 這個月已領取的每日獎勵數量: {claimed_rewards}")
                global_vars.setFooter(embed)
                await ctx.send(embed=embed)
        await client.close()
    @commands.command()
    async def abyss(self, ctx, *, name: discord.Member = None):
        name = name or ctx.author
        found = False
        for user in users:
            if name.id==user['discordID']:
                found = True
                cookies = {"ltuid": user['ltuid'], "ltoken": user['ltoken']}
                uid = user['uid']
                username = user['name']
                break
        if found == False:
            embed = global_vars.embedNoAccount
            global_vars.setFooter(embed)
            await ctx.send(embed=embed)
            return
        try:
            #obtaining data
            client = genshin.GenshinClient(cookies)
            client.lang = "zh-tw"
            abyss = await client.get_spiral_abyss(uid)
            strongestStrike = abyss.ranks.strongest_strike
            mostKill = abyss.ranks.most_kills
            mostPlayed = abyss.ranks.most_played
            mostBurst = abyss.ranks.most_bursts_used
            mostSkill = abyss.ranks.most_skills_used
            mBurst = mostBurst[0].value
            mBurstChar = mostBurst[0].name
            mSkill = mostSkill[0].value
            mSkillChar = mostSkill[0].name
            mKill = mostKill[0].value
            mKillChar = mostKill[0].name
            mPlay = mostPlayed[0].value
            mPlayChar = mostPlayed[0].name
            dmg = strongestStrike[0].value
            dmgChar = strongestStrike[0].name
        except IndexError:
            embed = global_vars.defaultEmbed("找不到資料!", "可能是因為你還沒打深淵, 輸入`!stats`來看看你打到幾層了")
            global_vars.setFooter(embed)
            await ctx.send(embed=embed)
            await client.close()
        embedAbyss=global_vars.defaultEmbed(f"深境螺旋: {username}",f"💥 最高單次傷害角色: {dmgChar}, {dmg}點傷害\n☠ 擊殺王: {mKillChar}, {mKill}個擊殺\n🎄 最常使用角色: {mPlayChar}, {mPlay}次\n🇶 最多大招使用角色: {mBurstChar}, {mBurst}次\n🇪 最多小技能使用角色: {mSkillChar}, {mSkill}次")
        global_vars.setFooter(embedAbyss)
        await ctx.send(embed=embedAbyss)
        await client.close()
    @commands.command()
    async def diary(self, ctx, *, name: discord.Member = None): 
        name = name or ctx.author
        found = False
        for user in users:
            if name.id==user['discordID']:
                found = True
                cookies = {"ltuid": user['ltuid'], "ltoken": user['ltoken']}
                uid = user['uid']
                username = user['name']
                break
        if found == False:
            embed = global_vars.embedNoAccount
            global_vars.setFooter(embed)
            await ctx.send(embed=embed)
            return
        # 取得資料
        client = genshin.GenshinClient(cookies)
        client.lang = "zh-tw"
        diary = await client.get_diary()
        primoCategoryStr = ""
        for category in diary.data.categories:
            primoCategoryStr = primoCategoryStr + f"{category.percentage}%: {category.name} ({category.amount} 原石)" + "\n"
        embedDiary = global_vars.defaultEmbed(f"原石與摩拉收入: {username}",f"<:mora:958577933650362468> **這個月獲得的摩拉數量: {diary.data.current_mora}**")
        embedDiary.add_field(name=f"<:primo:958555698596290570> 這個月獲得的原石數量: {diary.data.current_primogems}", value=f"收入分類: \n{primoCategoryStr}")
        global_vars.setFooter(embedDiary)
        await ctx.send(embed=embedDiary)
        await client.close()
    @commands.command()
    async def log(self, ctx, *, name: discord.Member = None): 
        name = name or ctx.author
        found = False
        for user in users:
            if name.id==user['discordID']:
                found = True
                cookies = {"ltuid": user['ltuid'], "ltoken": user['ltoken']}
                uid = user['uid']
                username = user['name']
                break
        if found == False:
            embed = global_vars.embedNoAccount
            global_vars.setFooter(embed)
            await ctx.send(embed=embed)
            return
        # 取得資料
        client = genshin.GenshinClient(cookies)
        client.lang = "zh-tw"
        diary = await client.get_diary()
        primoLog = ""
        moraLog = ""
        async for action in client.diary_log(limit=25):
            primoLog = primoLog+f"{action.action} - {action.amount} 原石"+"\n"
        async for action in client.diary_log(mora=True, limit=25):
            moraLog = moraLog+f"{action.action} - {action.amount} 摩拉"+"\n"
        embedPrimo = global_vars.defaultEmbed(f"<:primo:958555698596290570> 最近25筆原石紀錄",f"{primoLog}")
        global_vars.setFooter(embedPrimo)
        embedMora = global_vars.defaultEmbed(f"<:mora:958577933650362468> 最近25筆摩拉紀錄",f"{moraLog}")
        global_vars.setFooter(embedMora)
        await client.close()
        paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx, remove_reactions=True)
        paginator.add_reaction('◀', "back")
        paginator.add_reaction('▶', "next")
        embeds = [embedPrimo, embedMora]
        await paginator.run(embeds)
        await client.close()
    @commands.command()
    async def char(self, ctx, *, name: discord.Member = None):
        name = name or ctx.author
        found = False
        for user in users:
            if name.id==user['discordID']:
                found = True
                cookies = {"ltuid": user['ltuid'], "ltoken": user['ltoken']}
                uid = user['uid']
                username = user['name']
                break
        if found == False:
            embed = global_vars.embedNoAccount
            global_vars.setFooter(embed)
            await ctx.send(embed=embed)
            return
        # 取得資料
        client = genshin.GenshinClient(cookies)
        client.lang = "zh-tw"
        char = await client.get_characters(uid)
        clientCharacters = []
        charEmbeds = []
        for character in char:
            weapon = character.weapon
            artifacts = character.artifacts
            artifactList = []
            artifactIconList = []
            for artifact in artifacts:
                artifactList.append(artifact.name)
                artifactIconList.append(artifact.icon)
            clientCharacters.append(Character(character.name,character.level,character.constellation,character.icon, character.friendship, weapon.name, weapon.refinement, weapon.level, artifactList, artifactIconList))
        for character in clientCharacters:
            artifactStr = ""
            for artifact in character.artifacts:
                artifactStr = artifactStr + "- " + artifact + "\n"
            embedChar = global_vars.defaultEmbed(f"{character.name}: C{character.constellation} R{character.refinement}", f"Lvl {character.level}\n好感度 {character.friendship}\n武器 {character.weapon}, lvl{character.weaponLevel}\n{artifactStr}")
            embedChar.set_thumbnail(url=f"{character.iconUrl}")
            global_vars.setFooter(embedChar)
            charEmbeds.append(embedChar)
        paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx, remove_reactions=True)
        paginator.add_reaction('⏮️', "first")
        paginator.add_reaction('◀', "back")
        paginator.add_reaction('▶', "next")
        paginator.add_reaction('⏭️', "last")
        await paginator.run(charEmbeds)
        await client.close()

    @commands.command()
    async def users(self, ctx):
        userStr = ""
        for user in users:
            userStr = userStr+f"{user['name']} - {user['uid']}\n"
        embed = global_vars.defaultEmbed("所有帳號",userStr)
        global_vars.setFooter(embed)
        await ctx.send(embed=embed)

    @commands.command()
    async def today(self, ctx, *, name: discord.Member = None): 
        name = name or ctx.author
        found = False
        for user in users:
            if name.id==user['discordID']:
                found = True
                cookies = {"ltuid": user['ltuid'], "ltoken": user['ltoken']}
                uid = user['uid']
                username = user['name']
                break
        if found == False:
            embed = global_vars.embedNoAccount
            global_vars.setFooter(embed)
            await ctx.send(embed=embed)
            return
        # 取得資料
        client = genshin.GenshinClient(cookies)
        client.lang = "zh-tw"
        diary = await client.get_diary()
        # print(diary.day_data.)
        mora = diary.day_data.current_mora
        primo = diary.day_data.current_primogems
        embed = global_vars.defaultEmbed(f"今日收入: {username}",f"<:primo:958555698596290570> {primo}原石\n<:mora:958577933650362468> {mora}摩拉")
        global_vars.setFooter(embed)
        await ctx.send(embed=embed)
        await client.close()

def setup(bot):
    bot.add_cog(GenshinCog(bot))