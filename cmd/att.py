import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import gspread, discord, yaml
import global_vars
global_vars.Global()
from discord.ext import commands
from discord.ext.forms import Form
from discord.ext.forms import ReactionForm
with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', encoding = 'utf-8') as file:
	users = yaml.full_load(file)
with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', encoding = 'utf-8') as file:
	bank = yaml.full_load(file)

sa = gspread.service_account()
sh = sa.open("Genshin")
wks = sh.worksheet("4/14")
teamCol = [2, 6, 10]
teamRow = [3, 9, 15, 21]
captainCol = [4, 8, 12]
captainRow = [4, 10, 16, 22]
memberCol = [3, 7, 11]
memberRow = [5, 6, 7, 11, 12, 13, 17, 18, 19, 23, 24, 25]
teams = []
for col in teamCol:
	for row in teamRow:
		val = wks.cell(row, col).value
		if val == None:
			continue
		teams.append(val)
captains = []
for col in captainCol:
	for row in captainRow:
		val = wks.cell(row, col).value
		if val == None:
			continue
		captains.append(val)
members = []
for col in memberCol:
    for row in memberRow:
        val = wks.cell(row, col).value
        if val == None:
            val = "(暫無團員)"
        members.append(val)
x = 3
memberList = [members[i:i+x] for i in range(0, len(members), x)]

class AttendCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def get(self, ctx, arg):
		await ctx.send(wks.acell(arg).value)

	@commands.command()
	async def att(self, ctx):
		teamStr = ""
		for team in teams:
			teamStr += f"• {team}\n"
		form = Form(ctx, '要對哪個隊伍做點名?', cleanup = True)
		form.add_question(teamStr, 'title')
		form.add_question("每個有到的隊員要給多少flow幣?", 'flow')
		form.edit_and_delete(True)
		form.set_timeout(60)
		await form.set_color("0xa68bd3")
		result = await form.start()
		team = result.title
		pos = -1
		for team in teams:
			if team == result.title:
				pos = teams.index(team)
				break
		if pos == -1:
			await ctx.send("找不到該小組, 請查看名稱是否輸入錯誤")
		else:
			if int(captains[pos]) == ctx.author.id:
				list = memberList[pos]
				for member in list:
					if member == "(暫無團員)":
						continue
					embed = global_vars.defaultEmbed("這個人有來嗎?",member)
					message = await ctx.send(embed=embed)
					form = ReactionForm(message,self.bot,ctx.author)
					form.add_reaction("✅", True)
					form.add_reaction("❌", False)
					choice = await form.start()
					if choice == True:
						for user in users:
							if user['name'] in member:
								user['flow'] += int(result.flow)
								bank['flow'] -= int(result.flow)
								with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
									yaml.dump(users, file)
								with open(f'C:/Users/{owner}/shenhe_bot/asset/bank.yaml', 'w', encoding = 'utf-8') as file:
									yaml.dump(bank, file)
								await ctx.send(f"{member} 獲得了 {result.flow} flow幣")
								break
					elif choice == False:
						await ctx.send(f"{member} 沒到")
			else:
				await ctx.send(f"{ctx.author.mention} 你不是這個團的隊長")

def setup(bot):
	bot.add_cog(AttendCog(bot))