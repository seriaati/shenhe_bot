import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import os, discord, asyncio, genshin, yaml, datetime, time, DiscordUtils, uuid, inflect, emoji, re
import global_vars
global_vars.Global()
from discord.ext import commands
from discord.ext.forms import Form
from datetime import date
from discord.ext.forms import ReactionForm

with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', encoding = 'utf-8') as file:
	users = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/find.yaml', encoding = 'utf-8') as file:
	finds = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/confirm.yaml', encoding = 'utf-8') as file:
	confirms = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', encoding = 'utf-8') as file:
	bank = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/shop.yaml', encoding = 'utf-8') as file:
	shop = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/log.yaml', encoding = 'utf-8') as file:
	logs = yaml.full_load(file)

class FlowCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def register(name, id):
		dcUser = self.bot.get_user(id)
		if not dcUser.bot:
			today = date.today()
			newUser = {'name': str(name), 'discordID': int(id), 'flow': 100, 'morning': today}
			bank['flow'] -= 100
			users.append(newUser)
			with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
				yaml.dump(users, file)
			with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding = 'utf-8') as file:
				yaml.dump(bank, file)
		else:
			return

	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author == self.bot.user:
			return
		if "早安" in message.content:
			today = date.today()
			found = False
			for user in users:
				if message.author.id == user['discordID']:
					found = True
					if user['morning']!=today:
						user['flow'] += 1
						bank['flow'] -= 1
						user['morning'] = today
						with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
							yaml.dump(users, file)
						with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding = 'utf-8') as file:
							yaml.dump(bank, file)
						await message.add_reaction(f"☀️")
			if found == False:
				if not message.author.bot:
					discordID = message.author.id
					user = self.bot.get_user(message.author.id)
					register(user, discordID)
				else:
					return

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		# if payload.message_id == :

		if payload.message_id == 963972447600771092:
			for i in range(1, 9):
				p = inflect.engine()
				word = p.number_to_words(i)
				emojiStr = emoji.emojize(f":{word}:", language='alias')
				if payload.emoji.name == str(emojiStr):
					guild = self.bot.get_guild(payload.guild_id)
					member = guild.get_member(payload.user_id)
					role = discord.utils.get(guild.roles, name=f"W{i}")
					await member.add_roles(role)
					break
		else:
			channel = self.bot.get_channel(payload.channel_id)
			message = await channel.fetch_message(payload.message_id)
			reaction = discord.utils.get(message.reactions, emoji='✅')
			found = False
			for user in users:
				if user['discordID']==payload.user_id:
					found = True
					break
			if found == False:
				dcUser = self.bot.get_user(payload.user_id)
				if not dcUser.bot:
					discordID = payload.user_id
					user = self.bot.get_user(payload.user_id)
					register(user, discordID)
				else:
					return
				
			for find in finds:
				if payload.message_id == find['msgID'] and payload.emoji.name == '✅' and payload.user_id != self.bot.user.id:
					for user in users:
						if payload.user_id == find['authorID']:
							userObj = self.bot.get_user(find['authorID'])
							message = await channel.send(f"{userObj.mention}不可以自己接自己的委託啦")
							await reaction.remove(payload.member)
							return
						elif user['discordID'] == payload.user_id:
							await message.clear_reaction('✅')
							author = self.bot.get_user(find['authorID'])
							acceptUser = self.bot.get_user(user['discordID'])
							if find['type']==1:
								await author.send(f"[成功接受委託] {acceptUser.mention} 接受了你的 {find['title']} 委託")
								await acceptUser.send(f"[成功接受委託] 你接受了 {author.mention} 的 {find['title']} 委託")
								await channel.send(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {find['title']} 委託")
							elif find['type']==2:
								await author.send(f"[成功接受素材委託] {acceptUser.mention} 接受了你的 {find['title']} 素材委託")
								await acceptUser.send(f"[成功接受素材委託] 你接受了 {author.mention} 的 {find['title']} 素材委託")
								await channel.send(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {find['title']} 素材委託")
							elif find['type']==3:
								await author.send(f"[成功接受委託] {acceptUser.mention} 接受了你的 {find['title']} 委託")
								await acceptUser.send(f"[成功接受委託] 你接受了 {author.mention} 的 {find['title']} 委託")
								await channel.send(f"✅ {acceptUser.mention} 已接受 {author.mention} 的 {find['title']} 委託")
							elif find['type']==4:
								await author.send(f"✅ {acceptUser.mention} 接受了你的 {find['title']} 幫助")
								await acceptUser.send(f"✅ 你接受了 {author.mention} 的 {find['title']} 幫助")
								await channel.send(f"✅ {acceptUser.mention} 接受 {author.mention} 的 {find['title']} 幫助")
								return
							embedDM = global_vars.defaultEmbed("結算單","當對方完成委託的內容時, 請按 🆗來結算flow幣")
							global_vars.setFooter(embedDM)
							if find['type'] == 4:
								dm = await acceptUser.send(embed=embedDM)
								await dm.add_reaction('🆗')
							else:
								dm = await author.send(embed=embedDM)
								await dm.add_reaction('🆗')
							newConfirm = {'title': find['title'], 'authorID': int(find['authorID']), 
								'receiverID': int(user['discordID']), 'flow': find['flow'], 'msgID': dm.id, 'dm': find['type']}
							confirms.append(newConfirm)
							finds.remove(find)
							with open(f'C:/Users/{owner}/shenhe_bot/asset/confirm.yaml', 'w', encoding = 'utf-8') as file:
								yaml.dump(confirms, file)
							with open(f'C:/Users/{owner}/shenhe_bot/asset/find.yaml', 'w', encoding = 'utf-8') as file:
								yaml.dump(finds, file)
							return
			for confirm in confirms:
				if payload.message_id == confirm['msgID'] and payload.emoji.name == '🆗' and payload.user_id != self.bot.user.id:
					if confirm['dm'] == 4:
						for user in users:
							if user['discordID'] == confirm['authorID']:
								user['flow'] += confirm['flow']
							elif user['discordID'] == confirm['receiverID']:
								user['flow'] -= confirm['flow']
					else:
						for user in users:
							if user['discordID'] == confirm['authorID']:
								user['flow'] -= confirm['flow']
							elif user['discordID'] == confirm['receiverID']:
								user['flow'] += confirm['flow']
					author = self.bot.get_user(confirm['authorID'])
					receiver = self.bot.get_user(confirm['receiverID'])
					if confirm['dm'] == 4:
						embed = global_vars.defaultEmbed("🆗 結算成功", 
							f"委託名稱: {confirm['title']}\n委託人: {author.mention} **+{confirm['flow']} flow幣**\n接收人: {receiver.mention} **-{confirm['flow']} flow幣**")
					else:
						embed = global_vars.defaultEmbed("🆗 結算成功", 
							f"委託名稱: {confirm['title']}\n委託人: {author.mention} **-{confirm['flow']} flow幣**\n接收人: {receiver.mention} **+{confirm['flow']} flow幣**")
					global_vars.setFooter(embed)
					await author.send(embed=embed)
					await receiver.send(embed=embed)
					confirms.remove(confirm)
					with open(f'C:/Users/{owner}/shenhe_bot/asset/confirm.yaml', 'w', encoding = 'utf-8') as file:
						yaml.dump(confirms, file)
					with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
						yaml.dump(users, file)
					break

	@commands.Cog.listener()
	async def on_raw_reaction_remove(self, payload):
		if payload.message_id == 963972447600771092:
			for i in range(1, 9):
				p = inflect.engine()
				word = p.number_to_words(i)
				emojiStr = emoji.emojize(f":{word}:", language='alias')
				if payload.emoji.name == str(emojiStr):
					guild = self.bot.get_guild(payload.guild_id)
					member = guild.get_member(payload.user_id)
					role = discord.utils.get(guild.roles, name=f"W{i}")
					await member.remove_roles(role)
					break

	@commands.command()
	async def acc(self, ctx, *, member: discord.Member = None):
		member = member or ctx.author
		found = False
		for user in users:
			if user['discordID']==member.id:
				found = True
				embed = global_vars.defaultEmbed(f"使用者: {user['name']}",f"flow幣: {user['flow']}")
				global_vars.setFooter(embed)
				await ctx.send(embed=embed)
		if found == False:
			if not member.bot:
				discordID = member.id
				user = self.bot.get_user(discordID)
				register(user, discordID)
				await ctx.send("你本來沒有帳號, 現在申鶴幫你做了一個, 再打`!acc`一次試試看")
			else:
				return

	@commands.command()
	@commands.has_role("小雪團隊")
	async def roles(self, ctx):
		channel = self.bot.get_channel(962311051683192842)
		embed = global_vars.defaultEmbed("請選擇你的世界等級", " ")
		global_vars.setFooter(embed)
		message = await channel.send(embed=embed)
		for i in range(1, 9):
			p = inflect.engine()
			word = p.number_to_words(i)
			emojiStr = emoji.emojize(f":{word}:", language='alias')
			await message.add_reaction(str(emojiStr))

	@commands.command()
	@commands.has_role("小雪團隊")
	async def notif_roles(self, ctx):
		channel = self.bot.get_channel(962311051683192842)
		embed = global_vars.defaultEmbed("如果你想收到發布委託通知的話, 請選擇 <:Serialook:959100214747222067> 表情符號", " ")
		global_vars.setFooter(embed)
		message = await channel.send(embed=embed)
		await message.add_reaction("<:Serialook:959100214747222067>")

	@commands.command()
	async def find(self, ctx):
		if ctx.channel.id != 960861105503232030:
			channel = self.bot.get_channel(960861105503232030)
			await ctx.send(f"請在{channel.mention}裡使用此指令")
			return
		await ctx.message.delete()
		found = False
		for user in users:
			if user['discordID']==ctx.author.id:
				found = True
		if found == False:
			if not ctx.author.bot:
				discordID = ctx.author.id
				user = self.bot.get_user(discordID)
				register(user, discordID)
			else:
				return
		roles = []
		for i in range(1, 9):
			roles.append(discord.utils.get(ctx.guild.roles,name=f"W{str(i)}"))
			i += 1
		roleForChannel = self.bot.get_channel(962311051683192842)
		roleStr = f'請至{roleForChannel.mention}選擇身份組'
		for role in roles:
			if role in ctx.author.roles:
				roleStr = role.name
				break
		embed = global_vars.defaultEmbed("請選擇委託類別",
			"1️⃣: 其他玩家進入你的世界(例如: 陪玩, 打素材等)\n2️⃣: 你進入其他玩家的世界(例如: 拿特產)\n3️⃣: 其他委託\n4️⃣: 可以幫助別人(讓拿素材, 可幫打刀鐔等)")
		message = await ctx.send(embed=embed)
		form = ReactionForm(message,self.bot,ctx.author)
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
				embedResult = global_vars.defaultEmbed(f"發布失敗, 請輸入大於1的flow幣"," ")
				global_vars.setFooter(embedResult)
				message = await ctx.send(embed=embedResult)
				return
			for user in users:
				if ctx.author.id == user['discordID']:
					if int(result.flow) > user['flow']:
						embedResult = global_vars.defaultEmbed(f"發布失敗, 請勿輸入大於自己擁有數量的flow幣"," ")
						global_vars.setFooter(embedResult)
						message = await ctx.send(embed=embedResult)
						return
			else:
				tagStr = ""
				roleIndex = -1
				for role in roles:
					if role in ctx.author.roles:
						roleIndex = roles.index(role)
						break
				tagList = roles[roleIndex:]
				for role in tagList:
					tagStr += f"{role.mention} "
				embedResult = global_vars.defaultEmbed(f"請求幫助: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n世界等級: >={roleStr}\n按 ✅ 來接受委託")
				global_vars.setFooter(embedResult)
				message = await ctx.send(embed=embedResult)
				await message.add_reaction('✅')
				# await ctx.send(tagStr)
				newFind = {'title': str(result.title), 'msgID': int(message.id), 'flow': int(result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 1}
				finds.append(newFind)
				with open(f'C:/Users/{owner}/shenhe_bot/asset/find.yaml', 'w', encoding = 'utf-8') as file:
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
				embedResult = global_vars.defaultEmbed(f"發布失敗, 請輸入大於1的flow幣"," ")
				global_vars.setFooter(embedResult)
				message = await ctx.send(embed=embedResult)
				return
			for user in users:
				if ctx.author.id == user['discordID']:
					if int(result.flow) > user['flow']:
						embedResult = global_vars.defaultEmbed(f"發布失敗, 請勿輸入大於自己擁有數量的flow幣"," ")
						global_vars.setFooter(embedResult)
						message = await ctx.send(embed=embedResult)
						return
			else:
				tagStr = ""
				roleIndex = -1
				for role in roles:
					if role in ctx.author.roles:
						roleIndex = roles.index(role) + 1
						break
				tagList = roles[:roleIndex]
				for role in tagList:
					tagStr += f"{role.mention} "
				embedResult = global_vars.defaultEmbed(f"素材請求: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n世界等級: <={roleStr}\n按 ✅ 來接受請求")
				global_vars.setFooter(embedResult)
				message = await ctx.send(embed=embedResult)
				await message.add_reaction('✅')
				# await ctx.send(tagStr)
				newFind = {'title': str(result.title), 'msgID': int(message.id), 'flow': int(result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 2}
				finds.append(newFind)
				with open(f'C:/Users/{owner}/shenhe_bot/asset/find.yaml', 'w', encoding = 'utf-8') as file:
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
				embedResult = global_vars.defaultEmbed(f"發布失敗, 請輸入大於1的flow幣"," ")
				global_vars.setFooter(embedResult)
				message = await ctx.send(embed=embedResult)
				return
			for user in users:
				if ctx.author.id == user['discordID']:
					if int(result.flow) > user['flow']:
						embedResult = global_vars.defaultEmbed(f"發布失敗, 請勿輸入大於自己擁有數量的flow幣"," ")
						global_vars.setFooter(embedResult)
						message = await ctx.send(embed=embedResult)
						return
			else:
				embedResult = global_vars.defaultEmbed(f"委託: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n按 ✅ 來接受請求")
				global_vars.setFooter(embedResult)
				message = await ctx.send(embed=embedResult)
				await message.add_reaction('✅')
				newFind = {'title': str(result.title), 'msgID': int(message.id), 'flow': int(result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 3}
				finds.append(newFind)
				with open(f'C:/Users/{owner}/shenhe_bot/asset/find.yaml', 'w', encoding = 'utf-8') as file:
					yaml.dump(finds, file)
		elif choice == 4:
			await ctx.send("尚未完成...")
			return
			def is_me(m):
				return m.author == self.bot.user
			await ctx.channel.purge(limit=1, check=is_me)
			formFalse = Form(ctx, '設定流程', cleanup=True)
			formFalse.add_question('想要幫助什麼?', 'title')
			formFalse.add_question('你覺得這個幫助值多少flow幣?', 'flow')
			formFalse.edit_and_delete(True)
			formFalse.set_timeout(60)
			await formFalse.set_color("0xa68bd3")
			result = await formFalse.start()
			embedResult = global_vars.defaultEmbed(f"可以幫忙: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n按 ✅ 來接受幫助")
			global_vars.setFooter(embedResult)
			message = await ctx.send(embed=embedResult)
			await message.add_reaction('✅')
			newFind = {'title': str(result.title), 'msgID': int(message.id), 'flow': int(result.flow), 'author': str(ctx.author), 'authorID': ctx.author.id, 'type': 4}
			finds.append(newFind)
			with open(f'C:/Users/{owner}/shenhe_bot/asset/find.yaml', 'w', encoding = 'utf-8') as file:
				yaml.dump(finds, file)


	@commands.command()
	async def give(self, ctx, member: discord.Member, argFlow: int):
		if member.id == ctx.author.id:
			await ctx.send(f"<:PaimonSeria:958341967698337854> 還想學土司跟ceye洗錢啊!(不可以自己給自己")
			return
		if argFlow < 0:
			await ctx.send(f"<:PaimonSeria:958341967698337854> 還想學土司跟ceye洗錢啊!(不可以給負數flow幣")
			return
		found = False
		for user in users:
			if user['discordID']==member.id:
				found = True
		if found == False:
			if not member.bot:
				discordID = member.id
				user = self.bot.get_user(discordID)
				register(user, discordID)
			else:
				return
		for user in users:
			if user['discordID'] == ctx.author.id:
				if user['flow'] < int(argFlow):
					embed = global_vars.defaultEmbed("❌交易失敗", "自己都不夠了還想給人ww")
					global_vars.setFooter(embed)
					await ctx.send(embed=embed)
					return
				else:
					user['flow'] -= int(argFlow)
					with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
						yaml.dump(users, file)
			if user['discordID'] == member.id:
				user['flow'] += int(argFlow)
				acceptor = self.bot.get_user(member.id)
				embed = global_vars.defaultEmbed("✅ 交易成功", f"{ctx.author.mention}給了{acceptor.mention} {str(argFlow)}枚flow幣")
				with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
					yaml.dump(users, file)
				global_vars.setFooter(embed)
				await ctx.send(embed=embed)

	@commands.command()
	@commands.has_role("小雪團隊")
	async def take(self, ctx):
		formFalse = Form(ctx, '沒收flow幣', cleanup=True)
		formFalse.add_question('要沒收哪些人的flow幣?(用逗號分隔: @ceye, @ttos)', 'members')
		formFalse.add_question('多少flow幣?', 'flow')
		formFalse.edit_and_delete(True)
		formFalse.set_timeout(60)
		await formFalse.set_color("0xa68bd3")
		result = await formFalse.start()
		memberList = result.members.split(", ")
		for member in memberList:
			id = int(re.search(r'\d+', member).group())
			for user in users:
				if user['discordID'] == id:
					user['flow'] -= int(result.flow) 
					bank['flow'] += int(result.flow)
					acceptor = self.bot.get_user(id)
					embed = global_vars.defaultEmbed("✅ 已成功施展反摩拉克斯的力量", f"{ctx.author.mention} 從 {acceptor.mention} 的帳戶裡拿走了 {result.flow} 枚flow幣")
					global_vars.setFooter(embed)
					await ctx.send(embed=embed)
					with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
						yaml.dump(users, file)
					with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding = 'utf-8') as file:
						yaml.dump(bank, file)
					break

	@commands.command()
	@commands.has_role("小雪團隊")
	async def make(self, ctx):
		formFalse = Form(ctx, '發放flow幣', cleanup=True)
		formFalse.add_question('要給哪些人?(用逗號分隔: @小雪, @sueno)', 'members')
		formFalse.add_question('多少flow幣?', 'flow')
		formFalse.edit_and_delete(True)
		formFalse.set_timeout(60)
		await formFalse.set_color("0xa68bd3")
		result = await formFalse.start()
		memberList = result.members.split(", ")
		for member in memberList:
			id = int(re.search(r'\d+', member).group())
			for user in users:
				if user['discordID'] == id:
					user['flow'] += int(result.flow) 
					bank['flow'] -= int(result.flow)
					acceptor = self.bot.get_user(id)
					embed = global_vars.defaultEmbed("✅ 已成功施展摩拉克斯的力量", f"{ctx.author.mention}從銀行轉出了 {result.flow}枚flow幣給 {acceptor.mention}")
					global_vars.setFooter(embed)
					await ctx.send(embed=embed)
					with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
						yaml.dump(users, file)
					with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding = 'utf-8') as file:
						yaml.dump(bank, file)
					break

	@commands.command()
	async def flow(slef, ctx):
		embed = global_vars.defaultEmbed("flow系統","`!acc`查看flow帳戶\n`!give @user <number>`給flow幣\n`!find`發布委託\n`!shop`商店\n`!shop buy`購買商品")
		global_vars.setFooter(embed)
		await ctx.send(embed=embed)

	@commands.command()
	@commands.has_role("小雪團隊")
	async def reset(self, ctx):
		bank['flow'] = 12000
		for user in users:
			user['flow'] = 100
			bank['flow'] -= 100
		embed = global_vars.defaultEmbed("🔄 已重設世界的一切", f"所有人都回到100flow幣")
		global_vars.setFooter(embed)
		with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
			yaml.dump(users, file)
		with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding = 'utf-8') as file:
			yaml.dump(bank, file)
		await ctx.send(embed=embed)

	@commands.group()
	async def shop(self, ctx):
		if ctx.invoked_subcommand is None:
			itemStr = ""
			count = 1
			for item in shop:
				itemStr = itemStr + f"{count}. {item['name']} - {item['flow']} flow ({item['current']}/{item['max']})\n||{item['uuid']}||\n"
				count += 1
			embed = global_vars.defaultEmbed("🛒 flow商店", itemStr)
			global_vars.setFooter(embed)
			await ctx.send(embed=embed)

	@shop.command()
	@commands.has_role("小雪團隊")
	async def newitem(self, ctx):
		form = Form(ctx, '新增商品', cleanup=True)
		form.add_question('商品名稱?', 'name')
		form.add_question('flow幣價格?', 'flow')
		form.add_question('最大購買次數?', 'max')
		form.edit_and_delete(True)
		form.set_timeout(60)
		await form.set_color("0xa68bd3")
		result = await form.start()
		id = uuid.uuid1()
		newItem = {'name': result.name, 'flow': int(result.flow), 'current': 0, 'max': int(result.max), 'uuid': str(id)}
		shop.append(newItem)
		with open(f'C:/Users/{owner}/shenhe_bot/asset/shop.yaml', 'w', encoding = 'utf-8') as file:
			yaml.dump(shop, file)
		await ctx.send(f"商品{result.name}新增成功")

	@shop.command()
	@commands.has_role("小雪團隊")
	async def removeitem(self, ctx, *, arg=''):
		for item in shop:
			if item['uuid'] == arg:
				shop.remove(item)
				with open(f'C:/Users/{owner}/shenhe_bot/asset/shop.yaml', 'w', encoding = 'utf-8') as file:
					yaml.dump(shop, file)
				await ctx.send("商品刪除成功")
				break

	@shop.command()
	async def buy(self, ctx):
		itemStr = ""
		count = 1
		for item in shop:
				itemStr = itemStr + f"{count}. {item['name']} - {item['flow']} flow ({item['current']}/{item['max']})\n"
				count += 1
		form = Form(ctx, '要購買什麼商品?(輸入數字)', cleanup=True)
		form.add_question(f'{itemStr}', 'number')
		form.edit_and_delete(True)
		form.set_timeout(60)
		await form.set_color("0xa68bd3")
		result = await form.start()
		pos = int(result.number) - 1
		for user in users:
			if user['discordID'] == ctx.author.id:
				found = True
				itemPrice = int(shop[pos]['flow'])
				if user['flow'] < itemPrice:
					await ctx.send(f"{ctx.author.mention} 你的flow幣不足夠購買這項商品")
					return
				if shop[pos]['current'] >= shop[pos]['max']:
					await ctx.send(f"{ctx.author.mention} 這個商品已經售罄了")
					return
				else:
					shop[pos]['current'] += 1
					with open(f'C:/Users/{owner}/shenhe_bot/asset/shop.yaml', 'w', encoding = 'utf-8') as file:
						yaml.dump(shop, file)
					newLog = {'item': shop[pos]['name'], 'flow': int(shop[pos]['flow']), 'buyerID': ctx.author.id, 'itemUUID': shop[pos]['uuid']}
					logs.append(newLog)
					with open(f'C:/Users/{owner}/shenhe_bot/asset/log.yaml', 'w', encoding = 'utf-8') as file:
						yaml.dump(logs, file)
					itemPrice = int(shop[pos]['flow'])
					user['flow'] -= itemPrice
					bank['flow'] += itemPrice
					with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding = 'utf-8') as file:
						yaml.dump(bank, file)
					with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
						yaml.dump(users, file)
					await ctx.send(f"商品 {shop[pos]['name']} 購買成功, 詳情請查看私訊")
					await ctx.author.send(f"您已在flow商城購買了 {shop[pos]['name']} 商品, 請將下方的收據截圖並寄給小雪或律律來兌換商品")
					embed = global_vars.defaultEmbed("📜 購買證明",f"購買人: {ctx.author.mention}\n購買人ID: {ctx.author.id}\n商品: {shop[pos]['name']}\nUUID: {shop[pos]['uuid']}\n價格: {shop[pos]['flow']}")
					global_vars.setFooter(embed)
					await ctx.author.send(embed=embed)
					break
		if found == False:
			if not ctx.author.bot:
				discordID = ctx.author.id
				user = self.bot.get_user(discordID)
				register(user, discordID)
				await ctx.send("你本來沒有帳號, 現在申鶴幫你做了一個, 再打一次`!shop buy`試試看")
			else:
				return

	@shop.command()
	@commands.has_role("小雪團隊")
	async def log(self, ctx):
		for log in logs:
			user = self.bot.get_user(int(log['buyerID']))
			embed = global_vars.defaultEmbed("購買紀錄",f"商品: {log['item']}\n價格: {log['flow']}\n購買人: {user.mention}\n購買人ID: {log['buyerID']}\n商品UUID: {log['itemUUID']}")
			global_vars.setFooter(embed)
			await ctx.send(embed=embed)

	@shop.command()
	@commands.has_role("小雪團隊")
	async def clear(self, ctx, uuid):
		if uuid == "all":
			for item in shop:
				item['current'] = 0
				with open(f'C:/Users/{owner}/shenhe_bot/asset/shop.yaml', 'w', encoding = 'utf-8') as file:
					yaml.dump(shop, file)
			await ctx.send(f"已將所有商品的購買次數清零")
			return
		for item in shop:
			if item['uuid'] == uuid:
				item['current'] = 0
				with open(f'C:/Users/{owner}/shenhe_bot/asset/shop.yaml', 'w', encoding = 'utf-8') as file:
					yaml.dump(shop, file)
				await ctx.send(f"已將 {item['name']} 的購買次數設為0")
				break

	@commands.command()
	async def total(self, ctx):
		total = 0
		count = 0
		for user in users:
			count += 1
			total += user['flow']
		flowSum = total+bank['flow']
		await ctx.send(f"目前群組裡共有:\n{count}個flow帳號\n用戶{total}+銀行{bank['flow']}={flowSum}枚flow幣")

def setup(bot):
	bot.add_cog(FlowCog(bot))