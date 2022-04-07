import discord
from classes import User
def Global():
    global warningColor, purpleColor, footerAuthor, footerImage, timeOutErrorMsg, embedNoAccount, embedNoGroup, groups
    warningColor = 0xfc5165
    purpleColor = 0xa68bd3
    footerAuthor = "所有指令打!help, 有錯誤請告知小雪"
    footerImage = "https://i.imgur.com/DWYpYrd.jpg"
    timeOutErrorMsg = "已取消當前操作, 請在30秒內回答問題"
    embedNoAccount = discord.Embed(title = "😢 該帳號不存在", description="請使用`!register`來註冊帳號, 如有疑問請@小雪", color=warningColor)
    embedNoGroup = discord.Embed(title = "😢 該小組不存在", description="有可能是打錯字了", color = warningColor)

def setFooter(embed):
    Global()
    embed.set_footer(text=footerAuthor,icon_url=footerImage)

def defaultEmbed(title, message):
    Global()
    return discord.Embed(title = title, description = message, color = purpleColor)