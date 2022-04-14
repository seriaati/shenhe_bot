import gspread
import discord
from discord.ext import commands

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
	async def teams(self, ctx):
		titleStr = ""
		for title in titleCells:
			titleStr += f"= {wks.acell(title)}\n"
		await ctx.send(titleStr)

def setup(bot):
	bot.add_cog(AttendCog(bot))