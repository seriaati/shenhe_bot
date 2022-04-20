import discord
import yaml


global warningColor, purpleColor, footerAuthor, footerImage, timeOutErrorMsg, embedNoAccount, embedNoGroup, groups, whyRegister
warningColor = 0xfc5165
purpleColor = 0xa68bd3
footerAuthor = "所有指令打!help, 想要新功能或有bug請告訴小雪"
footerImage = "https://i.imgur.com/DWYpYrd.jpg"
timeOutErrorMsg = "已取消當前操作, 請在30秒內回答問題"
embedNoAccount = discord.Embed(
    title="😢 該帳號不存在", description="請使用`!register`來註冊帳號, 如有疑問請@小雪", color=warningColor)
embedNoGroup = discord.Embed(
    title="😢 該小組不存在", description="有可能是打錯字了", color=warningColor)
whyRegister = "• `!abyss`炫耀你的深淵傷害(或被嘲笑)\n• `!check`查看目前的派遣、樹脂、塵歌壺等狀況\n• `!char`炫耀你擁有的角色\n• `!stats`證明你是大佬\n• `!diary`看看這個月要不要課\n• `!area`炫耀探索度(或被嘲笑)\n• `!today`今天的肝還在嗎\n• 自動領取hoyolab網頁登入獎勵\n• 樹脂提醒功能(詳情請打`!dm`)"
global bot_token
bot_token = "OTU2MDQ5OTEyNjk5NzE1NjM0.Yjqk3Q.emwxEymWn5zMSDf-MPqIuD-vSpQ"


def setFooter(embed):
    embed.set_footer(text=footerAuthor, icon_url=footerImage)


def defaultEmbed(title, message):
    return discord.Embed(title=title, description=message, color=purpleColor)

def loadFlowYaml():
    with open(f'cmd/asset/flow.yaml', encoding='utf-8') as file:
        users = yaml.full_load(file)
    with open(f'cmd/asset/find.yaml', encoding='utf-8') as file:
        finds = yaml.full_load(file)
    with open(f'cmd/asset/confirm.yaml', encoding='utf-8') as file:
        confirms = yaml.full_load(file)
    with open(f'cmd/asset/bank.yaml', encoding='utf-8') as file:
        bank = yaml.full_load(file)
    with open(f'cmd/asset/shop.yaml', encoding='utf-8') as file:
        shop = yaml.full_load(file)
    with open(f'cmd/asset/log.yaml', encoding='utf-8') as file:
        logs = yaml.full_load(file)
    with open(f'cmd/asset/giveaways.yaml', encoding='utf-8') as file:
        giveaways = yaml.full_load(file)

def loadGenshinYaml():
    with open(f'cmd/asset/accounts.yaml', encoding='utf-8') as file:
        users = yaml.full_load(file)
    return users