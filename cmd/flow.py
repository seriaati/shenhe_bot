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

class FlowCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def flow(self, ctx, *, name: discord.Member = None):
		name = name or ctx.author.id
		found = False
		for user in users:
			if user['discordID']==name:
				found = True
				await ctx.send(f"使用者: {user['name']}\nflow幣: {user['flow']}")
		if found == False:
			discordID = name
			name = ctx.author
			newUser = {'name': str(name), 'discordID': int(discordID), 'flow': 0}
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
		w1 = discord.utils.get(ctx.guild.roles,name="W1")
		w2 = discord.utils.get(ctx.guild.roles,name="W2")
		w3 = discord.utils.get(ctx.guild.roles,name="W3")
		w4 = discord.utils.get(ctx.guild.roles,name="W4")
		w5 = discord.utils.get(ctx.guild.roles,name="W5")
		w6 = discord.utils.get(ctx.guild.roles,name="W6")
		w7 = discord.utils.get(ctx.guild.roles,name="W7")
		w8 = discord.utils.get(ctx.guild.roles,name="W8")

		embed = global_vars.defaultEmbed("你是需要幫打素材還是需要別人世界的素材?","✅: 幫打素材\n❌: 拿其他世界的素材")
		message = await ctx.send(embed=embed)
		form = ReactionForm(message,self.bot,ctx.author)
		form.add_reaction("✅", True)
		form.add_reaction("❌", False)
		choice = await form.start()
		if choice == True:
			formTrue = Form(ctx, '請求幫助設定流程')
			formTrue.add_question('需要什麼幫助?(例如: 打刀鐔)', 'title')
			formTrue.add_question('這個幫助值多少flow幣?', 'flow')
			formTrue.edit_and_delete(True)
			formTrue.set_timeout(60)
			await formTrue.set_color("0xa68bd3")
			result = await formTrue.start()
			embedResult = global_vars.defaultEmbed(f"請求幫助: {result.title}", f"發布者: {ctx.author.mention}\nflow幣: {result.flow}")
			global_vars.setFooter(embedResult)
			print(ctx.author.roles)
			await ctx.send(embed=embedResult)
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
			await ctx.send("施工中…")

def setup(bot):
	bot.add_cog(FlowCog(bot))