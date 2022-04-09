import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import os, discord, asyncio, genshin, yaml, datetime
import global_vars
global_vars.Global()
from discord.ext import commands
from discord.ext.forms import Form

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
		form = Form(ctx, '請求幫助設定流程')
		form.add_question('需要什麼幫助?', 'title')
		form.add_question('世界等級?', 'level')
		form.add_question('這個幫助值多少flow幣?', 'flow')

		form.edit_and_delete(True)
		form.set_timeout(60)
		await form.set_color("0xa68bd3")
		result = await form.start()
		embed = global_vars.defaultEmbed("結果",f"{result.title}\n{result.level}\n{result.flow}")
		global_vars.setFooter(embed)
		await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(FlowCog(bot))