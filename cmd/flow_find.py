from discord.ext.forms import Form, ReactionForm
from discord.ext import commands
import yaml
from asset.global_vars import defaultEmbed, setFooter
import discord

with open(f'asset/flow.yaml', encoding='utf-8') as file:
    users = yaml.full_load(file)
with open(f'asset/find.yaml', encoding='utf-8') as file:
    finds = yaml.full_load(file)
with open(f'asset/confirm.yaml', encoding='utf-8') as file:
    confirms = yaml.full_load(file)


class FlowFindCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id == 965143582178705459 or payload.message_id == 963972447600771092:
            return
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        reaction = discord.utils.get(message.reactions, emoji='✅')
        found = False
        for user in users:
            if user['discordID'] == payload.user_id:
                found = True
                break
        if found == False:
            dcUser = self.bot.get_user(payload.user_id)
            if not dcUser.bot:
                discordID = payload.user_id
                user = self.bot.get_user(payload.user_id)
                flowCog = self.bot.get_cog('FlowCog')
                await flowCog.register(user, discordID)

        if payload.emoji.name == '✅' and payload.user_id != self.bot.user.id and message.reactions[0].count != 2:
            for find in finds:
                if payload.message_id == find['msgID']:
                    for user in users:
                        if payload.user_id == find['authorID']:
                            userObj = self.bot.get_user(find['authorID'])
                            message = await channel.send(f"{userObj.mention}不可以自己接自己的委託啦", delete_after=2)
                            await reaction.remove(payload.member)
                            return
                        elif user['discordID'] == payload.user_id:
                            await message.clear_reaction('✅')
                            author = self.bot.get_user(find['authorID'])
                            acceptUser = self.bot.get_user(user['discordID'])
                            if find['type'] == 1:
                                await author.send(f"[成功接受委託] {acceptUser.mention} 接受了你的 {find['title']} 委託")
                                await acceptUser.send(f"[成功接受委託] 你接受了 {author.mention} 的 {find['title']} 委託")
                                await channel.send(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {find['title']} 委託")
                            elif find['type'] == 2:
                                await author.send(f"[成功接受素材委託] {acceptUser.mention} 接受了你的 {find['title']} 素材委託")
                                await acceptUser.send(f"[成功接受素材委託] 你接受了 {author.mention} 的 {find['title']} 素材委託")
                                await channel.send(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {find['title']} 素材委託")
                            elif find['type'] == 3:
                                await author.send(f"[成功接受委託] {acceptUser.mention} 接受了你的 {find['title']} 委託")
                                await acceptUser.send(f"[成功接受委託] 你接受了 {author.mention} 的 {find['title']} 委託")
                                await channel.send(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {find['title']} 委託")
                            elif find['type'] == 4:
                                await author.send(f"✅ {acceptUser.mention} 接受了你的 {find['title']} 幫助")
                                await acceptUser.send(f"✅ 你接受了 {author.mention} 的 {find['title']} 幫助")
                                await channel.send(f"✅ {acceptUser.mention} 接受 {author.mention} 的 {find['title']} 幫助")
                            if find['type'] == 4:
                                embedDM = defaultEmbed(
                                    "結算單", f"當對方完成幫忙的內容時, 請按 🆗來結算flow幣\n按下後, 你的flow幣將會 **- {find['flow']}**, 對方則會 **+ {find['flow']}**")
                                setFooter(embedDM)
                                dm = await acceptUser.send(embed=embedDM)
                            else:
                                embedDM = defaultEmbed(
                                    "結算單", f"當對方完成委託的內容時, 請按 🆗來結算flow幣\n按下後, 你的flow幣將會 **- {find['flow']}**, 對方則會 **+ {find['flow']}**")
                                setFooter(embedDM)
                                dm = await author.send(embed=embedDM)
                            await dm.add_reaction('🆗')

                            finds.remove(find)
                            with open(f'asset/find.yaml', 'w', encoding='utf-8') as file:
                                yaml.dump(finds, file)

                            newConfirm = {'title': find['title'], 'authorID': int(find['authorID']),
                                          'receiverID': int(user['discordID']), 'flow': find['flow'], 'msgID': dm.id, 'dm': find['type']}
                            confirms.append(newConfirm)
                            with open(f'asset/confirm.yaml', 'w', encoding='utf-8') as file:
                                yaml.dump(confirms, file)
                            return

    @commands.command()
    async def find(self, ctx):
        if ctx.channel.id != 960861105503232030:
            channel = self.bot.get_channel(960861105503232030)
            await ctx.send(f"請在{channel.mention}裡使用此指令")
            return
        await ctx.message.delete()
        found = False
        for user in users:
            if user['discordID'] == ctx.author.id:
                found = True
        if found == False and ctx.author.bot == False:
            discordID = ctx.author.id
            user = self.bot.get_user(discordID)
            flowCog = self.bot.get_cog('FlowCog')
            await flowCog.register(user, discordID)
        roles = []
        for i in range(1, 9):
            roles.append(discord.utils.get(ctx.guild.roles, name=f"W{str(i)}"))
            i += 1
        roleForChannel = self.bot.get_channel(962311051683192842)
        roleStr = f'請至{roleForChannel.mention}選擇身份組'
        for role in roles:
            if role in ctx.author.roles:
                roleStr = role.name
                break
        embed = defaultEmbed("請選擇委託類別",
                             "1️⃣: 其他玩家進入你的世界(例如: 陪玩, 打素材等)\n2️⃣: 你進入其他玩家的世界(例如: 拿特產)\n3️⃣: 其他委託\n4️⃣: 可以幫助別人(讓拿素材, 可幫打刀鐔等)")
        message = await ctx.send(embed=embed)
        form = ReactionForm(message, self.bot, ctx.author)
        form.add_reaction("1️⃣", 1)
        form.add_reaction("2️⃣", 2)
        form.add_reaction("3️⃣", 3)
        form.add_reaction("4️⃣", 4)
        choice = await form.start()

        if choice == 1:
            def is_me(m):
                return m.author == self.bot.user
            await ctx.channel.purge(limit=1, check=is_me)
            formTrue = Form(ctx, '設定流程', cleanup=True)
            formTrue.add_question('需要什麼幫助?(例如: 打刀鐔)', 'title')
            formTrue.add_question('你要付多少flow幣給幫你的人?', 'flow')
            formTrue.edit_and_delete(True)
            formTrue.set_timeout(60)
            await formTrue.set_color("0xa68bd3")
            result = await formTrue.start()
            if int(result.flow) < 0:
                embedResult = defaultEmbed(
                    f"發布失敗, 請輸入大於1的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return
            for user in users:
                if ctx.author.id == user['discordID'] and int(result.flow) > user['flow']:
                    embedResult = defaultEmbed(
                        f"發布失敗, 請勿輸入大於自己擁有數量的flow幣", " ")
                    setFooter(embedResult)
                    message = await ctx.send(embed=embedResult)
                    return

            guild = self.bot.get_guild(916838066117824553)
            role = discord.utils.get(guild.roles, name=f"委託通知")
            embed = defaultEmbed(
                f"請求幫助: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n世界等級: >={roleStr}\n按 ✅ 來接受委託")
            setFooter(embed)
            message = await ctx.send(embed=embed)
            await message.add_reaction('✅')
            await ctx.send(role.mention)
            newFind = {'title': str(result.title), 'msgID': int(message.id), 'flow': int(
                result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 1}
            finds.append(newFind)
            with open(f'asset/find.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(finds, file)

        elif choice == 2:
            def is_me(m):
                return m.author == self.bot.user
            await ctx.channel.purge(limit=1, check=is_me)
            formFalse = Form(ctx, '設定流程', cleanup=True)
            formFalse.add_question('需要什麼素材?(例如: 緋櫻繡球)', 'title')
            formFalse.add_question('你要付多少flow幣給讓你拿素材的人?', 'flow')
            formFalse.edit_and_delete(True)
            formFalse.set_timeout(60)
            await formFalse.set_color("0xa68bd3")
            result = await formFalse.start()
            if int(result.flow) < 0:
                embedResult = defaultEmbed(
                    f"發布失敗, 請輸入大於1的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return
            for user in users:
                if ctx.author.id == user['discordID']:
                    if int(result.flow) > user['flow']:
                        embedResult = defaultEmbed(
                            f"發布失敗, 請勿輸入大於自己擁有數量的flow幣", " ")
                        setFooter(embedResult)
                        message = await ctx.send(embed=embedResult)
                        return

            guild = self.bot.get_guild(916838066117824553)
            role = discord.utils.get(guild.roles, name=f"委託通知")
            notifRole = self.bot.get
            embed = defaultEmbed(
                f"素材請求: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n世界等級: <={roleStr}\n按 ✅ 來接受請求")
            setFooter(embed)
            message = await ctx.send(embed=embed)
            await message.add_reaction('✅')
            await ctx.send(role.mention)
            newFind = {'title': str(result.title), 'msgID': int(message.id), 'flow': int(
                result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 2}
            finds.append(newFind)
            with open(f'asset/find.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(finds, file)

        elif choice == 3:
            def is_me(m):
                return m.author == self.bot.user
            await ctx.channel.purge(limit=1, check=is_me)
            formFalse = Form(ctx, '設定流程', cleanup=True)
            formFalse.add_question('要委託什麼?', 'title')
            formFalse.add_question('你要付多少flow幣給接受委託的人?', 'flow')
            formFalse.edit_and_delete(True)
            formFalse.set_timeout(60)
            await formFalse.set_color("0xa68bd3")
            result = await formFalse.start()
            if int(result.flow) < 0:
                embedResult = defaultEmbed(
                    f"發布失敗, 請輸入大於1的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return
            for user in users:
                if ctx.author.id == user['discordID']:
                    if int(result.flow) > user['flow']:
                        embedResult = defaultEmbed(
                            f"發布失敗, 請勿輸入大於自己擁有數量的flow幣", " ")
                        setFooter(embedResult)
                        message = await ctx.send(embed=embedResult)
                        return

            guild = self.bot.get_guild(916838066117824553)
            role = discord.utils.get(guild.roles, name=f"委託通知")
            embed = defaultEmbed(
                f"委託: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n按 ✅ 來接受請求")
            setFooter(embed)
            message = await ctx.send(embed=embed)
            await ctx.send(role.mention)
            await message.add_reaction('✅')
            newFind = {'title': str(result.title), 'msgID': int(message.id), 'flow': int(
                result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 3}
            finds.append(newFind)
            with open(f'asset/find.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(finds, file)

        elif choice == 4:
            def is_me(m):
                return m.author == self.bot.user
            await ctx.channel.purge(limit=1, check=is_me)
            formFalse = Form(ctx, '設定流程', cleanup=True)
            formFalse.add_question('你想要幫助什麼?', 'title')
            formFalse.add_question('被你幫助的人要付多少flow幣給你?', 'flow')
            formFalse.edit_and_delete(True)
            formFalse.set_timeout(60)
            await formFalse.set_color("0xa68bd3")
            result = await formFalse.start()
            if int(result.flow) < 0:
                embedResult = defaultEmbed(
                    f"發布失敗, 請輸入大於1的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return
            for user in users:
                if ctx.author.id == user['discordID']:
                    if int(result.flow) > user['flow']:
                        embedResult = defaultEmbed(
                            f"發布失敗, 請勿輸入大於自己擁有數量的flow幣", " ")
                        setFooter(embedResult)
                        message = await ctx.send(embed=embedResult)
                        return
            else:
                guild = self.bot.get_guild(916838066117824553)
                role = discord.utils.get(guild.roles, name=f"委託通知")
                embedResult = defaultEmbed(
                    f"可以幫忙: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n按 ✅ 來接受幫助")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                await ctx.send(role.mention)
                await message.add_reaction('✅')
                newFind = {'title': str(result.title), 'msgID': int(message.id), 'flow': int(
                    result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 4}
                finds.append(newFind)
                with open(f'asset/find.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(finds, file)


def setup(bot):
    bot.add_cog(FlowFindCog(bot))
