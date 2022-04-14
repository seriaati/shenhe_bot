import gspread, discord, re
from discord.ext import commands
from discord.ext.forms import Form

sa = gspread.service_account()
sh = sa.open("Genshin")
wks = sh.worksheet("4/14")
teamCol = ["d", "h", "l"]
teamRow = ["3", "9", "15", "21"]
captainRow = ["4", "10", "16", "22"]
teamCells = []
for col in teamCol:
	for row in teamRow:
		teamCells.append(col+row)
captainCells = []
for col in teamCol:
	for row in captainRow:
		captainCells.append(col+row)

class AttendCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def get(self, ctx, arg):
		await ctx.send(wks.acell(arg).value)

	@commands.command()
	async def att(self, ctx):
		titleStr = ""
		for title in titleCells:
			titleStr += f"- {wks.acell(title).value}\n"
		form = Form(ctx, '要對哪個隊伍做點名?', cleanup=True)
		form.add_question(titleStr, 'title')
		form.edit_and_delete(True)
		form.set_timeout(60)
		await form.set_color("0xa68bd3")
		result = await form.start()
		for team in teamCells:
			if result.title == wks.acell(team).value:
				cellWord = " ".join(re.findall("[a-zA-Z]+", str(team)))
				cellNum = re.findall(r'\b\d+\b', str(team))
				cell = cellWord+str(cellNum)
				if ctx.author.id == wks.acell(cell):
					await ctx.send("true")


def setup(bot):
	bot.add_cog(AttendCog(bot))