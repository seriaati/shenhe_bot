import gspread
import discord
from discord.ext import commands

sa = gspread.service_account()
sh = sa.open("Genshin")
wks = sh.worksheet("4/14")

class AttendCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def get(self, ctx, arg):
		await ctx.send(wks.acell(arg).value)

def setup(bot):
	bot.add_cog(AttendCog(bot))