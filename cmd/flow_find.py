from discord.ext.forms import Form, ReactionForm
from discord.ext import commands
import yaml
from cmd.asset.global_vars import defaultEmbed, setFooter
import discord

with open(f'cmd/asset/flow.yaml', encoding='utf-8') as file:
    users = yaml.full_load(file)
with open(f'cmd/asset/find.yaml', encoding='utf-8') as file:
    finds = yaml.full_load(file)
with open(f'cmd/asset/confirm.yaml', encoding='utf-8') as file:
    confirms = yaml.full_load(file)


class FlowFindCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id == 965143582178705459 or payload.message_id == 963972447600771092:
            return
        channel = self.bot.get_channel(payload.channel_id)
        message = channel.get_partial_message(payload.message_id)
        reaction = discord.utils.get(message.reactions, emoji='✅')
        discordID = payload.user_id
        if discordID not in users:
            user = self.bot.get_user(payload.user_id)
            flowCog = self.bot.get_cog('FlowCog')
            await flowCog.register(channel, user, discordID)
            return
        if payload.emoji.name == '✅' and payload.user_id != self.bot.user.id and message.reactions[0].count != 2:
            if payload.message_id in finds:
                if payload.user_id == finds[payload.message_id]['authorID']:
                    userObj = self.bot.get_user(payload.use_id)
                    await channel.send(f"{userObj.mention}不可以自己接自己的委託啦", delete_after=2)
                    await reaction.remove(payload.member)
                    return
                else:
                    await message.clear_reaction('✅')
                    author = self.bot.get_user(
                        finds[payload.message_id]['authorID'])
                    acceptUser = self.bot.get_user(payload.user_id)
                    if finds[payload.message_id]['type'] == 1:
                        await author.send(f"[成功接受委託] {acceptUser.mention} 接受了你的 {finds[payload.message_id]['title']} 委託")
                        await acceptUser.send(f"[成功接受委託] 你接受了 {author.mention} 的 {finds[payload.message_id]['title']} 委託")
                        await channel.send(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {finds[payload.message_id]['title']} 委託")
                    elif finds[payload.message_id]['type'] == 2:
                        await author.send(f"[成功接受素材委託] {acceptUser.mention} 接受了你的 {finds[payload.message_id]['title']} 素材委託")
                        await acceptUser.send(f"[成功接受素材委託] 你接受了 {author.mention} 的 {finds[payload.message_id]['title']} 素材委託")
                        await channel.send(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {finds[payload.message_id]['title']} 素材委託")
                    elif finds[payload.message_id]['type'] == 3:
                        await author.send(f"[成功接受委託] {acceptUser.mention} 接受了你的 {finds[payload.message_id]['title']} 委託")
                        await acceptUser.send(f"[成功接受委託] 你接受了 {author.mention} 的 {finds[payload.message_id]['title']} 委託")
                        await channel.send(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {finds[payload.message_id]['title']} 委託")
                    elif finds[payload.message_id]['type'] == 4:
                        await author.send(f"✅ {acceptUser.mention} 接受了你的 {finds[payload.message_id]['title']} 幫助")
                        await acceptUser.send(f"✅ 你接受了 {author.mention} 的 {finds[payload.message_id]['title']} 幫助")
                        await channel.send(f"✅ {acceptUser.mention} 接受 {author.mention} 的 {finds[payload.message_id]['title']} 幫助")

                    if finds[payload.message_id]['type'] == 4:
                        embedDM = defaultEmbed(
                            "結算單", f"當對方完成幫忙的內容時, 請按 🆗來結算flow幣\n按下後, 你的flow幣將會 **- {finds[payload.message_id]['flow']}**, 對方則會 **+ {finds[payload.message_id]['flow']}**")
                        setFooter(embedDM)
                        dm = await acceptUser.send(embed=embedDM)
                    else:
                        embedDM = defaultEmbed(
                            "結算單", f"當對方完成委託的內容時, 請按 🆗來結算flow幣\n按下後, 你的flow幣將會 **- {finds[payload.message_id]['flow']}**, 對方則會 **+ {finds[payload.message_id]['flow']}**")
                        setFooter(embedDM)
                        dm = await author.send(embed=embedDM)
                    await dm.add_reaction('🆗')

                    del finds[payload.message_id]
                    with open(f'cmd/asset/find.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(finds, file)
                    confirms[dm.id] = {'title': finds[payload.message_id]['title'], 'authorID': int(
                        finds[payload.message_id]['authorID']), 'receiverID': payload.user_id, 'flow': finds[payload.message_id]['flow'], 'type': finds[payload.message_id]['type']}
                    with open(f'cmd/asset/confirm.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(confirms, file)

    @commands.command()
    async def find(self, ctx):
        if ctx.channel.id != 960861105503232030:
            channel = self.bot.get_channel(960861105503232030)
            await ctx.send(f"請在{channel.mention}裡使用此指令")
            return
        await ctx.message.delete()
        discordID = ctx.author.id
        if discordID not in users:
            user = self.bot.get_user(discordID)
            flowCog = self.bot.get_cog('FlowCog')
            await flowCog.register(ctx, user, discordID)
            return
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

        guild = self.bot.get_guild(916838066117824553)
        role = discord.utils.get(guild.roles, name=f"委託通知")

        if choice == 1:
            await message.delete()
            formTrue = Form(ctx, '設定流程', cleanup=True)
            formTrue.add_question('需要什麼幫助?(例如: 打刀鐔)', 'title')
            formTrue.add_question('你要付多少flow幣給幫你的人?', 'flow')
            formTrue.edit_and_delete(True)
            formTrue.set_timeout(30)
            await formTrue.set_color("0xa68bd3")
            result = await formTrue.start()

            if int(result.flow) < 0:
                embedResult = defaultEmbed(
                    f"發布失敗, 請輸入大於1的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return
            if users[discordID]['flow'] < int(result.flow):
                embedResult = defaultEmbed(
                    f"發布失敗, 請勿輸入大於自己擁有數量的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return

            embed = defaultEmbed(
                f"請求幫助: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n世界等級: >={roleStr}\n按 ✅ 來接受委託")
            setFooter(embed)
            message = await ctx.send(embed=embed)
            await message.add_reaction('✅')
            await ctx.send(role.mention)
            finds[message.id] = {'title': result.title, 'flow': int(
                result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 1}
            with open(f'cmd/asset/find.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(finds, file)

        elif choice == 2:
            await message.delete()
            formFalse = Form(ctx, '設定流程', cleanup=True)
            formFalse.add_question('需要什麼素材?(例如: 緋櫻繡球)', 'title')
            formFalse.add_question('你要付多少flow幣給讓你拿素材的人?', 'flow')
            formFalse.edit_and_delete(True)
            formFalse.set_timeout(30)
            await formFalse.set_color("0xa68bd3")
            result = await formFalse.start()

            if int(result.flow) < 0:
                embedResult = defaultEmbed(
                    f"發布失敗, 請輸入大於1的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return
            if users[discordID]['flow'] < int(result.flow):
                embedResult = defaultEmbed(
                    f"發布失敗, 請勿輸入大於自己擁有數量的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return

            embed = defaultEmbed(
                f"素材請求: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n世界等級: <={roleStr}\n按 ✅ 來接受請求")
            setFooter(embed)
            message = await ctx.send(embed=embed)
            await message.add_reaction('✅')
            await ctx.send(role.mention)
            finds[message.id] = {'title': result.title, 'flow': int(
                result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 2}
            with open(f'cmd/asset/find.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(finds, file)

        elif choice == 3:
            await message.delete()
            formFalse = Form(ctx, '設定流程', cleanup=True)
            formFalse.add_question('要委託什麼?', 'title')
            formFalse.add_question('你要付多少flow幣給接受委託的人?', 'flow')
            formFalse.edit_and_delete(True)
            formFalse.set_timeout(30)
            await formFalse.set_color("0xa68bd3")
            result = await formFalse.start()
            
            if int(result.flow) < 0:
                embedResult = defaultEmbed(
                    f"發布失敗, 請輸入大於1的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return
            if users[discordID]['flow'] < int(result.flow):
                embedResult = defaultEmbed(
                    f"發布失敗, 請勿輸入大於自己擁有數量的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return

            embed = defaultEmbed(
                f"委託: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n按 ✅ 來接受請求")
            setFooter(embed)
            message = await ctx.send(embed=embed)
            await message.add_reaction('✅')
            await ctx.send(role.mention)
            finds[message.id] = {'title': result.title, 'flow': int(result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 3}
            with open(f'cmd/asset/find.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(finds, file)

        elif choice == 4:
            await message.delete()
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
            if users[discordID]['flow'] < int(result.flow):
                embedResult = defaultEmbed(
                    f"發布失敗, 請勿輸入大於自己擁有數量的flow幣", " ")
                setFooter(embedResult)
                message = await ctx.send(embed=embedResult)
                return

            embedResult = defaultEmbed(
                f"可以幫忙: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n按 ✅ 來接受幫助")
            setFooter(embedResult)
            message = await ctx.send(embed=embedResult)
            await message.add_reaction('✅')
            await ctx.send(role.mention)
            finds[message.id] = {'title': result.title, 'flow': int(result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 4}
            with open(f'cmd/asset/find.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(finds, file)


def setup(bot):
    bot.add_cog(FlowFindCog(bot))
