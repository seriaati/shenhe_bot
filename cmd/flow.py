import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import os, discord, asyncio, genshin, yaml, datetime
import global_vars
global_vars.Global()
from discord.ext import commands
from discord.ext.forms import Form
from discord.ext.forms import ReactionForm

with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', encoding = 'utf-8') as file:
	users = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/find.yaml', encoding = 'utf-8') as file:
	finds = yaml.full_load(file)

class FlowCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		channel = self.bot.get_channel(payload.channel_id)
		for find in finds:
			if payload.user_id != self.bot.user.id:
				if payload.message_id == find['msgID']:
					if payload.emoji.name == '✅':
						for user in users:
							if payload.user_id == find['authorID']:
								userObj = self.bot.get_user(find['authorID'])
								await channel.send(f"{userObj.mention}不可以自己接自己的委託啦")
								await reaction.remove(payload.member)
								return
							if user['discordID'] == payload.user_id:
								author = self.bot.get_user(find['authorID'])
								acceptUser = self.bot.get_user(user['discordID'])
								if find['one']==True:
									await channel.send(f"[接受委託] {acceptUser.mention} 接受 {author.mention} 的 {find['title']} 委託, 獲得了 **{find['flow']} flow幣**")
								elif find['one']==False:
									await channel.send(f"[接受素材委託] {acceptUser.mention} 接受 {author.mention} 的 {find['title']} 素材委託, 獲得了 **{find['flow']} flow幣**")
								user['flow'] += find['flow']
								await payload.message.clear_reaction()
							if user['discordID'] == find['authorID']:
								user['flow'] -= find['flow']
						finds.remove(find)
						with open(f'C:/Users/{owner}/shenhe_bot/asset/find.yaml', 'w', encoding = 'utf-8') as file:
							yaml.dump(finds, file)
						with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
							yaml.dump(users, file)

	@commands.command()
	async def acc(self, ctx, *, name: discord.Member = None):
		name = name or ctx.author
		found = False
		for user in users:
			if user['discordID']==name.id:
				found = True
				await ctx.send(f"使用者: {user['name']}\nflow幣: {user['flow']}")
		if found == False:
			discordID = name.id
			newUser = {'name': str(name), 'discordID': int(discordID), 'flow': 100}
			users.append(newUser)
			with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
				yaml.dump(users, file)
			await ctx.send("你本來沒有帳號, 現在申鶴幫你做了一個, 再打`!flow`一次試試看")

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
				if w8 in ctx.author.roles:
					await ctx.send(w8.mention)
				elif w7 in ctx.author.roles:
					await ctx.send(f"{w8.mention} {w7.mention}")
				elif w6 in ctx.author.roles:
					await ctx.send(f"{w8.mention} {w7.mention} {w6.mention}")
				elif w5 in ctx.author.roles:
					await ctx.send(f"{w8.mention} {w7.mention} {w6.mention} {w5.mention}")
				elif w4 in ctx.author.roles:
					await ctx.send(f"{w8.mention} {w7.mention} {w6.mention} {w5.mention} {w4.mention}")
				elif w3 in ctx.author.roles:
					await ctx.send(f"{w8.mention} {w7.mention} {w6.mention} {w5.mention} {w4.mention} {w3.mention}")
				elif w2 in ctx.author.roles:
					await ctx.send(f"{w8.mention} {w7.mention} {w6.mention} {w5.mention} {w4.mention} {w3.mention} {w2.mention}")
				elif w1 in ctx.author.roles:
					await ctx.send(f"{w8.mention} {w7.mention} {w6.mention} {w5.mention} {w4.mention} {w3.mention} {w2.mention} {w1.mention}")	
		elif choice == False:
			def is_me(m):
				return m.author == self.bot.user
			await ctx.channel.purge(limit=1, check=is_me)
			formFalse = Form(ctx, '設定流程', cleanup=True)
			formFalse.add_question('需要什麼素材?(例如: 緋櫻繡球)', 'title')
			formFalse.add_question('你要付多少flow幣給讓你拿素材的人?', 'flow')
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
				if w1 in ctx.author.roles:
					await ctx.send(w1.mention)
				elif w2 in ctx.author.roles:
					await ctx.send(f"{w1.mention} {w2.mention}")
				elif w3 in ctx.author.roles:
					await ctx.send(f"{w1.mention} {w2.mention} {w3.mention}")
				elif w4 in ctx.author.roles:
					await ctx.send(f"{w1.mention} {w2.mention} {w3.mention} {w4.mention}")
				elif w5 in ctx.author.roles:
					await ctx.send(f"{w1.mention} {w2.mention} {w3.mention} {w4.mention} {w5.mention}")
				elif w6 in ctx.author.roles:
					await ctx.send(f"{w1.mention} {w2.mention} {w3.mention} {w4.mention} {w5.mention} {w6.mention}")
				elif w7 in ctx.author.roles:
					await ctx.send(f"{w1.mention} {w2.mention} {w3.mention} {w4.mention} {w5.mention} {w6.mention} {w7.mention}")
				elif w8 in ctx.author.roles:
					await ctx.send(f"{w1.mention} {w2.mention} {w3.mention} {w4.mention} {w5.mention} {w6.mention} {w7.mention} {w8.mention}")	

	@commands.command()
	async def give(self, ctx, member: discord.Member, argFlow: int):
		if member.id == ctx.author.id:
			await ctx.send(f"<:PaimonSeria:958341967698337854> 還想學土司跟ceye洗錢啊!")
			return
		if argFlow < 0:
			await ctx.send(f"<:PaimonSeria:958341967698337854> 還想學土司跟ceye洗錢啊!")
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
				user['flow'] -= int(argFlow)
				acceptor = self.bot.get_user(member.id)
				embed = global_vars.defaultEmbed("✅ 已成功施展摩拉克斯的力量", f"{ctx.author.mention}憑空生出了 {str(argFlow)}枚flow幣給 {acceptor.mention}")
				with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
					yaml.dump(users, file)
				break
		global_vars.setFooter(embed)
		await ctx.send(embed=embed)

	@commands.command()
	async def flow(slef, ctx):
		embed = global_vars.defaultEmbed("flow系統","`!acc`帳戶\n`!give @user <number>`給flow幣\n`!find`發布委託")
		global_vars.setFooter(embed)
		await ctx.send(embed=embed)
def setup(bot):
	bot.add_cog(FlowCog(bot))