import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import os, discord, asyncio, genshin, yaml, datetime, time
import global_vars
global_vars.Global()
from discord.ext import commands
from discord.ext.forms import Form
from discord.ext.forms import ReactionForm

with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', encoding = 'utf-8') as file:
	users = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/find.yaml', encoding = 'utf-8') as file:
	finds = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/confirm.yaml', encoding = 'utf-8') as file:
	confirms = yaml.full_load(file)

class FlowCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_message(self, message):
		if "早安" in message.content:
			for user in users:
				if user['discordID'] == message.author.id:
					if user.has_key('morning')==False:
						user['morning'] = datetime.today().date()
						await message.add_reaction('☀️')
						user['flow'] += 1
					if user['morning'] != datetime.today().date():
						await message.add_reaction('☀️')
						user['flow'] += 1
					with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
						yaml.dump(users, file)
					break
		await self.bot.process_commands(message)

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		time.sleep(0.5)
		channel = self.bot.get_channel(payload.channel_id)
		message = await channel.fetch_message(payload.message_id)
		reaction = discord.utils.get(message.reactions, emoji='✅')
		found = False
		for user in users:
			if user['discordID']==payload.user_id:
				found = True
				break
		if found == False:
			discordID = payload.user_id
			user = self.bot.get_user(payload.user_id)
			newUser = {'name': str(user), 'discordID': int(discordID), 'flow': 100}
			users.append(newUser)
			with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
				yaml.dump(users, file)
		for find in finds:
			if payload.message_id == find['msgID'] and payload.emoji.name == '✅' and payload.user_id != self.bot.user.id:
				for user in users:
					if payload.user_id == find['authorID']:
						userObj = self.bot.get_user(find['authorID'])
						await channel.send(f"{userObj.mention}不可以自己接自己的委託啦")
						await reaction.remove(payload.member)
						return
					elif user['discordID'] == payload.user_id:
						await message.clear_reaction('✅')
						author = self.bot.get_user(find['authorID'])
						acceptUser = self.bot.get_user(user['discordID'])
						if find['one']==True:
							await author.send(f"[成功接受委託] {acceptUser.mention} 接受了你的 {find['title']} 委託")
							await acceptUser.send(f"[成功接受委託] 你接受了 {author.mention} 的 {find['title']} 委託")
						elif find['one']==False:
							await author.send(f"[成功接受素材委託] {acceptUser.mention} 接受了你的 {find['title']} 素材委託")
							await author.send(f"[成功接受素材委託] 你接受了 {author.mention} 的 {find['title']} 素材委託")
						# user['flow'] += find['flow']
						embedDM = global_vars.defaultEmbed("結算單","當對方完成委託的內容時, 請按 🆗來結算flow幣")
						global_vars.setFooter(embedDM)
						dm = await author.send(embed=embedDM)
						await dm.add_reaction('🆗')
						newConfirm = {'title': find['title'], 'authorID': int(find['authorID']), 
							'receiverID': int(user['discordID']), 'flow': find['flow'], 'msgID': dm.id}
						confirms.append(newConfirm)
						finds.remove(find)
						with open(f'C:/Users/{owner}/shenhe_bot/asset/confirm.yaml', 'w', encoding = 'utf-8') as file:
							yaml.dump(confirms, file)
						with open(f'C:/Users/{owner}/shenhe_bot/asset/find.yaml', 'w', encoding = 'utf-8') as file:
							yaml.dump(finds, file)
						return
		for confirm in confirms:
			if payload.message_id == confirm['msgID'] and payload.emoji.name == '🆗' and payload.user_id != self.bot.user.id:
				for user in users:
					if user['discordID'] == confirm['authorID']:
						user['flow'] -= confirm['flow']
					elif user['discordID'] == confirm['receiverID']:
						user['flow'] += confirm['flow']
				author = self.bot.get_user(confirm['authorID'])
				receiver = self.bot.get_user(confirm['receiverID'])
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

	@commands.command()
	async def acc(self, ctx, *, name: discord.Member = None):
		name = name or ctx.author
		found = False
		for user in users:
			if user['discordID']==name.id:
				found = True
				embed = global_vars.defaultEmbed(f"使用者: {user['name']}",f"flow幣: {user['flow']}")
				global_vars.setFooter(embed)
				await ctx.send(embed=embed)
		if found == False:
			discordID = name.id
			newUser = {'name': str(name), 'discordID': int(discordID), 'flow': 100}
			users.append(newUser)
			with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
				yaml.dump(users, file)
			await ctx.send("你本來沒有帳號, 現在申鶴幫你做了一個, 再打`!acc`一次試試看")

	@commands.command()
	@commands.is_owner()
	async def roles(self, ctx):
		channel = self.bot.get_channel(962311051683192842)
		embed = global_vars.defaultEmbed("請選擇你的世界等級", " ")
		global_vars.setFooter(embed)
		message = await channel.send(embed=embed)
		await message.add_reaction('1️⃣')
		await message.add_reaction('2️⃣')
		await message.add_reaction('3️⃣')
		await message.add_reaction('4️⃣')
		await message.add_reaction('5️⃣')
		await message.add_reaction('6️⃣')
		await message.add_reaction('7️⃣')
		await message.add_reaction('8️⃣')

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
			discordID = ctx.author.id
			newUser = {'name': str(ctx.author), 'discordID': int(discordID), 'flow': 100}
			users.append(newUser)
			with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
				yaml.dump(users, file)

		w1 = discord.utils.get(ctx.guild.roles,name="W1")
		w2 = discord.utils.get(ctx.guild.roles,name="W2")
		w3 = discord.utils.get(ctx.guild.roles,name="W3")
		w4 = discord.utils.get(ctx.guild.roles,name="W4")
		w5 = discord.utils.get(ctx.guild.roles,name="W5")
		w6 = discord.utils.get(ctx.guild.roles,name="W6")
		w7 = discord.utils.get(ctx.guild.roles,name="W7")
		w8 = discord.utils.get(ctx.guild.roles,name="W8")
		roles = [w1, w2, w3, w4, w5, w6, w7, w8]

		embed = global_vars.defaultEmbed("請選擇委託類別",
			"1️⃣: 其他玩家進入你的世界(例如: 陪玩, 打素材等)\n2️⃣: 你進入其他玩家的世界(例如: 拿特產)")
		message = await ctx.send(embed=embed)
		form = ReactionForm(message,self.bot,ctx.author)
		form.add_reaction("1️⃣", True)
		form.add_reaction("2️⃣", False)
		choice = await form.start()
		if choice == True: 
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
				embedResult = global_vars.defaultEmbed(f"請求幫助: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n按 ✅ 來接受委託")
				global_vars.setFooter(embedResult)
				message = await ctx.send(embed=embedResult)
				title = result.title
				msgID = message.id
				flow = result.flow
				author = ctx.author
				await message.add_reaction('✅')
				newFind = {'title': str(title), 'msgID': int(msgID), 'flow': int(flow), 'author': str(author), 'authorID': ctx.author.id, 'one': True}
				finds.append(newFind)
				with open(f'C:/Users/{owner}/shenhe_bot/asset/find.yaml', 'w', encoding = 'utf-8') as file:
					yaml.dump(finds, file)
		elif choice == False:
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
				embedResult = global_vars.defaultEmbed(f"素材請求: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}\n按 ✅ 來接受請求")
				global_vars.setFooter(embedResult)
				message = await ctx.send(embed=embedResult)
				title = result.title
				msgID = message.id
				flow = result.flow
				maxPerson = 1
				author = ctx.author
				await message.add_reaction('✅')
				newFind = {'title': str(title), 'msgID': int(msgID), 'flow': int(flow), 'maxPerson': int(maxPerson), 'author': str(author), 'authorID': ctx.author.id, 'one': False}
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
			discordID = member.id
			newUser = {'name': str(member), 'discordID': int(discordID), 'flow': 100}
			users.append(newUser)
			with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
				yaml.dump(users, file)
		for user in users:
			if user['discordID'] == ctx.author.id:
				if user['flow'] < int(argFlow):
					embed = global_vars.defaultEmbed("❌交易失敗", "自己都不夠了還想給人ww")
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
	@commands.is_owner()
	async def take(self, ctx, member: discord.Member, argFlow: int):
		for user in users:
			if user['discordID'] == member.id:
				user['flow'] -= int(argFlow)
				acceptor = self.bot.get_user(member.id)
				embed = global_vars.defaultEmbed("✅ 沒收成功", f"{ctx.author.mention}沒收了{acceptor.mention} {str(argFlow)}枚flow幣")
				with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
					yaml.dump(users, file)
				break
		global_vars.setFooter(embed)
		await ctx.send(embed=embed)

	@commands.command()
	@commands.is_owner()
	async def make(self, ctx, member: discord.Member, argFlow: int):
		for user in users:
			if user['discordID'] == member.id:
				user['flow'] += int(argFlow)
				acceptor = self.bot.get_user(member.id)
				embed = global_vars.defaultEmbed("✅ 已成功施展摩拉克斯的力量", f"{ctx.author.mention}憑空生出了 {str(argFlow)}枚flow幣給 {acceptor.mention}")
				with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
					yaml.dump(users, file)
				break
		global_vars.setFooter(embed)
		await ctx.send(embed=embed)

	@commands.command()
	async def flow(slef, ctx):
		embed = global_vars.defaultEmbed("flow系統","`!acc`查看flow帳戶\n`!give @user <number>`給flow幣\n`!find`發布委託\n`!shop`商店")
		global_vars.setFooter(embed)
		await ctx.send(embed=embed)

	@commands.command()
	@commands.is_owner()
	async def reset(self, ctx):
		for user in users:
			user['flow'] = 100
		embed = global_vars.defaultEmbed("🔄 已重設世界的一切", f"所有人都回到100flow幣")
		global_vars.setFooter(embed)
		with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
			yaml.dump(users, file)
		await ctx.send(embed=embed)

	@commands.command()
	async def shop(self, ctx):
		embed = global_vars.defaultEmbed("🛒 flow商店","這裡還空空如也…\n過一段時間再回來看看吧")
		global_vars.setFooter(embed)
		await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(FlowCog(bot))