import gspread, discord, re
from discord.ext import commands
from discord.ext.forms import Form

sa = gspread.service_account()
sh = sa.open("Genshin")
wks = sh.worksheet("4/14")
teamCol = [2, 6, 10]
teamRow = [3, 9, 15, 21]
captianCol = [4, 8, 12]
captainRow = [4, 10, 16, 22]

class AttendCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def get(self, ctx, arg):
		await ctx.send(wks.acell(arg).value)

	@commands.command()
	async def att(self, ctx):
		titleStr = ""
		for row in teamRow:
			for col in teamCol:
				val = wks.cell(row, col).value
				if val == None:
					continue
				titleStr += f"- {val}\n"
		form = Form(ctx, '要對哪個隊伍做點名?', cleanup=True)
		form.add_question(titleStr, 'title')
		form.edit_and_delete(True)
		form.set_timeout(60)
		await form.set_color("0xa68bd3")
		result = await form.start()




def setup(bot):
	bot.add_cog(AttendCog(bot))