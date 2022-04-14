import gspread
import discord
from discord.ext import commands
from discord.ext.forms import Form

sa = gspread.service_account()
sh = sa.open("Genshin")
wks = sh.worksheet("4/14")
titleCells = ["b3", "f3", "b9", "f9", "b15", "f15", "b21", "f21", "j21"]

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
		

def setup(bot):
	bot.add_cog(AttendCog(bot))